# Copyright (c) 2025-2026 Mark Buckwell and contributors
# SPDX-License-Identifier: MIT

import os
import sys
import subprocess
import shutil
import toml
import re
import importlib.util
import glob
import base64
import json
import urllib.request
import urllib.parse
import markdown
from bs4 import BeautifulSoup

def extract_md_files(nav_element):
    """Recursively walks the Zensical navigation tree to extract .md files in order."""
    files = []
    if isinstance(nav_element, str):
        if nav_element.endswith('.md'):
            files.append(nav_element)
    elif isinstance(nav_element, list):
        for item in nav_element:
            files.extend(extract_md_files(item))
    elif isinstance(nav_element, dict):
        for key, value in nav_element.items():
            files.extend(extract_md_files(value))
    return files

def discover_icon_dirs(config):
    """Discovers all valid .icons directories across project folders and active Python environments."""
    dirs = [
        os.path.abspath(os.path.join(os.getcwd(), "overrides", ".icons")),
        os.path.abspath(os.path.join(os.getcwd(), ".icons")),
        os.path.abspath(os.path.join(os.getcwd(), "docs", ".icons")),
        os.path.abspath(os.path.join(os.getcwd(), config.get('docs_dir', 'docs'), ".icons"))
    ]
    
    try:
        import site
        site_paths = []
        if hasattr(site, 'getsitepackages'):
            site_paths.extend(site.getsitepackages())
        if hasattr(site, 'getusersitepackages'):
            site_paths.append(site.getusersitepackages())
        
        for sp in site_paths:
            for pkg in ["material", "mkdocs_material", "zensical"]:
                dirs.append(os.path.join(sp, pkg, "templates", ".icons"))
                dirs.append(os.path.join(sp, pkg, ".icons"))
    except Exception:
        pass

    for local_dir in [".venv", "venv", "env"]:
        base_venv = os.path.join(os.getcwd(), local_dir)
        if os.path.isdir(base_venv):
            for pkg in ["material", "mkdocs_material", "zensical"]:
                dirs.extend(glob.glob(os.path.join(base_venv, "lib", "python*", "site-packages", pkg, "templates", ".icons")))
                dirs.extend(glob.glob(os.path.join(base_venv, "lib", "python*", "site-packages", pkg, ".icons")))
                dirs.extend(glob.glob(os.path.join(base_venv, "Lib", "site-packages", pkg, "templates", ".icons")))
                dirs.extend(glob.glob(os.path.join(base_venv, "Lib", "site-packages", pkg, ".icons")))

    valid_dirs = []
    for d in dirs:
        abs_d = os.path.abspath(d)
        if os.path.isdir(abs_d) and abs_d not in valid_dirs:
            valid_dirs.append(abs_d)
    return valid_dirs

def build_icon_registry(icon_dirs):
    """Scans all discovered directory frameworks and indexes vector targets recursively."""
    registry = {}
    for base_dir in icon_dirs:
        if not os.path.isdir(base_dir):
            continue
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.lower().endswith('.svg'):
                    full_path = os.path.abspath(os.path.join(root, file)).replace('\\', '/')
                    rel_path = os.path.relpath(full_path, base_dir).replace('\\', '/').lower()
                    
                    slug = os.path.splitext(rel_path)[0]
                    hyphen_slug = slug.replace('/', '-')
                    
                    registry[hyphen_slug] = full_path
                    registry[hyphen_slug.replace('_', '-')] = full_path
                    registry[hyphen_slug.replace('-', '_')] = full_path
                    
                    parts = slug.split('/')
                    if len(parts) > 1:
                        short_key = f"{parts[0]}-{parts[-1]}"
                        if short_key not in registry:
                            registry[short_key] = full_path
                        
                        if parts[0] == "fontawesome" and len(parts) > 2:
                            fa_key = f"fa-{parts[1]}-{parts[-1]}"
                            registry[fa_key] = full_path
                    
                    flat_key = parts[-1]
                    if flat_key not in registry:
                        registry[flat_key] = full_path
    return registry

def page_front_matter_flag(path, key):
    """True if path's YAML front matter sets key: true. Shared by
    page_excluded_from_word_count() and page_is_appendix(). Reads the
    original source file, not its preprocessed copy - preprocess_markdown()
    already strips the front matter by the time a page reaches
    compute_pdf_word_count() or the Lua numbering filter."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
    except OSError:
        return False
    if not text.startswith('---'):
        return False
    parts = text.split('---', 2)
    if len(parts) < 3:
        return False
    return bool(re.search(rf'^{re.escape(key)}:\s*true\s*$', parts[1], re.MULTILINE | re.IGNORECASE))

def page_excluded_from_word_count(path):
    """True if path's YAML front matter sets exclude_from_word_count: true -
    see "Word count" in customise.md. Used to skip pages like References,
    Acronyms, Glossary, and Originality & AI Use, which conventionally don't
    count toward a submission's word limit. Mirrors the same check in
    macros.py, used there for the website's {{ word_count }} variable."""
    return page_front_matter_flag(path, 'exclude_from_word_count')

def page_is_appendix(path):
    """True if path's YAML front matter sets is_appendix: true - see
    "Appendixes" in customise.md. Used to give the page's H1 (and any H2/H3
    beneath it) letter-based numbering ("Appendix A", "A.1", ...) instead of
    continuing the document's normal numeric sequence. Mirrors the same
    check in macros.py, used there for the website's own numbering."""
    return page_front_matter_flag(path, 'is_appendix')

