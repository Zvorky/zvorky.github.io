"""
Custom Jinja2 macros for MkDocs.

Provides dynamic listing of categories, subcategories, and articles by scanning
the filesystem at build time. Intended for README.md files at every level of the
docs/<lang>/ tree.

ADR references:
  ADR-4.3  Dynamic Indexing     — list_children()
  ADR-4.4  Automated Content Showcases — list_categories()
"""

import re
import yaml
from pathlib import Path
from urllib.parse import quote


def define_env(env):
    # ── helpers ────────────────────────────────────────────────────────────

    def _read_frontmatter(filepath: Path) -> dict:
        try:
            content = filepath.read_text(encoding="utf-8")
            if content.startswith("---"):
                match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
                if match:
                    return yaml.safe_load(match.group(1)) or {}
        except Exception:
            pass
        return {}

    def _get_title(filepath: Path, fallback: str) -> str:
        fm = _read_frontmatter(filepath)
        if "title" in fm:
            return fm["title"]
        try:
            for line in filepath.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped.startswith("# "):
                    return stripped[2:].strip()
        except Exception:
            pass
        return fallback

    def _get_date(filepath: Path):
        return _read_frontmatter(filepath).get("date")

    # ── macros ─────────────────────────────────────────────────────────────

    @env.macro
    def list_children(show_date: bool = True) -> str:
        """
        List subcategories and articles in the current page's directory.

        Intended for README.md files at category and subcategory level (ADR-4.3).
        Subcategories are only shown when they contain their own README.md.
        Articles are all .md files other than README.md and LICENSE.md.
        """
        current_dir = Path(env.page.file.abs_src_path).parent
        use_dir_urls = env.conf.get("use_directory_urls", True)

        sections = []
        articles = []

        for entry in sorted(current_dir.iterdir(), key=lambda p: p.name.lower()):
            if entry.is_dir():
                readme = entry / "README.md"
                if readme.exists():
                    title = _get_title(readme, entry.name)
                    sections.append((entry.name, title))
            elif entry.suffix == ".md" and entry.name not in ("README.md", "LICENSE.md"):
                title = _get_title(entry, entry.stem)
                date = _get_date(entry)
                articles.append((entry.stem, title, date))

        if not sections and not articles:
            return "<p><em>No content yet.</em></p>"

        out = []

        if sections:
            out.append("<h3>Subcategories</h3>")
            out.append("<ul>")
            for slug, title in sections:
                out.append(f'  <li><a href="{quote(slug)}/">{title}</a></li>')
            out.append("</ul>")

        if articles:
            out.append("<h3>Articles</h3>")
            out.append("<ul>")
            for slug, title, date in articles:
                href = f"{quote(slug)}/" if use_dir_urls else f"{quote(slug)}.html"
                date_str = f" <em>({date})</em>" if date and show_date else ""
                out.append(f'  <li><a href="{href}">{title}</a>{date_str}</li>')
            out.append("</ul>")

        return "\n".join(out)

    @env.macro
    def list_categories() -> str:
        """
        List top-level categories for the current language's landing page (ADR-4.3).

        Intended for docs/<lang>/README.md files. Reads each category's README.md
        to extract a proper title.
        """
        current_dir = Path(env.page.file.abs_src_path).parent

        categories = []
        for entry in sorted(current_dir.iterdir(), key=lambda p: p.name.lower()):
            if entry.is_dir():
                readme = entry / "README.md"
                if readme.exists():
                    title = _get_title(readme, entry.name)
                    categories.append((entry.name, title))

        if not categories:
            return "<p><em>No categories yet.</em></p>"

        out = ["<ul>"]
        for slug, title in categories:
            out.append(f'  <li><a href="{quote(slug)}/">{title}</a></li>')
        out.append("</ul>")
        return "\n".join(out)
