#!/usr/bin/env python3
"""
Build script for MkDocs with validation and post-processing.
Implements architecture decisions from dev/ARCHITECTURE.md

Usage:
    python build.py [--clean] [--serve]
"""

import os
import sys
import argparse
import subprocess
import re
import shutil
from pathlib import Path
from typing import List, Tuple
import yaml


class BuildValidator:
    """Validates project structure against architectural decisions."""
    
    SUPPORTED_LANGUAGES = ['en', 'pt']
    REQUIRED_DIRS = ['docs', '.github/workflows', 'dev']
    REQUIRED_FILES = ['macros.py', 'mkdocs.yml', 'requirements.txt']

    def _docs_root_path(self) -> Path:
        return self.root_dir / 'docs'

    def _validate_docs_root_entries(self):
        """Allow only language directories directly under docs/."""
        docs_dir = self._docs_root_path()
        if not docs_dir.exists():
            return

        allowed = set(self.SUPPORTED_LANGUAGES)
        for entry in docs_dir.iterdir():
            if entry.name.startswith('.'):
                continue
            if entry.name not in allowed:
                self.errors.append(
                    f"Unexpected entry in docs/: {entry.name}. "
                    f"Only language directories are allowed: {', '.join(self.SUPPORTED_LANGUAGES)}"
                )

    def _validate_category_indexes(self):
        """Warn when a category/subcategory directory lacks its README.md index (ADR-4.3)."""
        for lang in self.SUPPORTED_LANGUAGES:
            lang_dir = self._docs_root_path() / lang
            if not lang_dir.exists():
                continue
            for entry in lang_dir.rglob('*'):
                if entry.is_dir() and not (entry / 'README.md').exists():
                    self.warnings.append(
                        f"Category/subcategory missing README.md index: "
                        f"{entry.relative_to(self.root_dir)}"
                    )
    
    def __init__(self, root_dir: str = '.'):
        self.root_dir = Path(root_dir)
        self.errors = []
        self.warnings = []
    
    def validate_structure(self) -> bool:
        """Validate overall project structure."""
        print("🔍 Validating project structure...")
        
        # Check required directories
        for dir_path in self.REQUIRED_DIRS:
            full_path = self.root_dir / dir_path
            if not full_path.exists():
                self.errors.append(f"Missing required directory: {dir_path}")

        # Check required root files
        for file_path in self.REQUIRED_FILES:
            if not (self.root_dir / file_path).exists():
                self.errors.append(f"Missing required file: {file_path}")
        
        # Check docs language structure
        self._validate_docs_root_entries()

        for lang in self.SUPPORTED_LANGUAGES:
            lang_dir = self.root_dir / 'docs' / lang
            if not lang_dir.exists():
                self.errors.append(f"Missing language directory: docs/{lang}")
            else:
                license_file = lang_dir / 'LICENSE.md'
                if not license_file.exists():
                    self.warnings.append(f"Missing LICENSE.md in docs/{lang}")
                
                readme_file = lang_dir / 'README.md'
                if not readme_file.exists():
                    self.warnings.append(f"Missing README.md in docs/{lang}")
        
        # Check category/subcategory index pages (ADR-4.3)
        self._validate_category_indexes()

        return len(self.errors) == 0
    
    def validate_front_matter(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Validate YAML front matter in markdown files."""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for YAML front matter
            if content.startswith('---'):
                match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
                if match:
                    try:
                        yaml.safe_load(match.group(1))
                    except yaml.YAMLError as e:
                        issues.append(f"Invalid YAML in {file_path}: {e}")
            else:
                # Front matter is optional for index files
                if file_path.name not in ['README.md', 'LICENSE.md']:
                    issues.append(f"No front matter in {file_path}")
        
        except Exception as e:
            issues.append(f"Error reading {file_path}: {e}")
        
        return len(issues) == 0, issues
    
    def validate_all_markdown(self) -> bool:
        """Validate all markdown files in docs directory."""
        print("📝 Validating Markdown files...")
        docs_dir = self._docs_root_path()

        # Enforce ADR-4.1: all markdown content must be scoped under docs/<lang>/...
        for md_file in docs_dir.rglob('*.md'):
            rel_parts = md_file.relative_to(docs_dir).parts
            if not rel_parts or rel_parts[0] not in self.SUPPORTED_LANGUAGES:
                self.errors.append(
                    f"Markdown outside language scope: docs/{md_file.relative_to(docs_dir)}"
                )
        
        for md_file in docs_dir.rglob('*.md'):
            valid, issues = self.validate_front_matter(md_file)
            if not valid:
                self.warnings.extend(issues)
        
        return True
    
    def report(self):
        """Print validation report."""
        if self.errors:
            print("\n❌ Validation Errors:")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print("\n⚠️  Validation Warnings:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if not self.errors and not self.warnings:
            print("✅ Validation passed!")
        
        print()


class MkDocsBuild:
    """Handles MkDocs build process."""
    
    def __init__(self, root_dir: str = '.'):
        self.root_dir = Path(root_dir)
    
    def clean(self) -> bool:
        """Clean previous builds."""
        print("🧹 Cleaning previous builds...")
        site_dir = self.root_dir / 'site'
        if site_dir.exists():
            shutil.rmtree(site_dir)
            print("  Removed site directory")
        return True
    
    def build(self) -> bool:
        """Build site with MkDocs."""
        print("🔨 Building site with MkDocs...")
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'mkdocs', 'build'],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ Build failed:\n{result.stderr}")
                return False

            self.prepare_english_entrypoint()
            self.write_root_redirect()
            
            print("✅ Build completed successfully!")
            return True
        
        except FileNotFoundError:
            print("❌ MkDocs not found. Install with: pip install -r requirements.txt")
            return False
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False

    def write_root_redirect(self) -> None:
        """Force root entrypoint to redirect to /en/."""
        index_file = self.root_dir / 'site' / 'index.html'
        redirect_html = """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <title>Redirecting...</title>
    <meta http-equiv=\"refresh\" content=\"0; url=en/\">
    <link rel=\"canonical\" href=\"en/\">
    <script>window.location.replace('en/');</script>
  </head>
  <body>
    <p>Redirecting to <a href=\"en/\">English</a>...</p>
  </body>
</html>
"""
        index_file.write_text(redirect_html, encoding='utf-8')

    def prepare_english_entrypoint(self) -> None:
        """Create /en/ aliases from default-language output before redirecting root."""
        site_dir = self.root_dir / 'site'
        root_index = site_dir / 'index.html'
        en_index = site_dir / 'en' / 'index.html'

        if root_index.exists():
            content = root_index.read_text(encoding='utf-8')
            content = content.replace('<head>', '<head>\n    <base href="../">', 1)
            en_index.parent.mkdir(parents=True, exist_ok=True)
            en_index.write_text(content, encoding='utf-8')

        root_license = site_dir / 'LICENSE' / 'index.html'
        en_license = site_dir / 'en' / 'LICENSE' / 'index.html'
        if root_license.exists():
            content = root_license.read_text(encoding='utf-8')
            content = content.replace('<head>', '<head>\n    <base href="../../">', 1)
            en_license.parent.mkdir(parents=True, exist_ok=True)
            en_license.write_text(content, encoding='utf-8')
    
    def serve(self) -> bool:
        """Serve generated static site locally."""
        print("📡 Starting local static server...")
        print("   Access at http://127.0.0.1:8000")
        try:
            site_dir = self.root_dir / 'site'
            subprocess.run(
                [sys.executable, '-m', 'http.server', '8000'],
                cwd=site_dir
            )
            return True
        except Exception as e:
            print(f"❌ Serve error: {e}")
            return False


def main():
    """Main build orchestration."""
    parser = argparse.ArgumentParser(
        description='Build and validate MkDocs site',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python build.py              # Validate and build
  python build.py --clean      # Clean and build
  python build.py --serve      # Build and serve locally
        '''
    )
    
    parser.add_argument('--clean', action='store_true', help='Clean before building')
    parser.add_argument('--serve', action='store_true', help='Serve locally after building')
    parser.add_argument('--validate-only', action='store_true', help='Only validate, don\'t build')
    
    args = parser.parse_args()
    
    # Step 1: Validate
    validator = BuildValidator()
    if not validator.validate_structure():
        validator.report()
        return 1
    
    validator.validate_all_markdown()
    validator.report()
    
    if args.validate_only:
        return 0
    
    # Step 2: Build
    builder = MkDocsBuild()
    
    if args.clean:
        builder.clean()
    
    if not builder.build():
        return 1
    
    # Step 3: Serve (optional)
    if args.serve:
        builder.serve()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
