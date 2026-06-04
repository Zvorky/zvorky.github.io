# Architecture Decision Record

## **[ADR-1.0]** Deployment Environment
**Created at:** 2026-05-28T21:54:42 | **Modified at:** 2026-05-28T21:54:42  

**Description:** Decisions regarding the hosting platform, serving method, and foundational architecture for the knowledge base.  

- ### **[ADR-1.1]** Use GitHub Pages as the Static Hosting Environment  
  **Modified at:** 2026-05-28T21:54:42  
  **Problem:** The repository needs a free, reliable, and zero-maintenance hosting solution to serve technical articles globally. Initial ideas considered dynamic rendering (SSR).  
  **Decision:** Adopt a Static Site Generation (SSG) architecture and host the rendered HTML files on GitHub Pages. Dynamic SSR is abandoned for this specific use case.  
  **Pro:** Zero hosting costs  
  **Pro:** Native integration with GitHub repositories  
  **Pro:** High availability and performance for static content  
  **Con:** Inability to run server-side logic (e.g., dynamic Jinja rendering on request) directly on the host  


## **[ADR-2.0]** Documentation Engine & Core Plugins
**Created at:** 2026-05-28T21:54:42 | **Modified at:** 2026-05-28T21:54:43  

**Description:** Decisions defining the framework, visual theme, and plugins used to parse Markdown and generate the static site.  

- ### **[ADR-2.1]** Use MkDocs with the Material Theme  
  **Modified at:** 2026-05-28T21:54:42  
  **Problem:** Building and maintaining a custom markdown renderer requires significant effort and diverges focus from content creation.  
  **Decision:** Use MkDocs, a Python-based SSG, paired with the 'Material for MkDocs' theme.  
  **Pro:** Industry standard for technical documentation  
  **Pro:** Out-of-the-box responsive design  
  **Pro:** Native support for tags and admonitions  
  **Con:** Requires learning the MkDocs configuration schema  

- ### **[ADR-2.2]** Implement mkdocs-static-i18n  
  **Modified at:** 2026-05-28T21:54:42  
  **Problem:** The knowledge base must support multiple languages (English and Portuguese) with automatic URL synchronization between equivalent articles.  
  **Decision:** Use the mkdocs-static-i18n plugin to generate static language-specific versions of the site while maintaining a unified Markdown structure in the repository.  
  **Pro:** Native language selector  
  **Pro:** SEO friendly  
  **Pro:** Transparent URL translation  
  **Con:** Adds minor complexity to the build process  

- ### **[ADR-2.3]** Implement mkdocs-macros-plugin  
  **Modified at:** 2026-05-28T21:54:43  
  **Problem:** README.md files acting as directory index pages need to dynamically list all articles within their respective folders to avoid manual index updates.  
  **Decision:** Use the mkdocs-macros-plugin to inject Jinja2 templates directly into Markdown files, allowing dynamic iteration over page objects during the build.  
  **Pro:** Eliminates manual index updates  
  **Pro:** Keeps logic inside standard Markdown files  
  **Con:** Markdown files containing Jinja syntax will display raw loops when viewed directly on GitHub's native viewer  


## **[ADR-3.0]** Repository Structure and CI/CD
**Created at:** 2026-05-28T21:54:43 | **Modified at:** 2026-05-28T21:54:43  

**Description:** Decisions regarding Git branching strategy and automated deployment pipelines.  

- ### **[ADR-3.1]** Branch Strategy  
  **Modified at:** 2026-05-28T21:54:43  
  **Problem:** Maintaining all the HTML content in the same branch as the Markdown source files and configuration can lead to a terrible experience for users that want to clone the repository and view the Markdown files directly on GitHub or his own device.  
  **Decision:** Maintain a single 'main' branch containing both the Markdown content (docs/) and configuration files. Generated HTML will be isolated to the 'gh-pages' branch.  
  **Pro:** Allows immediate local testing  
  **Pro:** Simplifies the Git workflow for content authors  
  **Pro:** Keeps main branch lightweight  
  **Con:** Mixes system configuration files with raw content in the same branch root  

- ### **[ADR-3.2]** Automate Build and Deployment via GitHub Actions  
  **Modified at:** 2026-05-28T21:54:43  
  **Problem:** Manual compilation of the MkDocs site and subsequent pushing to the gh-pages branch is repetitive and prone to error.  
  **Decision:** Implement a GitHub Actions workflow triggered on pushes to the main branch to automatically install dependencies, build the static site, and deploy to gh-pages.  
  **Pro:** Fully automated pipeline  
  **Pro:** Ensures production always reflects the main branch  
  **Pro:** No manual intervention required  
  **Con:** Relies on GitHub's CI/CD availability  


## **[ADR-4.0]** Content Organization and Navigation
**Created at:** 2026-05-28T21:54:43 | **Modified at:** 2026-06-04T17:05:17  

**Description:** Decisions regarding directory structure, metadata, and dynamic content generation for the knowledge base.  