def compute_pdf_word_count(markdown_paths):
    """Rough prose word count across the given already-preprocessed files:
    strips fenced/HTML code blocks, inline code, HTML tags/comments, and
    markdown link/image/emphasis syntax before splitting on whitespace. Used
    to fill in the cover page's {WORDCOUNT} marker (see index.md); excludes
    the cover page itself and the auto-generated Table of Contents, since
    neither is "content".

    Handles both the markdown-syntax fences preprocess_markdown() still
    produces and the real <pre>/<code> blocks render_page_html() produces
    (see zendoc-template#92) - the generic <[^>]+> tag strip below doesn't
    remove a code block's own *text content*, only markdown's fence
    delimiters do that, so an HTML code block needs its content dropped
    explicitly first or its source code inflates the count as if it were
    prose.
    """
    total_words = 0
    for path in markdown_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
        except OSError:
            continue
        text = re.sub(r'<!--.*?-->', ' ', text, flags=re.DOTALL)
        text = re.sub(r'<pre[^>]*>.*?</pre>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'```.*?```', ' ', text, flags=re.DOTALL)
        text = re.sub(r'~~~.*?~~~', ' ', text, flags=re.DOTALL)
        text = re.sub(r'`[^`]*`', ' ', text)
        text = re.sub(r'<code[^>]*>.*?</code>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', text)
        text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
        text = re.sub(r'[#*_~>|]', ' ', text)
        total_words += len(text.split())
    return total_words

def get_latest_release_tag(repo_url):
    """Returns the latest published release's tag name (e.g. "v0.0.11") for
    a GitHub or GitLab repo_url, for the PDF cover page's optional {RELEASE}
    marker (see index.md) - the PDF-side equivalent of the version already
    shown live in the website's own header repo widget (see issue #61),
    which fetches it client-side; Pandoc/WeasyPrint has no JS engine to do
    the same, so this fetches it once here instead, at PDF build time.

    Deliberately not computed in macros.py alongside repo_url/word_count,
    since that would add a network call to every website rebuild (including
    every live-reload save during `zensical serve`) for a value only the PDF
    actually needs.

    Returns "" on any failure - no repo_url, an unsupported host, no
    published release, network unavailable, rate-limited, etc. - so a
    missing release can never break the build; the caller drops the whole
    {RELEASE} line in that case (see main()), since most forks of this
    template will never publish a release at all."""
    if not repo_url:
        return ""
    parsed = urllib.parse.urlparse(repo_url)
    host = (parsed.hostname or "").lower()
    owner_repo = parsed.path.strip("/")
    if not owner_repo:
        return ""
    try:
        if "github.com" in host:
            api_url = f"https://api.github.com/repos/{owner_repo}/releases/latest"
        elif "gitlab" in host:
            project = urllib.parse.quote(owner_repo, safe="")
            api_url = f"https://{parsed.hostname}/api/v4/projects/{project}/releases/permalink/latest"
        else:
            return ""
        with urllib.request.urlopen(api_url, timeout=5) as resp:
            data = json.load(resp)
        return str(data.get("tag_name") or "")
    except Exception:
        return ""

def _render_one_mermaid_diagram(diagram_source, temp_build_dir, mermaid_state):
    """Renders a single Mermaid diagram's source to a static SVG file via a
    local mermaid-cli install under tools/mermaid, returning the absolute SVG
    path, or None if mermaid-cli isn't installed or the render failed. The
    actual subprocess invocation shared by render_mermaid_diagrams() (the
    markdown-syntax-based pipeline) and render_page_html() (see
    zendoc-template#92's HTML-based pipeline, which finds diagram source in
    <pre class="mermaid"> rather than a ```mermaid fence)."""
    mmdc_bin = os.path.abspath(os.path.join("tools", "mermaid", "node_modules", ".bin", "mmdc"))
    if not os.path.exists(mmdc_bin):
        return None
    # Mermaid's default node/edge labels are HTML <foreignObject> content, which
    # WeasyPrint's SVG renderer can't display (text silently vanishes). Forcing
    # htmlLabels off makes mermaid emit plain SVG <text>/<tspan> labels instead.
    mmdc_config = os.path.abspath(os.path.join("tools", "mermaid", "mermaid_pdf_config.json"))
    # --no-sandbox: CI runners launch Chromium as root, where its sandbox refuses
    # to start without this; harmless when running unprivileged locally too.
    puppeteer_config = os.path.abspath(os.path.join("tools", "mermaid", "puppeteer_config.json"))

    mermaid_dir = os.path.join(temp_build_dir, "mermaid_diagrams")
    mermaid_state['count'] += 1
    idx = mermaid_state['count']
    os.makedirs(mermaid_dir, exist_ok=True)
    mmd_path = os.path.abspath(os.path.join(mermaid_dir, f"diagram_{idx}.mmd"))
    svg_path = os.path.abspath(os.path.join(mermaid_dir, f"diagram_{idx}.svg"))
    with open(mmd_path, "w", encoding="utf-8") as f:
        f.write(diagram_source)

    try:
        subprocess.run(
            [mmdc_bin, "-i", mmd_path, "-o", svg_path, "-b", "transparent",
             "-c", mmdc_config, "-p", puppeteer_config],
            check=True, capture_output=True, text=True, timeout=60
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        detail = getattr(e, "stderr", None) or str(e)
        print(f"\u26a0\ufe0f  Mermaid render failed for diagram {idx}: {detail}")
        return None
    return svg_path

def render_mermaid_diagrams(content, temp_build_dir, mermaid_state):
    """Pre-renders ```mermaid fenced code blocks (see
    https://zensical.org/docs/authoring/diagrams/) to static SVGs (see
    _render_one_mermaid_diagram()). WeasyPrint has no JS engine to run
    Mermaid.js client-side the way the live Zensical site does, so the
    diagram source must become an image before Pandoc ever sees it. The
    emitted markdown image tag is then picked up and base64-inlined by the
    existing image encoder further down in preprocess_markdown().
    """
    def replace(match):
        indent = match.group(1)
        raw_block = match.group(2)
        diagram_source = "\n".join(
            line[len(indent):] if line.startswith(indent) else line.lstrip()
            for line in raw_block.splitlines()
        )
        svg_path = _render_one_mermaid_diagram(diagram_source, temp_build_dir, mermaid_state)
        if svg_path is None:
            return match.group(0)
        return f'{indent}![Mermaid diagram]({svg_path})'

    return re.sub(
        r'^([ \t]*)```[ \t]*\{?\.?mermaid\}?[ \t]*\n(.*?)\n\1```[ \t]*$',
        replace,
        content,
        flags=re.MULTILINE | re.DOTALL
    )

def build_page_anchor_map(md_files):
    """Maps each nav markdown file (relative to docs_dir, e.g.
    "starthere/installtooling.md") to a deterministic anchor id (e.g.
    "page-starthere-installtooling"), used by tag_first_heading() and
    rewrite_internal_md_links() below to fix issue #16: build_pdf.py
    concatenates every page into one PDF document, so a link like
    installtooling.md that resolves fine on the website (a separate page)
    has nothing to point at in the PDF - Pandoc treats it as a link to an
    external file at whatever absolute path the PDF happened to be built
    from. Rewriting such links to in-document anchors instead fixes that."""
    page_anchor_map = {}
    for f in md_files:
        key = os.path.normpath(f).replace('\\', '/')
        slug = re.sub(r'[^a-z0-9]+', '-', key.lower().rsplit('.', 1)[0]).strip('-')
        page_anchor_map[key] = f'page-{slug}'
    return page_anchor_map

def _virtual_page_path(docs_rel_path):
    """The clean-URL "virtual directory" a docs_dir-relative page path maps
    to under Zensical's use_directory_urls convention - e.g.
    "starthere/installtooling.md" becomes "starthere/installtooling" (one
    level deeper than its own containing directory), while an index.md
    stays at its containing directory rather than nesting deeper (e.g.
    "starthere/index.md" -> "starthere", top-level "index.md" -> ""). Used
    by build_virtual_page_map()/render_page_html() to resolve a real
    <a href> - already rewritten to this same clean-URL form by
    zensical.extensions.links.LinksTreeprocessor (regular links) or
    zendoc's own cross_page_href() (\\ref{}/\\cite{}/\\gls{} links) by the
    time render() returns the page's HTML - back to the real page it
    points at."""
    dirname = os.path.dirname(docs_rel_path)
    basename = os.path.basename(docs_rel_path)
    if basename.lower() == 'index.md':
        return dirname
    slug = basename.rsplit('.', 1)[0]
    return os.path.join(dirname, slug).replace('\\', '/') if dirname else slug

def build_virtual_page_map(md_files):
    """Maps each nav markdown file's clean-URL virtual directory path (see
    _virtual_page_path()) to the same anchor id build_page_anchor_map()
    assigns it, so render_page_html() can resolve a rewritten <a href>
    without needing to know the original .md filename at all."""
    anchor_map = build_page_anchor_map(md_files)
    virtual_map = {}
    for f in md_files:
        key = os.path.normpath(f).replace('\\', '/')
        virtual_map[_virtual_page_path(key)] = anchor_map[key]
    return virtual_map

def to_base64_data_uri(img_src, base_dir):
    """Resolves a (possibly relative) image src to an absolute path under
    base_dir and returns it as a base64 data: URI, so the standalone
    compiled document doesn't depend on relative file paths resolving
    correctly from wherever Pandoc happens to run - used by render_page_html()
    (see zendoc-template#92)."""
    if img_src.startswith('data:'):
        return img_src

    path_part = img_src.split('#')[0]
    if path_part.startswith('file://'):
        path_part = path_part[7:]

    img_path = os.path.abspath(os.path.join(base_dir, path_part))
    if not os.path.exists(img_path):
        img_path = os.path.abspath(path_part)

    if os.path.exists(img_path) and os.path.isfile(img_path):
        try:
            ext = os.path.splitext(img_path)[1].lower().strip('.')
            mime_type = f"image/{ext}"
            if ext == "svg": mime_type = "image/svg+xml"
            elif ext == "jpg": mime_type = "image/jpeg"
            with open(img_path, 'rb') as f:
                b64_content = base64.b64encode(f.read()).decode('utf-8')
            return f"data:{mime_type};base64,{b64_content}"
        except Exception:
            pass
    return img_src

# Mirrors the border-left-color set per admonition type in the
# .admonition.<type> CSS rules in main()'s compiled stylesheet, so the icon
# matches the coloured bar rather than rendering in its raw (black) fill.
ADMONITION_ACCENT_COLORS = {
    "note": "#448aff", "abstract": "#00b0ff", "info": "#00b8d4", "tip": "#00bfa5",
    "success": "#00c853", "question": "#64dd17", "warning": "#ff9100", "failure": "#ff5252",
    "danger": "#ff1744", "bug": "#ec407a", "example": "#651fff", "quote": "#9e9e9e",
}

def admonition_icon_svg(adm_type, config, icon_registry):
    """Resolves an admonition type (note, warning, tip, ...) to its
    accent-coloured icon SVG markup, using the same icon set configured for
    the website's admonitions in project.theme.icon.admonition (zensical.toml)
    - see https://zensical.org/docs/authoring/admonitions/#supported-types.
    Zensical's own admonition HTML has no icon in it at all (confirmed
    directly - the icon is a website-only CSS mask-image/background trick
    referencing a theme asset that doesn't exist in the standalone PDF), so
    render_page_html() inserts one explicitly instead - see zendoc-template#92.
    Returns None if nothing is configured or the icon file can't be found."""
    project_cfg = config.get('project')
    theme_cfg = project_cfg.get('theme') if isinstance(project_cfg, dict) else None
    icon_cfg = theme_cfg.get('icon') if isinstance(theme_cfg, dict) else None
    adm_icon_cfg = icon_cfg.get('admonition') if isinstance(icon_cfg, dict) else None
    shortcode = adm_icon_cfg.get(adm_type) if isinstance(adm_icon_cfg, dict) else None
    if not shortcode:
        return None
    key = shortcode.strip('/').lower().replace('/', '-')
    abs_path = icon_registry.get(key)
    if not abs_path:
        return None
    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            svg_data = f.read()
    except OSError:
        return None
    accent_color = ADMONITION_ACCENT_COLORS.get(adm_type)
    if accent_color:
        # "currentColor" resolves against the CSS `color` property, not
        # `fill` - setting fill="..." on the <svg> root has no effect on a
        # descendant path's fill="currentColor", so replace it directly.
        svg_data = re.sub(r'currentColor', accent_color, svg_data, flags=re.IGNORECASE)
    return svg_data

def render_page_html(file_path, config, page_anchor_map, temp_build_dir, mermaid_state, is_index=False, repo_url='', icon_registry=None):
    """New render pipeline (see zendoc-template#92): renders this page
    through Zensical's own zensical.markdown.render.render() - the exact
    same zendoc/pymdownx extensions, real Jinja macro/variable substitution,
    and {% if %} conditional evaluation the live website uses - then lightly
    cleans up the resulting HTML for Pandoc's benefit, instead of the ~1000
    lines of regex preprocess_markdown() uses to hand-translate Zensical/
    pymdownx/zendoc markdown syntax (admonitions, tabs, grid cards, captions,
    superfences attributes, attr_list spans, mark/insert/keys, {% if %}
    conditionals) into a Pandoc-compatible markdown dialect - all of which
    Pandoc's own HTML reader already understands correctly once it's real
    HTML, no translation needed. Requires zensical.config.parse_config() to
    have already been called once (see main()) so zensical.config.get_config()
    - which zensical.markdown.render.render() and zendoc's own Zensical
    auto-detection both read - is actually populated.

    Math (pymdownx.arithmatex): Pandoc's HTML reader has no special
    awareness of <div class="arithmatex">/<span class="arithmatex"> the way
    its *markdown* reader recognises native $...$/$$...$$ as a real Math
    AST node, so the existing Lua filter's Math() handler never fires for
    HTML input - handled instead by dedicated Div()/Span() handlers in the
    Lua filter (see main()), matched by class rather than AST node type.

    Returns real HTML, fed to Pandoc with -f html - see main().
    """
    from zensical.markdown.render import render as zensical_render

    with open(file_path, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    docs_dir = config.get('docs_dir', 'docs')
    current_docs_rel_path = os.path.normpath(os.path.relpath(file_path, docs_dir)).replace('\\', '/')

    result = zensical_render(raw_content, current_docs_rel_path, current_docs_rel_path)
    soup = BeautifulSoup(result['content'], 'html.parser')

    # Website-only presentational output with no PDF equivalent: the PDF
    # numbers headings separately via the Lua filter's Header() function
    # and gets equivalent CSS added directly to the compiled stylesheet
    # instead (see reference_style_css/acronym_style_css/glossary_style_css
    # in main()), so heading_counter_reset()/reference_style()/
    # acronym_style()/glossary_style()'s injected <style> blocks are just
    # noise here. toc's hover-to-copy permalink links are meaningless in a
    # PDF too.
    for style in soup.find_all('style'):
        style.decompose()
    for permalink in soup.select('a.headerlink'):
        permalink.decompose()
    # zensical.extensions.glightbox wraps every image in a click-to-zoom
    # <a class="glightbox" href="..."> - a website-only JS lightbox feature
    # with no PDF equivalent, and whose href uses a different relative-path
    # convention than the <img> it wraps (assuming the page's own clean URL
    # is itself a directory, e.g. "../images/x.png" from
    # "starthere/startediting/" - one level deeper than the <img src>'s
    # "images/x.png" resolved directly against the source file's own
    # directory), which Pandoc/WeasyPrint then fails to resolve as a broken
    # link. Unwrapping to just the <img> avoids resolving that href at all.
    for lightbox_link in soup.select('a.glightbox'):
        lightbox_link.unwrap()

    # Embedded videos (e.g. a YouTube <iframe>, see starthere.md): confirmed
    # a raw <iframe> left for Pandoc/WeasyPrint to handle produces a stray,
    # unwanted heading in the compiled PDF (WeasyPrint attempting to fetch
    # the iframe's src and something in that response ending up parsed as
    # real page content) - a static PDF can't embed a live video player
    # regardless, so replace it with a "Watch Video" admonition link instead
    # (same treatment preprocess_markdown()'s video_iframe_replacer() gives
    # it, rebuilt here as real admonition HTML rather than "!!! info"
    # markdown syntax).
    for iframe in soup.find_all('iframe'):
        src = iframe.get('src', '')
        if not src:
            iframe.decompose()
            continue
        if 'youtube.com/embed/' in src:
            video_url = src.replace('youtube.com/embed/', 'youtube.com/watch?v=').split('?')[0]
        else:
            video_url = src
        video_title = iframe.get('title', '').strip() or 'Video Tutorial'
        admonition = soup.new_tag('div')
        admonition['class'] = ['admonition', 'info']
        title_p = soup.new_tag('p')
        title_p['class'] = 'admonition-title'
        title_p.string = video_title
        body_p = soup.new_tag('p')
        strong = soup.new_tag('strong')
        link = soup.new_tag('a', href=video_url)
        link.string = 'Watch Video'
        strong.append(link)
        body_p.append(strong)
        admonition.append(title_p)
        admonition.append(body_p)
        parent = iframe.parent
        # Only replace the immediate wrapping <div> too if the iframe is its
        # only real content - otherwise this would swallow unrelated sibling
        # content (e.g. a grid card, or the whole page's own wrapper div).
        if parent is not None and parent.name == 'div' and len(list(parent.find_all(True))) == 1:
            parent.replace_with(admonition)
        else:
            iframe.replace_with(admonition)

    # Content tabs: pymdownx.blocks.tab renders each tab's label as an
    # inline <label> sibling inside a wrapping <div class="tabbed-labels">.
    # Pandoc's HTML reader merges adjacent inline-level siblings with no
    # block boundary between them into one Plain block - confirmed this
    # collapses every label in a tabbed-set into one unseparated run of
    # text, with no way to recover the boundary afterward in a Lua filter.
    # Rewriting each into its own <p> here, before Pandoc's reader ever
    # sees it, is the only point this can be fixed - see the Lua filter's
    # tabbed-set Div() handler for the matching reconstruction into
    # tabbox-header/tabbox-body (the same shape the existing tabbox
    # convention already produces, so no CSS changes are needed to style
    # it).
    for radio in soup.select('input[type="radio"]'):
        radio.decompose()
    for label in soup.select('div.tabbed-labels label'):
        p = soup.new_tag('p')
        p['class'] = 'zendoc-tab-label'
        p.string = label.get_text()
        label.replace_with(p)

    # Admonition icons: Zensical's own admonition HTML has no icon markup at
    # all - the website draws it via a CSS trick referencing a theme asset
    # URL that doesn't exist in the standalone PDF (confirmed directly - a
    # built admonition's title paragraph is just its plain text, nothing
    # else). Insert the configured, accent-coloured icon explicitly instead
    # - see admonition_icon_svg().
    if icon_registry:
        for div in soup.select('div.admonition'):
            classes = div.get('class', [])
            adm_type = next((c for c in classes if c != 'admonition'), None)
            title_p = div.find('p', class_='admonition-title')
            if adm_type and title_p is not None:
                svg_markup = admonition_icon_svg(adm_type, config, icon_registry)
                if svg_markup:
                    # A raw inline <svg> confirmed not to survive Pandoc's
                    # HTML-to-HTML round trip through to WeasyPrint at all
                    # (tested directly, in isolation, outside this pipeline)
                    # - a base64 data: URI <img>, the same encoding
                    # to_base64_data_uri() already uses for regular images,
                    # renders reliably instead.
                    b64 = base64.b64encode(svg_markup.encode('utf-8')).decode('utf-8')
                    # Reuses the compiled stylesheet's existing img.twemoji
                    # rule (1.1em, sized for an inline icon) rather than a
                    # bare width/height attribute - the generic "img {
                    # max-width: 100% !important }" rule elsewhere in the
                    # same stylesheet otherwise overrides a plain attribute,
                    # scaling the icon up to fill the whole admonition width.
                    icon_img = soup.new_tag(
                        'img',
                        src=f'data:image/svg+xml;base64,{b64}',
                        **{'class': 'twemoji'},
                    )
                    title_p.insert(0, ' ')
                    title_p.insert(0, icon_img)

    # Any other inline icon/emoji shortcode (pymdownx.emoji renders these as
    # a raw inline <svg> inside a <span class="twemoji ...">, e.g. a grid
    # card's own ":material-clock-fast:" title icon) - confirmed, the same
    # way as admonition icons above, that a raw inline <svg> doesn't survive
    # Pandoc's HTML-to-HTML round trip through to WeasyPrint at all (tested
    # directly, in isolation). Converts every remaining <svg> anywhere on
    # the page to a base64 data: URI <img>, reusing the same img.twemoji
    # sizing rule.
    for svg in soup.find_all('svg'):
        b64 = base64.b64encode(str(svg).encode('utf-8')).decode('utf-8')
        icon_img = soup.new_tag(
            'img',
            src=f'data:image/svg+xml;base64,{b64}',
            **{'class': 'twemoji'},
        )
        svg.replace_with(icon_img)

    # Footnotes: Zensical's own markdown pipeline (python-markdown's
    # footnote extension) renders these as a <sup id="fnref:N"><a
    # class="footnote-ref">N</a></sup> at the reference point, with every
    # footnote's own text collected into one <div class="footnote"><ol>
    # <li id="fn:N"><p>...</p></li></ol></div> at the *end* of the page -
    # never a Pandoc-native Note element (that only exists when Pandoc's
    # own *markdown* reader parses "[^1]" syntax directly; feeding Pandoc
    # pre-rendered HTML here means it just sees an ordinary <div>/<ol>/
    # <sup>, not a Note). The Lua filter's Note() function (and the
    # .pdf-footnote float: footnote mechanism it feeds) was written for
    # that native-Note case and silently never fires here - confirmed
    # directly against the built PDF: a footnote's own text rendered
    # wherever the <div class="footnote"> happened to fall in normal
    # document flow, often several pages after its own reference, at
    # regular body-text size rather than float:footnote's smaller
    # bottom-of-page placement. Moves each footnote's text inline at its
    # own reference point instead, in the same <span class="pdf-footnote">
    # shape Note() used to produce, so float: footnote can anchor it to
    # the correct page.
    footnote_div = soup.find('div', class_='footnote')
    if footnote_div is not None:
        for li in footnote_div.select('li[id^="fn:"]'):
            ref = soup.find('sup', id=f'fnref:{li["id"][3:]}')
            if ref is None:
                continue
            backref = li.find('a', class_='footnote-backref')
            if backref is not None:
                backref.decompose()
            span = soup.new_tag('span', **{'class': 'pdf-footnote'})
            for p in li.find_all('p', recursive=False):
                p.unwrap()
            for child in list(li.contents):
                span.append(child)
            ref.replace_with(span)
        footnote_div.decompose()

    # Mermaid diagrams: WeasyPrint has no JS engine to run Mermaid.js
    # client-side - pre-render each <pre class="mermaid">'s source to a
    # static SVG via the same mermaid-cli install render_mermaid_diagrams()
    # uses (see _render_one_mermaid_diagram()), just reading the diagram
    # source from the rendered HTML instead of a markdown fence.
    for pre in soup.select('pre.mermaid'):
        svg_path = _render_one_mermaid_diagram(pre.get_text(), temp_build_dir, mermaid_state)
        if svg_path is not None:
            img = soup.new_tag('img', src=svg_path, alt='Mermaid diagram')
            pre.replace_with(img)

    # Zensical rewrites every page-relative reference - not just <a href>
    # links to other pages, but an <img src> too - relative to this page's
    # own clean-URL *virtual* directory (e.g. "starthere/startediting.md"'s
    # virtual directory is "starthere/startediting/", one level deeper than
    # its own containing directory), matching its use_directory_urls
    # convention - see _virtual_page_path(). Confirmed directly: a
    # <img src="../images/x.png"> here really does mean
    # "docs/starthere/images/x.png", not "docs/images/x.png" as a naive
    # relative-to-the-source-file resolution would assume.
    current_virtual_dir = _virtual_page_path(current_docs_rel_path)
    virtual_base_dir = os.path.join(docs_dir, current_virtual_dir)

    # Images: base64-embed every local image reference directly into the
    # HTML, so the standalone compiled document doesn't depend on relative
    # file paths resolving correctly from wherever Pandoc happens to run -
    # same reasoning as to_base64_data_uri()'s other call sites, just
    # targeting real <img> tags directly (render() has already resolved
    # markdown image syntax into these).
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if src and not src.startswith('data:'):
            img['src'] = to_base64_data_uri(src, virtual_base_dir)

    # Cross-page links: build_pdf.py concatenates every page into one PDF
    # document, so a link like installtooling.md (fine on the website, a
    # separate page) has nothing to point at here - rewrite to the
    # deterministic in-document anchor from page_anchor_map instead (see
    # build_page_anchor_map() / issue #16). By the time render() returns
    # this page's HTML, every such link - both a regular markdown link
    # (rewritten by zensical.extensions.links.LinksTreeprocessor) and a
    # \ref{}/\cite{}/\gls{} link (rewritten by zendoc's own
    # cross_page_href()) - already uses the same clean-URL virtual-
    # directory form.
    virtual_page_map = {_virtual_page_path(key): anchor for key, anchor in page_anchor_map.items()}
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith(('http://', 'https://', 'mailto:', '#')):
            continue
        target, _, frag = href.partition('#')
        if not target:
            continue
        resolved = os.path.normpath(os.path.join(current_virtual_dir, target)).replace('\\', '/').rstrip('/')
        anchor = virtual_page_map.get(resolved)
        if anchor is not None:
            a['href'] = f'#{frag}' if frag else f'#{anchor}'

    # Repo file links: a relative link to a non-markdown repo file (e.g.
    # [extra.css](../stylesheets/extra.css) in customise.md) isn't part of
    # the concatenated PDF at all (unlike a page link above) - resolved
    # relative to wherever Pandoc happens to run, it's meaningless (and
    # reveals a local file path) to anyone else reading the PDF, so rewrite
    # it to the file's canonical GitHub/GitLab "blob" URL instead (see
    # issue #19), same as rewrite_repo_file_links(). Unlike the clean-URL
    # page links above, this one *is* just a direct relative path from the
    # source file's own directory - Zensical doesn't clean-URL-rewrite
    # links to non-page assets.
    current_dir = os.path.dirname(current_docs_rel_path)
    repo_url_lower = repo_url.lower()
    if 'github.com' in repo_url_lower:
        blob_prefix = f'{repo_url}/blob/main/'
    elif 'gitlab' in repo_url_lower:
        blob_prefix = f'{repo_url}/-/blob/main/'
    else:
        blob_prefix = None
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith(('http://', 'https://', 'mailto:', '#', '/')):
            continue
        if blob_prefix is None:
            a.unwrap()
            continue
        repo_rel_path = os.path.normpath(os.path.join(docs_dir, current_dir, href)).replace('\\', '/')
        a['href'] = f'{blob_prefix}{repo_rel_path}'

    # Prepend-position figure-caption/table-caption ("/// figure-caption | <"
    # or "/// table-caption | <" - see "Captions" in customise.md): Pandoc's
    # Figure AST node stores Caption and content as two separate,
    # independently-typed fields rather than as ordered children reflecting
    # the original DOM position, and Pandoc's own HTML writer always
    # re-emits a Figure's <figcaption> *after* its content when serializing
    # back to HTML for WeasyPrint - confirmed directly (isolated test: a
    # <figcaption> placed first in the source HTML still comes out last in
    # Pandoc's own HTML writer output), discarding "prepend" positioning
    # entirely regardless of input order. A Div's children, unlike a
    # Figure's, ARE emitted in original document order - so retag any
    # figure whose <figcaption> comes first to a <div> (preserving id/
    # class) and unwrap the <figcaption> itself (also confirmed: Pandoc's
    # HTML reader treats a bare <figcaption> not inside a <figure> as
    # ordinary flow content), leaving the caption as this element's first
    # child block. The Lua filter's Div() handler applies the same
    # "Figure "/"Table " + chapter-prefix numbering to this case that its
    # Figure() handler applies to the (unaffected) default append-position
    # case.
    for figure in soup.find_all('figure', class_=['zendoc-figure-caption', 'zendoc-table-caption']):
        first_child = figure.find(True, recursive=False)
        if first_child is not None and first_child.name == 'figcaption':
            figure.name = 'div'
            first_child.unwrap()

    # Pandoc's native Para AST node has no attribute field at all (unlike
    # Div/Header/CodeBlock/Table/Figure, which all carry one) - confirmed
    # directly: a <p id="..." class="...">, once read by Pandoc's HTML
    # reader, comes out the other end as a bare Para with both the id *and*
    # the class silently gone. This is exactly the shape every attr_list
    # citation/acronym/glossary definition takes ({: #id .reference
    # data-cite-text="..." } on a plain paragraph - see "References and
    # bibliography" in customise.md), and the cover page's own title lines
    # ({: .title-ctr-b4 } etc.) - both would otherwise silently lose their
    # id/styling with no error at all. Retagging as a <div> (which Pandoc's
    # reader does preserve attributes on) fixes both at once.
    for p in soup.find_all('p'):
        classes = p.get('class') or []
        # zendoc-tab-label (see above) deliberately stays a <p>: the Lua
        # filter's tabbed-set Div() handler reads it as a Plain/Para whose
        # .content is a plain inline list, matching Pandoc's own Para AST
        # node - retagging it to a Div here too would change its .content
        # to a list of blocks instead, breaking that handler.
        if 'zendoc-tab-label' in classes:
            continue
        if p.get('id') or classes:
            p.name = 'div'

    # Cover page: every heading here (there's usually just one, hidden) is
    # decorative, not a real chapter - unnumbered/unlisted/hidden from the
    # Lua filter's Header() counter and the table of contents, matching
    # preprocess_markdown()'s own tag_unnumbered() handling for is_index.
    # Wrapped in the same .cover-page class the compiled stylesheet already
    # styles against.
    if is_index:
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            classes = heading.get('class', [])
            for extra_class in ('hidden', 'unnumbered', 'unlisted'):
                if extra_class not in classes:
                    classes.append(extra_class)
            heading['class'] = classes
        cover_div = soup.new_tag('div')
        cover_div['class'] = 'cover-page'
        for child in list(soup.contents):
            cover_div.append(child)
        soup.append(cover_div)

    # This page's own anchor (see build_page_anchor_map() / issue #16):
    # give the first real heading that id directly (same approach as
    # tag_first_heading(), just setting a real HTML attribute rather than a
    # Pandoc {#id} block), and flag it .appendix if this page is one, for
    # the Lua filter's Header() to letter instead of number it (see
    # page_is_appendix() / issue #24).
    own_anchor = page_anchor_map.get(current_docs_rel_path)
    first_heading = soup.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    if own_anchor and first_heading is not None:
        first_heading['id'] = own_anchor
        if page_is_appendix(file_path):
            classes = first_heading.get('class', [])
            classes.append('appendix')
            first_heading['class'] = classes

    return str(soup)

def main():
    if not os.path.exists('zensical.toml'):
        print("❌ Error: zensical.toml not found in the current directory.")
        sys.exit(1)
        
    with open('zensical.toml', 'r', encoding='utf-8') as f:
        config = toml.load(f)
        
    project_section = config.get('project', {})
    project_extra = project_section.get('extra', {}) if isinstance(project_section, dict) else {}
    heading_numbering_enabled = bool(project_extra.get('heading_numbering', True)) if isinstance(project_extra, dict) else True
    reference_style_global = str(project_extra.get('reference_style', 'european') if isinstance(project_extra, dict) else 'european').strip().lower() == 'global'
    # Spacing/indent values behind reference_style_global above (see
    # macros.py's matching _reference_style_values(), which the website's
    # reference_style()/acronym_style()/glossary_style() macros use) -
    # project.extra.reference_spacing_european/reference_indent_global/
    # reference_spacing_global in zensical.toml. reference_spacing_european
    # is also used, unconditionally, for the Acronyms/Glossary pages' PDF
    # spacing below, same as on the website.
    reference_spacing_european = str(project_extra.get('reference_spacing_european', '-0.8em')) if isinstance(project_extra, dict) else '-0.8em'
    reference_indent_global = str(project_extra.get('reference_indent_global', '1.27cm')) if isinstance(project_extra, dict) else '1.27cm'
    reference_spacing_global = str(project_extra.get('reference_spacing_global', '2em')) if isinstance(project_extra, dict) else '2em'
    # PDF page size/margins (see "Page size and margins" in customise.md) -
    # project.extra.pdf_page_size/pdf_margin_{top,right,bottom,left} in
    # zensical.toml, substituted into the @page CSS block below. No
    # validation: an invalid CSS length/size just silently breaks the PDF
    # layout, the same as it always has when this was a raw CSS edit.
    pdf_page_size = str(project_extra.get('pdf_page_size', 'A4')) if isinstance(project_extra, dict) else 'A4'
    pdf_margin_top = str(project_extra.get('pdf_margin_top', '2cm')) if isinstance(project_extra, dict) else '2cm'
    pdf_margin_right = str(project_extra.get('pdf_margin_right', '2cm')) if isinstance(project_extra, dict) else '2cm'
    pdf_margin_bottom = str(project_extra.get('pdf_margin_bottom', '2cm')) if isinstance(project_extra, dict) else '2cm'
    pdf_margin_left = str(project_extra.get('pdf_margin_left', '2cm')) if isinstance(project_extra, dict) else '2cm'
    # PDF running header/footer text colour, font size, and divider line
    # colour (see "Page header"/"Page footer" in customise.md) -
    # project.extra.pdf_header_footer_{font_size,color,divider_color} in
    # zensical.toml, substituted into all four @top-left/@top-right/
    # @bottom-left/@bottom-right corners below. One setting each (not one
    # per corner): nothing in the current design differentiates header from
    # footer or left from right here.
    pdf_header_footer_font_size = str(project_extra.get('pdf_header_footer_font_size', '10pt')) if isinstance(project_extra, dict) else '10pt'
    pdf_header_footer_color = str(project_extra.get('pdf_header_footer_color', '#555555')) if isinstance(project_extra, dict) else '#555555'
    pdf_header_footer_divider_color = str(project_extra.get('pdf_header_footer_divider_color', '#e2e8f0')) if isinstance(project_extra, dict) else '#e2e8f0'
    nav = project_section.get('nav', []) if isinstance(project_section, dict) else []
    if not nav: nav = config.get('nav', [])
    if not nav:
        print("❌ Error: No 'nav' section found in zensical.toml.")
        sys.exit(1)
        
    md_files = extract_md_files(nav)
    docs_dir = config.get('docs_dir', 'docs')
    full_paths = [os.path.join(docs_dir, f) for f in md_files]
    valid_paths = [p for p in full_paths if os.path.exists(p)]
    if not valid_paths:
        print("❌ Error: No valid markdown files found.")
        sys.exit(1)
    page_anchor_map = build_page_anchor_map(md_files)

    # Populates zensical.config's module-level config (as a side effect of
    # parsing zensical.toml through Zensical's own loader, not the toml.load()
    # above) so zensical.markdown.render.render() - called per page below via
    # render_page_html() (see zendoc-template#92) - resolves real Jinja
    # macro/variable substitution and {% if %} conditionals exactly like the
    # live website, and so zendoc.headings/citations/glossary's own Zensical
    # auto-detection (nav pre-scan, shared cross-page registries) works the
    # same way here as it does under `zensical build`/`zensical serve`.
    import zensical.config as _zensical_config
    _zensical_config.parse_config('zensical.toml')

    calculated_vars = {}
    macros_module = None
    if os.path.exists('macros.py'):
        print("🔧 Executing macros.py environment maps...")
        try:
            spec = importlib.util.spec_from_file_location("macros", "macros.py")
            macros_module = importlib.util.module_from_spec(spec)
            sys.path.insert(0, os.getcwd())
            spec.loader.exec_module(macros_module)
            for attr in dir(macros_module):
                if not attr.startswith('__'):
                    val = getattr(macros_module, attr)
                    if isinstance(val, (bool, str, int, float)): calculated_vars[attr] = val
                    elif isinstance(val, dict): calculated_vars.update(val)
            if hasattr(macros_module, 'define_env'):
                class AttributeDict(dict):
                    def getattr(self, attr): return self.get(attr)
                    def setattr(self, attr, value): self[attr] = value
                class MockEnv:
                    def __init__(self):
                        self.variables = AttributeDict()
                        self.conf = {}
                    def macro(self, func, name=None): return func
                env_obj = MockEnv()
                macros_module.define_env(env_obj)
                for k, v in env_obj.variables.items():
                    if isinstance(v, (bool, str, int, float)): calculated_vars[k] = v
        except Exception as e:
            print(f"⚠️ Warning: Encountered an issue while executing macros.py: {e}")

    theme_section = project_section.get('theme', {}) if isinstance(project_section, dict) else config.get('theme', {})
    font_section = theme_section.get('font', {}) if isinstance(theme_section, dict) else {}
    main_font, mono_font = "Inter", "JetBrains Mono"
    if isinstance(font_section, dict):
        main_font = font_section.get('text', main_font)
        mono_font = font_section.get('code', mono_font)

    copyright_text = project_section.get('copyright') or config.get('copyright') or "Copyright 2026"
    site_name_text = project_section.get('site_name') or config.get('site_name') or ""

    # Only still needed for admonition icons (see admonition_icon_svg()) -
    # everything else that used to need the icon registry (inline icon
    # shortcodes, emoji) now arrives pre-embedded as real inline <svg> markup
    # straight from render(), with no lookup required.
    icon_dirs = discover_icon_dirs(config)
    icon_registry = build_icon_registry(icon_dirs)

    temp_build_dir = "pdf_build_workspace"
    os.makedirs(temp_build_dir, exist_ok=True)

    mermaid_state = {'count': 0}

    print("🧹 Rendering pages via Zensical...")
    processed_paths = []
    for path in valid_paths:
        safe_name = path.replace('/', '_').replace('\\', '_') + '.html'
        temp_out_path = os.path.join(temp_build_dir, safe_name)
        is_index = "index.md" in os.path.basename(path).lower()
        html = render_page_html(path, config, page_anchor_map, temp_build_dir, mermaid_state, is_index=is_index, repo_url=calculated_vars.get('repo_url', ''), icon_registry=icon_registry)
        with open(temp_out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        processed_paths.append(temp_out_path)

    # Fill in the cover page's {WORDCOUNT}/{REPOURL} markers (see index.md),
    # if present. Each is left untouched if its marker line was deleted.
    if "index.md" in os.path.basename(valid_paths[0]).lower() and len(processed_paths) > 1:
        cover_path = processed_paths[0]
        with open(cover_path, 'r', encoding='utf-8') as f:
            cover_content = f.read()
        if '{WORDCOUNT}' in cover_content:
            # Word count of the actual content pages: everything except the
            # cover page itself, and any page opted out via
            # exclude_from_word_count (see page_excluded_from_word_count()) -
            # e.g. References, Acronyms, Glossary, Originality & AI Use.
            # Checked against valid_paths (the original source, front matter
            # intact) since processed_paths has already had it stripped.
            counted_paths = [
                processed_paths[i] for i in range(1, len(processed_paths))
                if not page_excluded_from_word_count(valid_paths[i])
            ]
            word_count = compute_pdf_word_count(counted_paths)
            cover_content = cover_content.replace('{WORDCOUNT}', f'{word_count:,}')
        if '{REPOURL}' in cover_content:
            # Computed once by macros.py (shared with the website's
            # {{ repo_url }} variable) and picked up here via calculated_vars.
            cover_content = cover_content.replace('{REPOURL}', calculated_vars.get('repo_url', ''))
        if '{RELEASE}' in cover_content:
            # See get_latest_release_tag() - unlike {WORDCOUNT}/{REPOURL},
            # which are always locally computable, most forks of this
            # template will never have a published release, so an empty
            # result drops the whole line rather than leaving a bare
            # "Release: " label behind.
            release_tag = get_latest_release_tag(calculated_vars.get('repo_url', ''))
            if release_tag:
                cover_content = cover_content.replace('{RELEASE}', release_tag)
            else:
                cover_content = re.sub(r'^.*\{RELEASE\}.*\n?', '', cover_content, flags=re.MULTILINE)
        if '{{ site_name }}' in cover_content:
            # Pandoc/build_pdf_final.py never evaluates Jinja, so the exact
            # same literal "{{ site_name }}" text used for the website's
            # macro variable can just be substituted directly here too - one
            # line in index.md works for both outputs, no separate marker.
            cover_content = cover_content.replace('{{ site_name }}', site_name_text)
        with open(cover_path, 'w', encoding='utf-8') as f:
            f.write(cover_content)

    toc_trigger_path = os.path.join(temp_build_dir, "toc_trigger_temp.html")
    with open(toc_trigger_path, "w", encoding="utf-8") as f:
        f.write('\n<h1 class="unnumbered unlisted">Table of Contents</h1>\n\n<div class="page-break"></div>\n')

    compiled_paths = [processed_paths[0], toc_trigger_path] + processed_paths[1:] if "index.md" in os.path.basename(valid_paths[0]).lower() else [toc_trigger_path] + processed_paths

    output_pdf = "docs/site_documentation.pdf"

    temp_master_md = os.path.join(temp_build_dir, "_temp_master_compiled.html")
    with open(temp_master_md, "w", encoding="utf-8") as out_f:
        out_f.write('<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>\n')
        for chunk_path in compiled_paths:
            with open(chunk_path, "r", encoding="utf-8") as in_f:
                out_f.write(in_f.read() + "\n\n")
        out_f.write('</body></html>')

    math_dir = os.path.abspath(os.path.join(temp_build_dir, "math_diagrams"))
    os.makedirs(math_dir, exist_ok=True)
    tex2svg_script = os.path.abspath(os.path.join("tools", "mathjax", "tex2svg.js"))
    mathjax_available = os.path.exists(os.path.join("tools", "mathjax", "node_modules", "mathjax-full"))

    lua_filter_path = os.path.join(temp_build_dir, "tabbox_filter.lua")
    with open(lua_filter_path, "w", encoding="utf-8") as f:
        f.write(
            "local h1, h2, h3 = 0, 0, 0\n"
            "local appendix_index = 0\n"
            "local in_appendix = false\n"
            f"local heading_numbering_enabled = {'true' if heading_numbering_enabled else 'false'}\n\n"
            "-- Converts 1, 2, 3... to A, B, C... for appendix numbering (see\n"
            "-- page_is_appendix() / issue #24). Single letters only - unlike CSS's\n"
            "-- own upper-alpha counter style, Lua has no built-in equivalent, and an\n"
            "-- academic report is never realistically going to have more than 26\n"
            "-- appendixes.\n"
            "local function to_letter(n)\n"
            "  return string.char(64 + n)\n"
            "end\n\n"
            f"local mathjax_available = {'true' if mathjax_available else 'false'}\n"
            f"local math_dir = \"{math_dir}\"\n"
            f"local tex2svg_script = \"{tex2svg_script}\"\n"
            "local math_counter = 0\n\n"
            "function Div(el)\n"
            "  if el.classes:includes('tabbox') then\n"
            "    local title = el.attributes['title'] or 'Tab'\n"
            "    local header = pandoc.Div({pandoc.Plain({pandoc.Str(title)})}, {class='tabbox-header'})\n"
            "    local body = pandoc.Div(el.content, {class='tabbox-body'})\n"
            "    el.content = {header, body}\n"
            "    el.classes = {'tabbox-container'}\n"
            "    return el\n"
            "  end\n"
            "  -- Reconstructs pymdownx.blocks.tab's HTML structure (see\n"
            "  -- zendoc-template#92, render_page_html()) into the same\n"
            "  -- tabbox-header/tabbox-body/tabbox-container shape as the\n"
            "  -- .tabbox handler just above, so both pipelines share one CSS\n"
            "  -- convention. A tabbed-set groups every tab's label\n"
            "  -- (tabbed-labels, one block per label - render_page_html()\n"
            "  -- rewrote each <label> into its own <p> before Pandoc's HTML\n"
            "  -- reader could merge them into one unseparated run of text)\n"
            "  -- and content (tabbed-content, one tabbed-block Div per tab)\n"
            "  -- together, unlike the .tabbox case above (already split into\n"
            "  -- one Div per tab before Pandoc ever sees it) - walk both\n"
            "  -- pairwise and emit one tabbox-container per tab.\n"
            "  if el.classes:includes('tabbed-set') then\n"
            "    local labels_div, content_div\n"
            "    for _, child in ipairs(el.content) do\n"
            "      if child.t == 'Div' and child.classes:includes('tabbed-labels') then\n"
            "        labels_div = child\n"
            "      elseif child.t == 'Div' and child.classes:includes('tabbed-content') then\n"
            "        content_div = child\n"
            "      end\n"
            "    end\n"
            "    if not labels_div or not content_div then return el end\n"
            "    local tabs = {}\n"
            "    for i, label_block in ipairs(labels_div.content) do\n"
            "      local body_block = content_div.content[i]\n"
            "      if body_block then\n"
            "        local header = pandoc.Div({pandoc.Plain(label_block.content)}, {class='tabbox-header'})\n"
            "        local body = pandoc.Div(body_block.content, {class='tabbox-body'})\n"
            "        table.insert(tabs, pandoc.Div({header, body}, {class='tabbox-container'}))\n"
            "      end\n"
            "    end\n"
            "    return tabs\n"
            "  end\n"
            "  -- Prepend-position figure-caption/table-caption (see\n"
            "  -- render_page_html(), zendoc-template#93): pymdownx.blocks.caption's\n"
            "  -- own HTML places a prepended figcaption physically first in the\n"
            "  -- DOM, but Pandoc's Figure AST node stores Caption and content as\n"
            "  -- two separate fields regardless of original order, and Pandoc's\n"
            "  -- own HTML writer always re-emits the caption *after* the content\n"
            "  -- when serializing Figure back to HTML - discarding the \"prepend\"\n"
            "  -- positioning entirely (confirmed directly, isolated test).\n"
            "  -- render_page_html() works around this by retagging any prepend-\n"
            "  -- position figure/table caption to a <div> before Pandoc parses it\n"
            "  -- (a Div's children ARE emitted in original document order),\n"
            "  -- leaving the caption as this Div's first child block - same\n"
            "  -- \"Figure \"/\"Table \" + chapter-prefix numbering as the Figure()\n"
            "  -- handler below, applied to el.content[1] instead of\n"
            "  -- el.caption.long[1].\n"
            "  if el.classes:includes('zendoc-figure-caption') or el.classes:includes('zendoc-table-caption') then\n"
            "    local word = el.classes:includes('zendoc-figure-caption') and 'Figure ' or 'Table '\n"
            "    local label = in_appendix and to_letter(appendix_index) or tostring(h1)\n"
            "    local block = el.content[1]\n"
            "    if block and (block.t == 'Para' or block.t == 'Plain') then\n"
            "      for i, inline in ipairs(block.content) do\n"
            "        if inline.t == 'Span' and inline.classes:includes('caption-prefix') then\n"
            "          table.insert(inline.content, 1, pandoc.Str(label .. '.'))\n"
            "          table.insert(block.content, i, pandoc.Str(word))\n"
            "          break\n"
            "        end\n"
            "      end\n"
            "    end\n"
            "    return el\n"
            "  end\n"
            "  -- pymdownx.arithmatex's generic-mode display math\n"
            "  -- (<div class=\"arithmatex\">\\[...\\]</div> - see\n"
            "  -- zendoc-template#92): Pandoc's HTML reader has no native Math\n"
            "  -- AST node for this the way its *markdown* reader does for\n"
            "  -- $$...$$, so this can't be handled by the Math() function\n"
            "  -- below at all - matched by class instead, stripping the\n"
            "  -- \\[ \\] delimiters before the same tex2svg render Math() uses.\n"
            "  if el.classes:includes('arithmatex') then\n"
            "    if not mathjax_available then return nil end\n"
            "    local text = pandoc.utils.stringify(el.content):gsub('^%s*\\\\%[%s*', ''):gsub('%s*\\\\%]%s*$', '')\n"
            "    math_counter = math_counter + 1\n"
            "    local ok, svg = pcall(pandoc.pipe, 'node', {tex2svg_script, 'display'}, text)\n"
            "    if not ok or not svg or svg == '' then return nil end\n"
            "    local svg_path = math_dir .. '/formula_' .. math_counter .. '.svg'\n"
            "    local out = io.open(svg_path, 'w')\n"
            "    if not out then return nil end\n"
            "    out:write(svg)\n"
            "    out:close()\n"
            "    return pandoc.Para({pandoc.RawInline('html', '<img class=\"pdf-math-display\" src=\"' .. svg_path .. '\" />')})\n"
            "  end\n"
            "end\n\n"
            "-- pymdownx.arithmatex's generic-mode inline math\n"
            "-- (<span class=\"arithmatex\">\\(...\\)</span>) - same reasoning as\n"
            "-- the Div() arithmatex handler above, for the inline case.\n"
            "function Span(el)\n"
            "  if el.classes:includes('arithmatex') then\n"
            "    if not mathjax_available then return nil end\n"
            "    local text = pandoc.utils.stringify(el.content):gsub('^%s*\\\\%(%s*', ''):gsub('%s*\\\\%)%s*$', '')\n"
            "    math_counter = math_counter + 1\n"
            "    local ok, svg = pcall(pandoc.pipe, 'node', {tex2svg_script, 'inline'}, text)\n"
            "    if not ok or not svg or svg == '' then return nil end\n"
            "    local svg_path = math_dir .. '/formula_' .. math_counter .. '.svg'\n"
            "    local out = io.open(svg_path, 'w')\n"
            "    if not out then return nil end\n"
            "    out:write(svg)\n"
            "    out:close()\n"
            "    return pandoc.RawInline('html', '<img class=\"pdf-math-inline\" src=\"' .. svg_path .. '\" />')\n"
            "  end\n"
            "end\n\n"
            "-- Prepends the current chapter number/appendix letter in front\n"
            "-- of pymdownx.blocks.caption's own bare per-page auto-number\n"
            "-- (e.g. \"1.\" -> \"7.1.\"), plus the \"Figure \"/\"Table \" word\n"
            "-- itself (added via CSS ::before on the website - see\n"
            "-- zendoc-template#92 - which has no equivalent for a PDF, where\n"
            "-- the number needs to be real text) - matching\n"
            "-- zensical.toml's zendoc-figure-caption/zendoc-table-caption\n"
            "-- classes (see [project.markdown_extensions.pymdownx.blocks.caption]).\n"
            "function Figure(el)\n"
            "  local word = nil\n"
            "  if el.classes:includes('zendoc-figure-caption') then word = 'Figure '\n"
            "  elseif el.classes:includes('zendoc-table-caption') then word = 'Table ' end\n"
            "  if not word then return el end\n"
            "  local label = in_appendix and to_letter(appendix_index) or tostring(h1)\n"
            "  for _, block in ipairs(el.caption.long) do\n"
            "    if block.t == 'Para' or block.t == 'Plain' then\n"
            "      for i, inline in ipairs(block.content) do\n"
            "        if inline.t == 'Span' and inline.classes:includes('caption-prefix') then\n"
            "          table.insert(inline.content, 1, pandoc.Str(label .. '.'))\n"
            "          table.insert(block.content, i, pandoc.Str(word))\n"
            "          return el\n"
            "        end\n"
            "      end\n"
            "      return el\n"
            "    end\n"
            "  end\n"
            "  return el\n"
            "end\n\n"
            "function Header(block)\n"
            "  if heading_numbering_enabled and not block.classes:includes('unnumbered') then\n"
            "    if block.level == 1 then\n"
            "      h2 = 0\n"
            "      h3 = 0\n"
            "      if block.classes:includes('appendix') then\n"
            "        appendix_index = appendix_index + 1\n"
            "        in_appendix = true\n"
            "        table.insert(block.content, 1, pandoc.Str('Appendix ' .. to_letter(appendix_index) .. '. '))\n"
            "      else\n"
            "        h1 = h1 + 1\n"
            "        in_appendix = false\n"
            "        table.insert(block.content, 1, pandoc.Str(tostring(h1) .. '. '))\n"
            "      end\n"
            "    elseif block.level == 2 then\n"
            "      h2 = h2 + 1\n"
            "      h3 = 0\n"
            "      if in_appendix then\n"
            "        table.insert(block.content, 1, pandoc.Str(to_letter(appendix_index) .. '.' .. tostring(h2) .. ' '))\n"
            "      else\n"
            "        table.insert(block.content, 1, pandoc.Str(tostring(h1) .. '.' .. tostring(h2) .. ' '))\n"
            "      end\n"
            "    elseif block.level == 3 then\n"
            "      h3 = h3 + 1\n"
            "      if in_appendix then\n"
            "        table.insert(block.content, 1, pandoc.Str(to_letter(appendix_index) .. '.' .. tostring(h2) .. '.' .. tostring(h3) .. ' '))\n"
            "      else\n"
            "        table.insert(block.content, 1, pandoc.Str(tostring(h1) .. '.' .. tostring(h2) .. '.' .. tostring(h3) .. ' '))\n"
            "      end\n"
            "    end\n"
            "  end\n"
            "  return block\n"
            "end\n\n"
            "function Math(el)\n"
            "  if not mathjax_available then return nil end\n"
            "  math_counter = math_counter + 1\n"
            "  local is_display = (el.mathtype == 'DisplayMath')\n"
            "  local ok, svg = pcall(pandoc.pipe, 'node', {tex2svg_script, is_display and 'display' or 'inline'}, el.text)\n"
            "  if not ok or not svg or svg == '' then return nil end\n"
            "  local svg_path = math_dir .. '/formula_' .. math_counter .. '.svg'\n"
            "  local out = io.open(svg_path, 'w')\n"
            "  if not out then return nil end\n"
            "  out:write(svg)\n"
            "  out:close()\n"
            "  local css_class = is_display and 'pdf-math-display' or 'pdf-math-inline'\n"
            "  return pandoc.RawInline('html', '<img class=\"' .. css_class .. '\" src=\"' .. svg_path .. '\" />')\n"
            "end\n\n"
            "function Pandoc(doc)\n"
            "  local toc_list = pandoc.structure.table_of_contents(doc)\n"
            "  local final_blocks = {}\n"
            "  for _, block in ipairs(doc.blocks) do\n"
            "    table.insert(final_blocks, block)\n"
            "    if block.t == 'Header' and block.level == 1 and pandoc.utils.stringify(block.content) == 'Table of Contents' then\n"
            "      table.insert(final_blocks, pandoc.Div(toc_list, {id='TOC', class='toc'}))\n"
            "    end\n"
            "  end\n"
            "  doc.blocks = final_blocks\n"
            "  return doc\n"
            "end\n"
        )
    
    # Rewrites CSS url(...) references (relative to the source CSS file) to base64 data
    # URIs, since the compiled CSS is written to a different directory (temp_build_dir)
    # where the original relative paths would no longer resolve.
    def inline_css_urls(css_text, css_dir):
        def url_replacer(match):
            quote, ref = match.group(1), match.group(2)
            if ref.startswith(('data:', 'http://', 'https://', '#')):
                return match.group(0)
            asset_path = os.path.abspath(os.path.join(css_dir, ref))
            if not os.path.isfile(asset_path):
                return match.group(0)
            ext = os.path.splitext(asset_path)[1].lower().strip('.')
            mime_type = {"svg": "image/svg+xml", "jpg": "image/jpeg"}.get(ext, f"image/{ext}")
            with open(asset_path, 'rb') as f:
                b64_payload = base64.b64encode(f.read()).decode('utf-8')
            return f'url({quote}data:{mime_type};base64,{b64_payload}{quote})'
        return re.sub(r'url\((["\']?)([^)"\']+)\1\)', url_replacer, css_text)

    temp_compiled_css = os.path.join(temp_build_dir, "_temp_compiled_print.css")
    original_css_content = ""
    for css_src in [os.path.join(docs_dir, "stylesheets", "extra.css"), os.path.join(docs_dir, "stylesheets", "print.css")]:
        if os.path.exists(css_src):
            with open(css_src, "r", encoding="utf-8") as f:
                original_css_content += inline_css_urls(f.read(), os.path.dirname(css_src)) + "\n"

    cleaned_original_css = re.sub(r'@charset[^;{]*(\{.*?\}|;)', '', original_css_content, flags=re.IGNORECASE | re.DOTALL)
    cleaned_original_css = re.sub(r'^.*user-select.*$\n?', '', cleaned_original_css, flags=re.MULTILINE | re.IGNORECASE)

    def css_escape_content_string(text):
        clean_text = text.strip().replace('\n', ' ').replace('\r', ' ')
        sanitized_text = clean_text.replace('&copy;', '©').replace('&#169;', '©')
        css_escaped_text = "".join(f"\\{ord(char):04X} " if ord(char) > 127 else char for char in sanitized_text)
        return css_escaped_text.replace('"', '\\"')

    safe_copyright = css_escape_content_string(copyright_text)
    safe_site_name = css_escape_content_string(site_name_text)

    css_blueprint = """
/* ==========================================================================
   DYNAMIC TYPOGRAPHY CONFIGURATION (Injected from settings)
   ========================================================================== */
body {
    font-family: "__MAIN_FONT__", sans-serif !important;
}
h1, h2, h3, h4, h5, h6 {
    font-family: "__MAIN_FONT__", sans-serif !important;
}
pre, code {
    font-family: "__MONO_FONT__", monospace !important;
}

/* ==========================================================================
   CRITICAL WEASYPRINT STRUCTURAL CANVAS RESET 
   ========================================================================== */
html, body, main, div, article, section, .md-container, .md-main, .md-content {
    display: block !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
    overflow: visible !important;
    position: static !important;
    float: none !important;
    background: transparent !important;
}
header, nav, footer, .md-sidebar, .md-header, .md-footer, .md-search, #search {
    display: none !important;
}

/* ==========================================================================
   A4 PAGE LAYOUT & UNIFIED HEADER/FOOTER CONFIGURATION
   ========================================================================== */
@page {
    size: __PDF_PAGE_SIZE__;
    margin: __PDF_MARGIN_TOP__ __PDF_MARGIN_RIGHT__ __PDF_MARGIN_BOTTOM__ __PDF_MARGIN_LEFT__ !important;
    @top-center { content: none !important; }
    @top-left {
        content: "__SITE_NAME__" !important;
        font-family: "__MAIN_FONT__", sans-serif !important;
        font-size: __PDF_HEADER_FOOTER_FONT_SIZE__ !important;
        color: __PDF_HEADER_FOOTER_COLOR__ !important;
        vertical-align: bottom !important;
        border-bottom: 1px solid __PDF_HEADER_FOOTER_DIVIDER_COLOR__ !important;
        padding-bottom: 8px !important;
        /* Margin (not padding) below the border: pushes the box's bottom
           edge away from the content boundary, so content that lands
           flush against a page break (e.g. a table/tabbox continuation
           fragment) never touches the header divider line. */
        margin-bottom: 3mm !important;
        width: 50% !important;
        text-align: left !important;
    }
    /* Current chapter title, set via string-set on h1 below - stays empty
       until the first numbered h1 (i.e. through the cover and Table of
       Contents pages), then holds that chapter's title for every page until
       the next h1. Shares the header width evenly with @top-left (rather
       than being squeezed into whatever's left of an unconstrained box),
       so longer chapter titles don't wrap onto a second line; its own
       matching border-bottom lines up with @top-left's to form one
       continuous divider. */
    @top-right {
        content: string(chapter-title) !important;
        font-family: "__MAIN_FONT__", sans-serif !important;
        font-size: __PDF_HEADER_FOOTER_FONT_SIZE__ !important;
        color: __PDF_HEADER_FOOTER_COLOR__ !important;
        vertical-align: bottom !important;
        border-bottom: 1px solid __PDF_HEADER_FOOTER_DIVIDER_COLOR__ !important;
        padding-bottom: 8px !important;
        margin-bottom: 3mm !important;
        width: 50% !important;
        text-align: right !important;
    }
    @bottom-center { content: none !important; }
    @bottom-left {
        content: "__COPYRIGHT__" !important;
        font-family: "__MAIN_FONT__", sans-serif !important;
        font-size: __PDF_HEADER_FOOTER_FONT_SIZE__ !important;
        color: __PDF_HEADER_FOOTER_COLOR__ !important;
        vertical-align: top !important;
        border-top: 1px solid __PDF_HEADER_FOOTER_DIVIDER_COLOR__ !important;
        padding-top: 8px !important;
        margin-top: 3mm !important;
        width: 80% !important;
        text-align: left !important;
    }
    /* 20% (not the previous 15%) so "Page X of Y" has room to stay on one
       line once the page count reaches 3 digits - at 15% wide, e.g. "Page
       98 of 999" already wrapped onto two lines (digit glyph widths vary,
       so this isn't a clean "3 digits" cutoff - some 2-digit page numbers
       hit it too). Verified up to a 999-page document at this width. */
    @bottom-right {
        content: "Page " counter(page) " of " counter(pages) !important;
        font-family: "__MAIN_FONT__", sans-serif !important;
        font-size: __PDF_HEADER_FOOTER_FONT_SIZE__ !important;
        color: __PDF_HEADER_FOOTER_COLOR__ !important;
        vertical-align: top !important;
        border-top: 1px solid __PDF_HEADER_FOOTER_DIVIDER_COLOR__ !important;
        padding-top: 8px !important;
        margin-top: 3mm !important;
        width: 20% !important;
        text-align: right !important;
    }
}
@page :first {
    @top-left { content: none !important; border-bottom: none !important; }
    @top-right { content: none !important; }
    @bottom-left { content: none !important; border-top: none !important; }
    @bottom-right { content: none !important; border-top: none !important; }
}

.page-break, .cover-page {
    page-break-after: always;
    break-after: always;
}
h1 { break-before: page !important; }
.cover-page h1 { break-before: auto !important; }
/* print.css's own "h1..h6 { page-break-after: avoid }" keeps a heading from
   being the last thing on a page - reasonable for h1/h2 (a chapter/section
   title followed by a short intro), but confirmed directly (isolated A/B
   rebuild) to backfire for h3-h6 whenever the heading's own following
   content is large (its own intro paragraph, an "Install X" sub-heading,
   then a whole grid-card of per-OS tabs): WeasyPrint couldn't satisfy
   "heading can't be alone at the bottom of the page" without pulling in
   far more content than intended, so it pushed the *entire* heading (with
   nothing before it moved) onto a fresh page instead - even with hundreds
   of points of genuinely blank space left on the previous page (e.g.
   "12.3 Installing a GUI Git client" / "12.3.1 Installing GitHub Desktop"
   /"12.3.2 Installing GitKraken", "7.2.2 Generate and configure ssh keys
   for Git"). h1/h2 keep the "avoid" behaviour (via print.css); h3-h6
   override back to "auto" here. */
h3, h4, h5, h6 { page-break-after: auto !important; break-after: auto !important; }
/* A plain <p> had no break-inside/orphans/widows protection at all.
   Making every <p> unsplittable (page-break-inside: avoid) over-corrected:
   a short paragraph immediately after a heading became atomic with that
   heading too (since the heading's own "stay with next" requirement, from
   h1/h2's avoid-after or a title's own avoid-after elsewhere, needs the
   *whole* next block to fit when that block can't split), and if the
   combined size didn't fit the remaining page, the whole pair got pushed
   to a fresh page - a blank-gap regression, confirmed directly for "8.2
   Synchronise your updates" (startediting.md). orphans/widows alone (no
   avoid) fixes that, but only if the threshold is low enough to actually
   allow a split: orphans: 3 / widows: 3 (6 combined) is taller than many
   real intro paragraphs here - "7.2.2 Generate and configure ssh keys for
   Git"'s own paragraph (installtooling.md) is only 2 lines, so no split
   was legal at all, and the whole paragraph moved away from its heading,
   orphaning it alone at the bottom of the previous page. orphans: 1 /
   widows: 2 (3 combined) is short enough to let even a 2-3 line paragraph
   split if it must, while still avoiding an ugly single-line widow for
   longer ones. */
p {
    orphans: 1;
    widows: 2;
}
/* Feeds @top-right above: skips the Table of Contents' own "Table of
   Contents" h1 (and the hidden cover-page h1) via .unnumbered, the same
   class the numbering Lua filter already uses to identify non-chapter
   headings, so the running title only starts once real content begins. */
h1:not(.unnumbered) { string-set: chapter-title content() !important; }

/* ==========================================================================
   TABLE LAYOUT STYLING MATRIX
   ========================================================================== */
table {
    border-collapse: collapse !important;
    border: 0.25pt solid #555555 !important;
    width: 100% !important;
    margin: 1.2em 0 !important;
    page-break-inside: auto !important;
    break-inside: auto !important;
}
/* Rows never split mid-row - a page break only ever falls between rows */
table tr {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
}
/* Repeats the header row on every page the table spans across */
thead {
    display: table-header-group;
}
/* pymdownx.blocks.caption always wraps its caption text in a <p> - inside
   a native <figcaption> for the default append-position case (still a
   <figure> - see the "figure {}"/"figure.zendoc-table-caption" rules
   below), or as the first child <p> once prepend-position unwraps the
   <figcaption> into a <div> (see render_page_html(), zendoc-template#93).
   This used to be "table caption {}", which only ever matches a literal
   <table><caption> - something pymdownx.blocks.caption never produces -
   dead code left over from the old regex pipeline's own hand-built
   markup; confirmed captions were rendering unitalicised because of it. */
figcaption p,
div.zendoc-table-caption > p:first-child,
div.zendoc-figure-caption > p:first-child {
    text-align: center !important;
    font-style: italic !important;
    margin-bottom: 8px !important;
    page-break-after: avoid !important;
    break-after: avoid-page !important;
}
table th { background-color: rgba(0, 0, 0, 0.1) !important; font-weight: bold !important; text-align: center !important; }
/* text-align/font-size set explicitly here, not left to inherit - a
   table-caption's own wrapping div (div.zendoc-table-caption above, or
   the pre-existing "figure {}" rule for an append-position table caption)
   sets text-align: center to keep its caption text centered, which every
   cell's content otherwise silently inherits too (confirmed directly:
   table body text was rendering center-aligned with no explicit rule
   anywhere overriding it). font-size is reduced from the inherited body
   size, matching how a dense grid of short cells reads better smaller -
   same reasoning as .tabbox-header/.admonition-title's own explicit
   smaller sizes above. */
table th, table td {
    padding: 8px 12px !important;
    border-top: 0.25pt solid #555555 !important;
    border-bottom: 0.25pt solid #555555 !important;
    border-left: none !important; border-right: none !important;
    font-size: 10pt !important;
}
table td { text-align: left !important; }
table tr:first-child th, table tr:first-child td { border-top: none !important; }
table tr:last-child td { border-bottom: none !important; }

/* ==========================================================================
   ADMONITIONS & TABS LAYOUT OVERRIDES
   ========================================================================== */
blockquote {
    background-color: #f8fafc !important; border-left: 4px solid #cbd5e1 !important;
    padding: 12px 16px !important; margin: 1em 0 !important;
}
/* Renders footnotes at the bottom of the page they're referenced on (like a
   printed book). Zensical's own markdown pipeline renders a footnote as a
   <sup id="fnref:N"> at the reference point plus a <div class="footnote">
   collecting every footnote's own text at the *end* of the page - never a
   Pandoc-native Note element (that only exists when Pandoc's own markdown
   reader parses "[^1]" syntax directly, not when it's handed pre-rendered
   HTML). render_page_html() moves each footnote's text inline into a
   <span class="pdf-footnote"> at its own reference point instead, so
   float: footnote can anchor it to the correct page - confirmed directly
   that without this, the footnote's div rendered wherever it fell in
   normal document flow, often several pages after its own reference. */
.pdf-footnote {
    float: footnote !important;
    font-size: 9pt !important;
    /* KNOWN LIMITATION: WeasyPrint 69's float: footnote renders the
       footnote-area text in a fixed, narrow column (confirmed directly -
       neither an explicit percentage nor absolute-point width override
       changes it), instead of the page's full content width, so a
       footnote often wraps to 2-3 short lines rather than one. Correct
       page and font-size are unaffected. Tracked upstream rather than
       worked around here, since no CSS-side override changes it. */
}
/* extra.css hides .pdf-only (the cover page's word-count/repo-link markers)
   on the live website; override that back to visible here, since they're
   meant to show only in the PDF once build_pdf_final.py has filled in the
   real values. */
.pdf-only {
    display: block !important;
    margin-bottom: 0 !important;
}
/* Collapses the gap between consecutive .pdf-only lines (e.g. word count
   directly above the repo link) without affecting the normal paragraph
   spacing above the first one. Both margin-bottom above and margin-top here
   need zeroing - CSS margin collapsing takes the max of the two, so zeroing
   only one side still leaves the other's margin as the visible gap. */
.pdf-only + .pdf-only {
    margin-top: 0 !important;
}
/* Renders TeX math ($...$/$$...$$, see https://zensical.org/docs/authoring/math/)
   as pre-rendered SVGs, since WeasyPrint has no JS engine to run MathJax
   client-side like the live Zensical site does. The Lua filter's Math()
   function replaces each formula with one of these images at build time. */
.pdf-math-display {
    display: block !important;
    margin: 1em auto !important;
    text-align: center !important;
    page-break-inside: avoid !important;
    break-inside: avoid !important;
}
.pdf-math-inline {
    display: inline !important;
    height: 1em !important;
    width: auto !important;
    vertical-align: middle !important;
}
@page {
    @footnote {
        border-top: 0.5pt solid #cbd5e1;
        padding-top: 6px;
        margin-top: 8px;
    }
}
.tabbox-container {
    border: 1px solid #cbd5e1; border-radius: 4px; margin: 1em 0;
    page-break-inside: auto !important; break-inside: auto !important;
    -webkit-box-decoration-break: clone !important; box-decoration-break: clone !important;
}
.tabbox-header {
    background-color: #e5e5e5 !important; color: #000000 !important;
    font-weight: bold; padding: 8px 12px; font-size: 10pt;
    page-break-after: avoid !important; break-after: avoid !important;
}
.tabbox-body {
    background-color: #f2f2f2 !important; padding: 12px;
    page-break-inside: auto !important; break-inside: auto !important;
    -webkit-box-decoration-break: clone !important; box-decoration-break: clone !important;
}
.admonition {
    border-left: 4px solid #448aff !important; background-color: #f8fafc !important;
    padding: 14px 18px !important; margin: 1.2em 0 !important;
    page-break-inside: auto !important; break-inside: auto !important;
    -webkit-box-decoration-break: clone !important; box-decoration-break: clone !important;
}
.admonition-title {
    font-weight: bold !important; margin-bottom: 8px !important; font-size: 10.5pt !important;
    color: #000000 !important;
    /* auto, not avoid: same WeasyPrint quirk as h3-h6's own page-break-after
       (see the h3,h4,h5,h6 rule above) - confirmed directly against the
       built PDF ("The Four Space Rule" admonition, zensicalbasics.md): even
       though .admonition itself already uses page-break-inside: auto, the
       title's own avoid-after still forced the *entire* admonition onto a
       fresh page rather than letting it start on the current one, leaving
       a large blank gap behind - despite the admonition's own body being
       only 2-3 short lines, easily small enough to have fit. */
}

.admonition.note     { border-left-color: #448aff !important; background-color: rgba(68, 138, 255, 0.05) !important; }
.admonition.abstract { border-left-color: #00b0ff !important; background-color: rgba(0, 176, 255, 0.05) !important; }
.admonition.info     { border-left-color: #00b8d4 !important; background-color: rgba(0, 184, 212, 0.05) !important; }
.admonition.tip      { border-left-color: #00bfa5 !important; background-color: rgba(0, 191, 165, 0.05) !important; }
.admonition.success  { border-left-color: #00c853 !important; background-color: rgba(0, 200, 83, 0.05) !important; }
.admonition.question { border-left-color: #64dd17 !important; background-color: rgba(100, 221, 23, 0.05) !important; }
.admonition.warning  { border-left-color: #ff9100 !important; background-color: rgba(255, 145, 0, 0.05) !important; }
.admonition.failure  { border-left-color: #ff5252 !important; background-color: rgba(255, 82, 82, 0.05) !important; }
.admonition.danger   { border-left-color: #ff1744 !important; background-color: rgba(255, 23, 68, 0.05) !important; }
.admonition.bug      { border-left-color: #ec407a !important; background-color: rgba(236, 64, 122, 0.05) !important; }
.admonition.example  { border-left-color: #651fff !important; background-color: rgba(101, 31, 255, 0.05) !important; }
.admonition.quote    { border-left-color: #9e9e9e !important; background-color: rgba(158, 158, 158, 0.05) !important; }

/* ==========================================================================
   ZENSICAL GRID CARD CANVAS ARCHITECTURE
   ========================================================================== */
.gridcard-matrix { display: block !important; margin: 1.5em 0 !important; }
.gridcard-item {
    background-color: #f4f8ff !important; border: none !important;
    padding: 16px !important; margin-bottom: 1em !important; border-radius: 4px !important;
    page-break-inside: avoid; break-inside: avoid;
}
.gridcard-title {
    font-weight: bold !important; font-size: 13pt !important; margin-bottom: 12px !important;
    display: block !important; color: #111111 !important; page-break-after: avoid !important; break-after: avoid !important;
}
.gridcard-title p { font-weight: bold !important; font-size: 13pt !important; color: #111111 !important; margin: 0 !important; display: inline !important; }
/* Zensical's own native grid-card HTML (<div class="grid cards" markdown>
   wrapping a bullet list - see "Grid cards" in zensicalbasics.md) is a
   plain <div class="grid cards ..."><ul><li>...</li></ul></div>, not the
   .gridcard-matrix/-item/-title structure above (that was hand-built by
   the old regex pipeline's own ::: {.gridcard-matrix} fenced-div
   convention, retired in zendoc-template#92 along with everything else
   that only existed to translate Zensical/pymdownx markdown syntax Pandoc
   itself doesn't understand - card layout has no such translation problem,
   Pandoc reads the real <div>/<ul>/<li> as-is). Same visual treatment as
   .gridcard-item/-title above, targeting the real structure directly: each
   <li> is a card, and the card's leading paragraph (its "__bold title__")
   is styled as the title.
   WeasyPrint's CSS Grid support is too limited to trust for an actual
   side-by-side multi-column layout, so every card - one-column or not -
   renders as one full-width box per row, stacked. */
div.grid.cards > ul {
    list-style: none !important; margin: 1.5em 0 !important; padding: 0 !important;
}
div.grid.cards > ul > li {
    background-color: #f4f8ff !important; border: none !important;
    padding: 16px !important; margin-bottom: 1em !important; border-radius: 4px !important;
    /* auto, not avoid: unlike the old .gridcard-item convention this
       replaces, a real Zensical grid card commonly wraps a whole tabbed-set
       (e.g. installtooling.md's per-OS install instructions, all three OS
       tabs stacked since WeasyPrint can't do interactive tabs) - often
       taller than a full page. "avoid" forced the entire oversized card
       onto a fresh page as one atomic unit (unable to actually fit there
       either), leaving a large blank gap on the previous page - confirmed
       directly against the built PDF. Same "auto" convention already used
       for .tabbox-container/.admonition below, for the same reason. */
    page-break-inside: auto !important; break-inside: auto !important; list-style: none !important;
}
div.grid.cards > ul > li > p:first-child {
    font-weight: bold !important; font-size: 13pt !important; margin-bottom: 12px !important;
    color: #111111 !important; page-break-after: avoid !important; break-after: avoid !important;
}

/* #dddddd is another 5% darker than #e9e9e9 (itself 5% darker than
   #f5f5f5, --md-code-bg-color - the website's shading for both inline
   code and code blocks; see docs/stylesheets/extra.css / the Zensical
   default theme), kept identical between inline code and code blocks here. */
pre, code { font-family: "__MONO_FONT__", monospace !important; }
/* text-align isn't otherwise set anywhere on pre/code, so a fenced code
   block nested inside a centered ancestor (figure {}, div.zendoc-*-caption,
   .gridcard-title, an admonition/tab that happens to be inside one of
   those, etc.) would silently inherit centered text-align, ragging every
   code line's left edge - same class of inheritance bug as the table
   text-align fix above. Explicit left keeps code blocks left-aligned
   regardless of ancestor context. */
pre { text-align: left !important; }
pre { padding: 10px !important; border-radius: 4px !important; margin: 1em 0 !important; white-space: pre-wrap !important; background-color: #dddddd !important; }
code { padding: 2px 4px !important; border-radius: 3px !important; background-color: #dddddd !important; }
/* Multi-line <code> inside <pre> is a single inline box split across hard line
   breaks; without this, the padding above lands only on the first line (default
   box-decoration-break: slice), making it look indented relative to the rest. */
pre code { padding: 0 !important; }

/* pymdownx.keys (++key+combo++) box styling - reproduces the website's
   light-mode --md-typeset-kbd-* custom properties (main.css), since only
   extra.css/print.css (not the theme's own main/palette CSS) are pulled
   into the PDF stylesheet above, so kbd's own theme rule never reaches
   WeasyPrint otherwise. */
kbd {
    background-color: #fafafa !important;
    border-radius: 3px !important;
    box-shadow: 0 2px 0 1px #b8b8b8, 0 2px 0 #b8b8b8, 0 -2px 3px #ffffff inset !important;
    display: inline-block !important;
    font-size: 0.75em !important;
    padding: 0 0.6em !important;
    vertical-align: text-top !important;
}
.keys span { color: #757575 !important; padding: 0 0.2em !important; }

/* ==========================================================================
   ADVANCED GLOBAL IMAGE AND VECTOR PROTECTION STANDARDS
   ========================================================================== */
img {
    max-width: 100% !important;
}
/* Keeps an image and its /// caption /// figcaption together as one atomic
   unit, so the caption can never be pushed to a page apart from its image.
   text-align: center centers the <img> itself (a naturally inline-level
   element, so its parent's text-align controls its horizontal position) -
   without this, only the figcaption text ends up centered (its own
   centering comes from WeasyPrint's UA stylesheet default for figcaption),
   leaving the image sitting at its default left-aligned position and
   visibly misaligned under its own caption. Applies both to figures
   zensical_caption_replacer() builds by hand and to Pandoc's own implicit
   figures (any standalone image Pandoc auto-wraps in <figure>, e.g. the
   institution logos on the front page). */
figure {
    page-break-inside: avoid !important;
    break-inside: avoid-page !important;
    text-align: center !important;
}
/* A prepend-position figure-caption is retagged from <figure> to <div> in
   render_page_html() (see zendoc-template#93, and the Lua filter's Div()
   handler above) so its caption keeps original document order through
   Pandoc - same page-break/centering treatment as the "figure {}" rule
   above (an image can't be split anyway, so keeping it atomic with its
   caption is safe), which no longer matches once it's a <div>. */
div.zendoc-figure-caption {
    page-break-inside: avoid !important;
    break-inside: avoid-page !important;
    text-align: center !important;
}
/* Unlike a figure-caption, a table-caption's content (the table itself)
   routinely runs longer than one page (see originality.md's AI-use
   table) - inheriting "figure {}"'s page-break-inside: avoid (or copying
   it verbatim to the div case above) forced the whole caption+table onto
   a fresh page as one atomic unit, unable to actually fit there either,
   leaving a large blank gap on the previous page (confirmed directly
   against the built PDF). "auto" here overrides that for both the
   default append-position case (still a native <figure>) and the
   prepend-position case (retagged to a <div> above) - each row is still
   individually protected from splitting by "table tr" below. */
figure.zendoc-table-caption, div.zendoc-table-caption {
    page-break-inside: auto !important;
    break-inside: auto !important;
    text-align: center !important;
}
/* Applied via "{ .screenshot }" on an image (see "Captions" in
   customise.md) - matches the website's equivalent img.screenshot rule
   in extra.css, so a screenshot renders identically framed in both
   outputs. */
img.screenshot {
    border: 1px solid #d0d0d0 !important;
    border-radius: 4px !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15) !important;
}
img.twemoji, i.fa-solid, i.fa-regular, i.fa-brands, i.material-icons, i[class*="fa-"], span[class*="octicon-"], .octicon {
    image-resolution: 96dpi !important;
    font-size: 1.1em !important;
    height: 1.1em !important;
    width: 1.1em !important;
    max-width: none !important;
    max-height: none !important;
    display: inline-block !important;
    vertical-align: -0.2em !important;
    margin: 0 2px !important;
    background: transparent !important;
}
.cover-page img {
    display: block !important;
    margin: 0.5cm auto 0.2cm auto !important;
    max-width: 65% !important;
    max-height: 3.5cm !important;
    object-fit: contain !important;
    image-resolution: 96dpi !important;
}
.text-center img, .text-center-italic img {
    display: inline-block !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* Inline vector mappings */
.twemoji svg {
    width: 1.1em;
    height: 1.1em;
    vertical-align: -0.2em;
}

/* ==========================================================================
   COVER PAGE & GENERAL PRINT ALIGNMENT UTILITY MATRIX
   ========================================================================= */
.cover-page {
    padding-top: 4cm;
}
.title-ctr-1, .title-ctr-2, .title-ctr-3, .title-ctr-4, .title-ctr-5, .title-ctr-6,
.title-ctr-b1, .title-ctr-b2, .title-ctr-b3, .title-ctr-b4, .title-ctr-b5, .title-ctr-b6 { text-align: center; display: block; }
.title-left-1, .title-left-2, .title-left-3, .title-left-4, .title-left-5, .title-left-6,
.title-left-b1, .title-left-b2, .title-left-b3, .title-left-b4, .title-left-b5, .title-left-b6 { text-align: left; display: block; }
.title-ctr-b1, .title-ctr-b2, .title-ctr-b3, .title-ctr-b4, .title-ctr-b5, .title-ctr-b6,
.title-left-b1, .title-left-b2, .title-left-b3, .title-left-b4, .title-left-b5, .title-left-b6 { font-weight: bold; }
[class*="title-"][class*="-1"] { font-size: 26pt; line-height: 32pt; margin-bottom: 0.6em; }
[class*="title-"][class*="-2"] { font-size: 22pt; line-height: 28pt; margin-bottom: 0.6em; }
[class*="title-"][class*="-3"] { font-size: 18pt; line-height: 24pt; margin-bottom: 0.6em; }
[class*="title-"][class*="-4"] { font-size: 15pt; line-height: 20pt; margin-bottom: 0.6em; }
[class*="title-"][class*="-5"] { font-size: 13pt; line-height: 17pt; margin-bottom: 0.6em; }
[class*="title-"][class*="-6"] { font-size: 11pt; line-height: 15pt; margin-bottom: 0.6em; }

.text-center, .text-center-italic { text-align: center !important; }
.text-right, .text-right-italic { text-align: right !important; }
.text-justify, .text-justify-italic { text-align: justify !important; }
.text-center-italic, .text-right-italic, .text-justify-italic { font-style: italic !important; }

.gridcard-matrix, .gridcard-item,
.text-center, .text-right, .text-justify,
.text-center-italic, .text-right-italic, .text-justify-italic {
    page-break-inside: auto !important;
    break-inside: auto !important;
}
.tabbox-header {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
}
"""

    final_css_payload = css_blueprint.replace("__MAIN_FONT__", main_font)\
                                     .replace("__MONO_FONT__", mono_font)\
                                     .replace("__COPYRIGHT__", safe_copyright)\
                                     .replace("__SITE_NAME__", safe_site_name)\
                                     .replace("__PDF_PAGE_SIZE__", pdf_page_size)\
                                     .replace("__PDF_MARGIN_TOP__", pdf_margin_top)\
                                     .replace("__PDF_MARGIN_RIGHT__", pdf_margin_right)\
                                     .replace("__PDF_MARGIN_BOTTOM__", pdf_margin_bottom)\
                                     .replace("__PDF_MARGIN_LEFT__", pdf_margin_left)\
                                     .replace("__PDF_HEADER_FOOTER_FONT_SIZE__", pdf_header_footer_font_size)\
                                     .replace("__PDF_HEADER_FOOTER_COLOR__", pdf_header_footer_color)\
                                     .replace("__PDF_HEADER_FOOTER_DIVIDER_COLOR__", pdf_header_footer_divider_color)

    # PDF equivalent of the website's reference_style() macro (see macros.py):
    # project.extra.reference_style = "global" in zensical.toml switches the
    # References page from the default "european" look (single line spacing
    # throughout, no indent) to single line spacing within each entry but
    # double spacing *between* entries, with a 0.5in/1.27cm hanging indent on
    # wrapped lines. Selectors here deliberately don't use ".md-typeset" -
    # unlike the website, Pandoc's HTML output has no such wrapper element, so
    # extra.css's own ".md-typeset p.reference + p.reference" rule (still
    # concatenated into cleaned_original_css above) never actually matches
    # anything here; these plain ".reference" selectors are what make either
    # style actually apply in the PDF.
    if reference_style_global:
        reference_style_css = f"""
p.reference {{
    padding-left: {reference_indent_global} !important;
    text-indent: -{reference_indent_global} !important;
}}
p.reference + p.reference {{
    margin-top: {reference_spacing_global} !important;
}}
"""
    else:
        reference_style_css = f"""
p.reference + p.reference {{
    margin-top: {reference_spacing_european} !important;
}}
"""

    # PDF equivalent of the website's acronym_style() macro (see macros.py)
    # (see docs/acronyms.md) - same reasoning as reference_style_css above:
    # Pandoc's HTML output has no ".md-typeset" wrapper, so this plain
    # ".acronym" selector is what actually applies the tight spacing here.
    acronym_style_css = f"""
p.acronym + p.acronym {{
    margin-top: {reference_spacing_european} !important;
}}
"""

    # PDF equivalent of the website's glossary_style() macro (see macros.py)
    # (see docs/glossary.md) - same reasoning as reference_style_css above.
    glossary_style_css = f"""
p.glossary + p.glossary {{
    margin-top: {reference_spacing_european} !important;
}}
"""

    # NOTE (zendoc-template#92/#93): the old pipeline's per-table "| <"
    # prepend position tracking (caption_state/prepend_table_ids) doesn't
    # apply to the new render_page_html() pipeline - pymdownx.blocks.caption's
    # own HTML output already places a prepended figcaption/caption physically
    # first in the DOM. Pandoc's own HTML writer does NOT preserve this
    # positioning though (confirmed: its Figure AST node always re-emits the
    # caption after the content, regardless of source order) - worked around
    # in render_page_html() by retagging any prepend-position figure/table
    # caption to a <div> before Pandoc parses it, which does preserve order.
    with open(temp_compiled_css, "w", encoding="utf-8") as f:
        f.write(cleaned_original_css + "\n\n" + final_css_payload + "\n\n" + reference_style_css + "\n\n" + acronym_style_css + "\n\n" + glossary_style_css)

    cmd = [
        "pandoc",
        os.path.join(temp_build_dir, "_temp_master_compiled.html"),
        "-o", output_pdf,
        "--pdf-engine=weasyprint",
        "--pdf-engine-opt=-q",
        "--mathjax",
        f"--lua-filter={lua_filter_path}",
        "-f", "html",
        "--resource-path=.",
        f"--resource-path={docs_dir}",
        f"--css={temp_compiled_css}"
    ]

    print("🚀 Processing via unified layout configuration framework...")
    try:
        subprocess.run(cmd, check=True)
        print(f"\n🎉 Success! The document compiled cleanly. PDF ready at: {output_pdf}")
    except subprocess.CalledProcessError:
        print("\n❌ Error: Pandoc/Weasyprint failed to compile the document stream.")
    finally:
        if os.path.exists(temp_build_dir):
            shutil.rmtree(temp_build_dir)

if __name__ == "__main__":
    main()