- ### **[ADR-4.1]** Multilingual Directory Architecture  
  **Modified at:** 2026-05-28T21:54:43  
  **Problem:** Content must be available in Portuguese and English, requiring a standardized structure that allows easy navigation and automatic URL synchronization.  
  **Decision:** Organize content using the strict pattern `docs/<lang>/<category>/[sub-category]/<file>.md`. Equivalent files must share the exact same filename across language directories.  
  **Pro:** Clean separation of languages  
  **Pro:** Enables seamless language switching via the i18n plugin  
  **Pro:** Predictable path structure for content creators  
  **Con:** Requires discipline to maintain naming parity across the 'pt' and 'en' directories  

- ### **[ADR-4.2]** Invisible Metadata via YAML Front Matter  
  **Modified at:** 2026-05-28T21:54:43  
  **Problem:** Articles need to be categorized and tagged for searchability and related-content linking without polluting the visual reading experience.  
  **Decision:** Embed tags and categories exclusively within standard YAML front matter at the top of each Markdown document. This header will be parsed by the engine but not rendered as text in the final HTML.  
  **Pro:** Native support in MkDocs Material  
  **Pro:** Keeps the Markdown body clean  
  **Pro:** Enables automated aggregation and filtering  
  **Con:** Requires authors to follow a strict YAML schema for each post  

- ### **[ADR-4.3]** Dynamic Indexing  
  **Modified at:** 2026-06-04T17:05:17  
  **Problem:** Maintaining manual lists of articles within categories and subcategories is error-prone and scales poorly as the repository grows.  
  **Decision:** Use the `README.md` files (rendered as `index.html` by MkDocs) from language|category|subcategory subdirectories as entrypoint for each one. Inject Jinja macros into these files to automatically iterate and list all child contents.  
  **Pro:** Zero manual maintenance for category index pages  
  **Pro:** Preserves native GitHub navigation when reading raw files in the repository  
  **Con:** Raw Markdown files will display Jinja loop syntax when viewed directly on GitHub's native viewer  

- ### **[ADR-4.4]** Automated Content Showcases  
  **Modified at:** 2026-05-28T21:54:44  
  **Problem:** The main landing page and individual articles need to surface relevant content to keep readers engaged, without requiring manual curation.  
  **Decision:** Utilize Jinja macros and blog plugins to automatically render the 3 most recently published articles on the root `README.md`, and generate a simple list of up to 3 related articles based on shared tags at the bottom of each post.  
  **Pro:** Improves user engagement and content discoverability  
  **Pro:** Fully automated layout updates whenever a new article is pushed  
  **Con:** Increases the processing overhead during the static site generation build phase  

- ### **[ADR-4.5]** Main Entry Point  
  **Modified at:** 2026-06-04T16:59:59  
  **Problem:** We have different languages under `docs/`, a single README as root page would break the language selection.  
  **Decision:** Instead of using the repos's root `README` as the landing page, we will place a `README.md` in each language subdirectory, redirecting who connects to `/` endpoint to its desired language, with fallback to English. E.g: `{url}/` → `{url}/en/` rendering the `docs/en/README.md` page.  


## **[ADR-5.0]** License
**Created at:** 2026-05-29T20:48:25 | **Modified at:** 2026-06-04T16:10:01  

**Description:** Decisions defining the License structure and how they will be displayed.  

- ### **[ADR-5.1.0]** Source Code and Content Licenses  
  **Modified at:** 2026-06-04T16:01:14  
  **Problem:** The Source Code from the html generator and the Content from the Articles have different natures.  
  **Decision:** Use MIT for the source code, and CC BY 4.0 for the content under `docs/` directory.  
  - #### **[ADR-5.1.1]** CC Copies  
    **Modified at:** 2026-06-04T15:54:46  
    **Problem:** We should place a copy of the CC license under the `docs/` directory, but we have many languages in our structure.  
    **Decision:** Place a copy under each language subdirectory, e.g.: `docs/en/LICENSE.md` & `docs/pt/LICENSE.md`.  

- ### **[ADR-5.2]** CC Notice on Pages  
  **Modified at:** 2026-06-04T15:59:26  
  **Problem:** The CC note should appear on our content pages.  
  **Decision:** Our python script should place automatically a footer note in ALL the pages, with a link to the page `docs/{lang}/LICENSE.md` an to the official creative commons website `https://creativecommons.org/licenses/by/4.0/`.  

- ### **[ADR-5.3]** LICENSE Pages  
  **Modified at:** 2026-06-04T16:06:16  
  **Problem:** As the ADR-5.2 decides, we need to have a page inside our pages dedicated to the CC License copy.  
  **Decision:** Render the 'LICENSE' markdown placed at `docs/` - as decided on AR-5.1.1 - under the endpoint `/{lang}/LICENSE`, in each laguage, as any other page, but without the footer CC notice.  

- ### **[ADR-5.4]** README Notice  
  **Modified at:** 2026-06-04T16:10:01  
  **Problem:** The `README.md` is the "landing page" from our repository, we must add a License Notice declaring the scope of each one.  
  **Decision:** Write a "License" section, specifying the scopes from each LICENSE and link to them.  


