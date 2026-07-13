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

# In-process cache so the same emoji is never fetched/read twice within a single build
_TWEMOJI_SVG_CACHE = {}

def resolve_twemoji_svg(unicode_str, icon_registry):
    """Resolves a genuine (non-icon-set) emoji's Unicode sequence to twemoji SVG data.

    Checks the already-discovered icon registry and an on-disk cache under
    ./.icons/twemoji first (fully offline once populated), then falls back to
    fetching the matching asset from the twemoji CDN and caching it locally so
    future builds no longer need network access for that emoji.
    """
    codepoints_full = "-".join(f"{ord(ch):x}" for ch in unicode_str)
    codepoints_stripped = "-".join(f"{ord(ch):x}" for ch in unicode_str if ch != '️')
    candidates = list(dict.fromkeys(c for c in [codepoints_full, codepoints_stripped] if c))

    for cp in candidates:
        if cp in _TWEMOJI_SVG_CACHE:
            return _TWEMOJI_SVG_CACHE[cp]

        abs_path = icon_registry.get(f"twemoji-{cp}") or icon_registry.get(cp)
        if abs_path and os.path.exists(abs_path):
            with open(abs_path, 'r', encoding='utf-8') as f:
                svg_data = f.read()
            _TWEMOJI_SVG_CACHE[cp] = svg_data
            return svg_data

    cache_dir = os.path.join(os.getcwd(), ".icons", "twemoji")
    for cp in candidates:
        cache_path = os.path.join(cache_dir, f"{cp}.svg")
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                svg_data = f.read()
            icon_registry[f"twemoji-{cp}"] = cache_path
            icon_registry.setdefault(cp, cache_path)
            _TWEMOJI_SVG_CACHE[cp] = svg_data
            return svg_data

    for cp in candidates:
        url = f"https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/svg/{cp}.svg"
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                svg_data = resp.read().decode('utf-8')
        except Exception:
            continue

        try:
            os.makedirs(cache_dir, exist_ok=True)
            cache_path = os.path.join(cache_dir, f"{cp}.svg")
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(svg_data)
            icon_registry[f"twemoji-{cp}"] = cache_path
            icon_registry.setdefault(cp, cache_path)
        except Exception:
            pass

        _TWEMOJI_SVG_CACHE[cp] = svg_data
        return svg_data

    return None

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

def parse_caption_modifier(modifier):
    """Parses the optional "| ..." modifier after a caption block's type
    name - pymdownx.blocks.caption's own header syntax for overriding
    position, number, id, and classes on a single caption (see "Captions"
    in customise.md), e.g. "| < 5 #custom-id.some-class". Returns
    (prepend, manual_number, custom_id, extra_classes):
    - prepend: True/False if "<"/">" is present, else None (caller decides
      the default - this template never sets a project-wide prepend: true,
      so the extension's own default is append).
    - manual_number: int if a bare integer token is present, else None.
    - custom_id / extra_classes: from a "#id.class1.class2"-style token,
      mirroring the CSS-selector shorthand the extension itself accepts."""
    prepend = None
    manual_number = None
    custom_id = None
    extra_classes = []
    if not modifier:
        return prepend, manual_number, custom_id, extra_classes
    for token in modifier.split():
        if token == '<':
            prepend = True
        elif token == '>':
            prepend = False
        elif token.isdigit():
            manual_number = int(token)
        elif token.startswith('#') or token.startswith('.'):
            id_match = re.search(r'#([\w-]+)', token)
            if id_match:
                custom_id = id_match.group(1)
            extra_classes.extend(re.findall(r'\.([\w-]+)', token))
    return prepend, manual_number, custom_id, extra_classes

def image_attrs_to_html(attrs):
    """Converts a Pandoc-style image attribute block (the "{ width="40%"
    .screenshot }" in "![alt](src){ width="40%" .screenshot }") into an HTML
    attribute string for a hand-written <img> tag - needed because
    zensical_caption_replacer() below builds its <figure>/<img>/<figcaption>
    markup directly as raw HTML rather than letting Pandoc's own markdown
    reader process the image, so Pandoc's own attribute handling (see issue
    #55) never sees this block unless it's redone here. Mirrors Pandoc's own
    behaviour: a width/height value that has a unit (e.g. "40%", "2cm")
    becomes an inline CSS style (Pandoc emits `style="width:40%"` for
    `{width="40%"}`); a bare integer becomes the legacy width/height HTML
    attribute (pixels). A ".class" token (e.g. ".screenshot" - see "Captions"
    in customise.md) becomes the <img>'s own class attribute - distinct from
    the <figure>'s own class (zendoc-figure-caption etc. - see
    zensical_caption_replacer() below), since the framed-screenshot CSS
    targets "img.screenshot" specifically. A "#id" token becomes the <img>'s
    id. Any other key becomes a plain HTML attribute."""
    if not attrs:
        return ''
    style_parts = []
    html_parts = []
    classes = []
    for token in re.findall(r'[\w-]+="[^"]*"|[\w-]+=\S+|\.[\w-]+|#[\w-]+', attrs):
        if token.startswith('.'):
            classes.append(token[1:])
            continue
        if token.startswith('#'):
            html_parts.append(f'id="{token[1:]}"')
            continue
        key, _, value = token.partition('=')
        value = value.strip('"\'')
        if key in ('width', 'height'):
            if re.match(r'^\d+$', value):
                html_parts.append(f'{key}="{value}"')
            else:
                style_parts.append(f'{key}:{value}')
        else:
            html_parts.append(f'{key}="{value}"')
    if classes:
        html_parts.append(f'class="{" ".join(classes)}"')
    style_attr = f' style="{"; ".join(style_parts)}"' if style_parts else ''
    html_attr = (' ' + ' '.join(html_parts)) if html_parts else ''
    return f'{html_attr}{style_attr}'

def compute_pdf_word_count(markdown_paths):
    """Rough prose word count across the given already-preprocessed markdown
    files: strips fenced code, inline code, HTML tags/comments, and markdown
    link/image/emphasis syntax before splitting on whitespace. Used to fill in
    the cover page's {WORDCOUNT} marker (see index.md); excludes the cover
    page itself and the auto-generated Table of Contents, since neither is
    "content".
    """
    total_words = 0
    for path in markdown_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
        except OSError:
            continue
        text = re.sub(r'<!--.*?-->', ' ', text, flags=re.DOTALL)
        text = re.sub(r'```.*?```', ' ', text, flags=re.DOTALL)
        text = re.sub(r'~~~.*?~~~', ' ', text, flags=re.DOTALL)
        text = re.sub(r'`[^`]*`', ' ', text)
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

def render_mermaid_diagrams(content, temp_build_dir, mermaid_state):
    """Pre-renders ```mermaid fenced code blocks (see
    https://zensical.org/docs/authoring/diagrams/) to static SVGs via a local
    mermaid-cli install under tools/mermaid. WeasyPrint has no JS engine to
    run Mermaid.js client-side the way the live Zensical site does, so the
    diagram source must become an image before Pandoc ever sees it. The
    emitted markdown image tag is then picked up and base64-inlined by the
    existing image encoder further down in preprocess_markdown().
    """
    mmdc_bin = os.path.abspath(os.path.join("tools", "mermaid", "node_modules", ".bin", "mmdc"))
    if not os.path.exists(mmdc_bin):
        return content
    # Mermaid's default node/edge labels are HTML <foreignObject> content, which
    # WeasyPrint's SVG renderer can't display (text silently vanishes). Forcing
    # htmlLabels off makes mermaid emit plain SVG <text>/<tspan> labels instead.
    mmdc_config = os.path.abspath(os.path.join("tools", "mermaid", "mermaid_pdf_config.json"))
    # --no-sandbox: CI runners launch Chromium as root, where its sandbox refuses
    # to start without this; harmless when running unprivileged locally too.
    puppeteer_config = os.path.abspath(os.path.join("tools", "mermaid", "puppeteer_config.json"))

    mermaid_dir = os.path.join(temp_build_dir, "mermaid_diagrams")

    def replace(match):
        indent = match.group(1)
        raw_block = match.group(2)
        diagram_source = "\n".join(
            line[len(indent):] if line.startswith(indent) else line.lstrip()
            for line in raw_block.splitlines()
        )

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
            return match.group(0)

        return f'{indent}![Mermaid diagram]({svg_path})'

    return re.sub(
        r'^([ \t]*)```[ \t]*\{?\.?mermaid\}?[ \t]*\n(.*?)\n\1```[ \t]*$',
        replace,
        content,
        flags=re.MULTILINE | re.DOTALL
    )

def convert_reference_attr_list_paragraphs(content):
    """Converts docs/references.md's, docs/acronyms.md's, and docs/glossary.md's
    `paragraph\n{: #id .class }` entries - Python-Markdown's attr_list syntax,
    understood natively by the website -
    into `<p id="id" class="class" markdown="1">paragraph</p>` blocks instead,
    since Pandoc (used for the PDF) has no idea what a standalone `{: ... }`
    line means and would otherwise leave it sitting in the output as literal,
    visible text. This lets those pages themselves stay as plain attr_list
    Markdown; the rewrite only happens in memory, for the PDF build. Only
    matches a `{: ... }` line that directly follows one or more non-blank
    lines with no blank line in between (i.e. attached to that paragraph),
    and only touches lines containing a `#id` - attr_list lines without one
    (not used in these files, but a reasonable safety net) are left alone."""
    pattern = re.compile(r'^((?:.+\n)+?)\{:\s*([^}]+?)\s*\}[ \t]*$', re.MULTILINE)

    def replacer(match):
        paragraph, attrs = match.group(1).rstrip('\n'), match.group(2)
        id_match = re.search(r'#([\w-]+)', attrs)
        if not id_match:
            return match.group(0)
        classes = re.findall(r'\.([\w-]+)', attrs)
        class_attr = f' class="{" ".join(classes)}"' if classes else ''
        return f'<p id="{id_match.group(1)}"{class_attr} markdown="1">{paragraph}</p>'

    return pattern.sub(replacer, content)

def convert_text_alignment_attr_list_paragraphs(content):
    """Converts a paragraph followed by a bare `{: .text-center }` (or any of
    the other five text-alignment/text-alignment-italic utility classes
    defined in extra.css) into `<p class="...">paragraph</p>`, since Pandoc
    (used for the PDF) has no idea what a standalone `{: ... }` line means and
    would otherwise leave it sitting in the output as literal, visible text
    (see issue #58). Unlike convert_reference_attr_list_paragraphs (id-based,
    References/Acronyms/Glossary only), this runs on every page - deliberately
    scoped to just these six known utility classes, and skipping anything with
    an `#id` or an unrecognised class, so it can't collide with attr_list used
    for other purposes (references, images, tables, code fences) elsewhere in
    this file. Run through apply_outside_fences() so a documentation example
    showing this exact syntax inside a fenced code block (e.g. a future
    "Text alignment" section in customise.md, following the same pattern as
    its existing References/Acronyms/Captions examples) is left as literal
    text rather than being converted into a live, rendered paragraph."""
    utility_classes = {
        'text-center', 'text-right', 'text-justify',
        'text-center-italic', 'text-right-italic', 'text-justify-italic',
    }
    pattern = re.compile(r'^((?:.+\n)+?)\{:\s*([^}]+?)\s*\}[ \t]*$', re.MULTILINE)

    def replacer(match):
        paragraph, attrs = match.group(1).rstrip('\n'), match.group(2)
        if '#' in attrs:
            return match.group(0)
        classes = re.findall(r'\.([\w-]+)', attrs)
        if not classes or not set(classes) <= utility_classes:
            return match.group(0)
        return f'<p class="{" ".join(classes)}" markdown="1">{paragraph}</p>'

    return apply_outside_fences(content, lambda segment: pattern.sub(replacer, segment))

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

def _walk_outside_fences(content, line_handler):
    """Shared fence-aware line-by-line walk: calls line_handler(line) for every
    line outside a fenced code block *and* outside an HTML comment (leaving
    both untouched), and stops calling it once line_handler returns a truthy
    "stop" signal. The HTML-comment skip matters because every page's
    copyright header is a `<!-- ... -->` block, and about half of them write
    the copyright/SPDX lines inside it with a leading "# " (mimicking a
    Markdown heading) - without skipping comments, tag_first_heading() below
    would mistake that line for the page's real title. Used by
    tag_first_heading() and mirrors the fence-tracking already used elsewhere
    in this file (e.g. _dashes_to_asterisks_outside_fences)."""
    lines = content.split('\n')
    in_fence, fence_char, fence_len = False, None, 0
    in_comment = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if in_fence:
            close_match = re.match(r'^(`{3,}|~{3,})\s*$', stripped)
            if close_match and close_match.group(1)[0] == fence_char and len(close_match.group(1)) >= fence_len:
                in_fence = False
            continue
        if in_comment:
            if '-->' in line:
                in_comment = False
            continue
        fence_match = re.match(r'^(`{3,}|~{3,})', stripped)
        if fence_match:
            in_fence = True
            fence_char = fence_match.group(1)[0]
            fence_len = len(fence_match.group(1))
            continue
        comment_start = line.find('<!--')
        if comment_start != -1:
            if '-->' not in line[comment_start:]:
                in_comment = True
            continue
        result = line_handler(i, line)
        if result is not None:
            lines[i] = result
            break
    return '\n'.join(lines)

def _split_fenced_blocks(text):
    """Splits text into a list of (is_fenced, segment) tuples, alternating
    between non-fenced and fenced (```/~~~) content, using the same fence
    detection as the rest of this file. Used by apply_outside_fences()."""
    lines = text.split('\n')
    segments = []
    current = []
    in_fence, fence_char, fence_len = False, None, 0
    for line in lines:
        stripped = line.strip()
        if not in_fence:
            fence_match = re.match(r'^(`{3,}|~{3,})', stripped)
            if fence_match:
                if current:
                    segments.append((False, '\n'.join(current)))
                current = [line]
                in_fence = True
                fence_char = fence_match.group(1)[0]
                fence_len = len(fence_match.group(1))
            else:
                current.append(line)
        else:
            current.append(line)
            close_match = re.match(r'^(`{3,}|~{3,})\s*$', stripped)
            if close_match and close_match.group(1)[0] == fence_char and len(close_match.group(1)) >= fence_len:
                in_fence = False
                segments.append((True, '\n'.join(current)))
                current = []
    if current:
        segments.append((in_fence, '\n'.join(current)))
    return segments

def apply_outside_fences(content, transform):
    """Applies transform(text) -> text only to the portions of content that
    are outside fenced code blocks, leaving fenced content completely
    untouched. Needed for regex-based rewrites (e.g. the caption block
    translation below) that would otherwise also match - and corrupt -
    example syntax shown as literal text inside a fenced code block in the
    docs (see docs/starthere/customise.md's "Captions" section, which shows
    the caption syntax itself as an example). Segments are rejoined with "\n"
    (not "") - _split_fenced_blocks() strips every newline via text.split(),
    and each segment's own text only accounts for the newlines *within* it,
    so the newline originally separating one segment from the next has to be
    reinserted here, exactly once per boundary, regardless of whether
    transform() changes a non-fenced segment's own line count."""
    return '\n'.join(
        segment if is_fenced else transform(segment)
        for is_fenced, segment in _split_fenced_blocks(content)
    )

def tag_first_heading(content, anchor, extra_class=None):
    """Gives a page's first top-level heading an explicit #anchor id (unless
    it already has one), so other pages can link to it by that id once
    everything is concatenated into a single PDF document. See
    build_page_anchor_map() / issue #16. If the heading already has a
    trailing {...} attribute block (e.g. the cover page's {.hidden
    .unnumbered .unlisted}), the id is inserted into that same block rather
    than appended as a second, separate {...} block - Pandoc only recognises
    one attribute block per heading, and a second one is left sitting in the
    output as literal, visible text instead of being parsed as an id.

    If extra_class is given (e.g. "appendix" - see page_is_appendix() /
    issue #24), it's added to the same block as a .class, giving the Lua
    numbering filter's Header() function something to detect on the raw
    Pandoc AST node - preprocess_markdown() itself has no reach into that
    filter, so this attribute is the only way to carry the flag through."""
    suffix = f'#{anchor}' + (f' .{extra_class}' if extra_class else '')
    def handler(_i, line):
        if not re.match(r'^#\s+\S', line):
            return None
        brace_match = re.search(r'\{([^}]*)\}\s*$', line)
        if brace_match:
            if '#' in brace_match.group(1):
                return line  # already has an explicit id - leave it alone
            end = brace_match.end(1)
            return f'{line[:end]} {suffix}{line[end:]}'
        return f'{line.rstrip()} {{{suffix}}}'
    return _walk_outside_fences(content, handler)

def rewrite_internal_md_links(content, current_docs_rel_path, page_anchor_map):
    """Rewrites relative .md links - e.g. [Install tooling](installtooling.md)
    or [Skoulikari, 2023](references.md#skou2023) - into in-document anchor
    links (#page-anchor or the existing #fragment) that resolve correctly once
    every page has been concatenated into one PDF (see build_page_anchor_map()
    / issue #16). A fragment on the original link (an id that already exists
    somewhere in the document, whether Pandoc's own auto-generated heading id
    or one we assign explicitly, e.g. via convert_reference_attr_list_paragraphs)
    is kept as-is; only the now-meaningless "target.md" file prefix is
    dropped. Skips fenced code blocks, so example link syntax shown as
    literal text in the docs (e.g. in zensicalbasics.md) survives unchanged."""
    current_dir = os.path.dirname(current_docs_rel_path)
    link_pattern = re.compile(r'\[([^\]]*)\]\(([^)\s]+?\.md)(#[\w-]+)?\)')

    def replace_link(match):
        text, target, frag = match.group(1), match.group(2), match.group(3)
        if target.startswith(('http://', 'https://', 'mailto:')):
            return match.group(0)
        if frag:
            return f'[{text}]({frag})'
        resolved = os.path.normpath(os.path.join(current_dir, target)).replace('\\', '/')
        anchor = page_anchor_map.get(resolved)
        if anchor is None:
            return match.group(0)
        return f'[{text}](#{anchor})'

    lines = content.split('\n')
    in_fence, fence_char, fence_len = False, None, 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not in_fence:
            fence_match = re.match(r'^(`{3,}|~{3,})', stripped)
            if fence_match:
                in_fence = True
                fence_char = fence_match.group(1)[0]
                fence_len = len(fence_match.group(1))
            else:
                lines[i] = link_pattern.sub(replace_link, line)
        else:
            close_match = re.match(r'^(`{3,}|~{3,})\s*$', stripped)
            if close_match and close_match.group(1)[0] == fence_char and len(close_match.group(1)) >= fence_len:
                in_fence = False
    return '\n'.join(lines)

def rewrite_repo_file_links(content, current_docs_rel_path, docs_dir, repo_url):
    """Rewrites relative links to non-Markdown repo files - e.g.
    [extra.css](../stylesheets/extra.css) - into the file's canonical
    GitHub/GitLab "blob" URL instead (see issue #19). Unlike the .md links
    rewrite_internal_md_links() handles, these targets aren't part of the
    concatenated PDF at all, so there's no in-document anchor to point at;
    left as a plain relative path, Pandoc/WeasyPrint resolve it against the
    build machine's own filesystem instead, producing a link that's
    meaningless (and reveals a local file path) to anyone else reading the
    PDF. Falls back to dropping the link and keeping just its text if
    repo_url is empty or its host isn't recognised, rather than risk
    guessing the wrong URL scheme. Skips fenced code blocks (so example link
    syntax shown as literal text survives unchanged), image embeds (already
    resolved to real embedded images by WeasyPrint, not links), and links
    that are external (http(s)/mailto), fragment-only (#id), site-root
    (leading /), or already handled by rewrite_internal_md_links (.md,
    optionally with a #fragment)."""
    repo_url_lower = repo_url.lower()
    if 'github.com' in repo_url_lower:
        blob_prefix = f'{repo_url}/blob/main/'
    elif 'gitlab' in repo_url_lower:
        blob_prefix = f'{repo_url}/-/blob/main/'
    else:
        blob_prefix = None

    current_dir = os.path.dirname(current_docs_rel_path)
    link_pattern = re.compile(r'(?<!!)\[([^\]]*)\]\(([^)\s]+)\)')

    def replace_link(match):
        text, target = match.group(1), match.group(2)
        if target.startswith(('http://', 'https://', 'mailto:', '#', '/')):
            return match.group(0)
        if target.endswith('.md') or '.md#' in target:
            return match.group(0)
        if blob_prefix is None:
            return text
        repo_rel_path = os.path.normpath(os.path.join(docs_dir, current_dir, target)).replace('\\', '/')
        return f'[{text}]({blob_prefix}{repo_rel_path})'

    return apply_outside_fences(content, lambda text: link_pattern.sub(replace_link, text))

def preprocess_markdown(file_path, output_path, config, calculated_vars, icon_registry, placeholder_map, temp_build_dir, mermaid_state, page_anchor_map, nav_snippet_text='', is_index=False, chapter_id=None, caption_state=None):
    """Parses template conditionals, applies global asset filtering, and converts raw shortcodes
    to alphanumeric tokens while ignoring those nested inside code block environments.

    chapter_id is this page's own chapter number ("7") or appendix letter
    ("A") - computed once per page in main(), before any page is
    preprocessed, by replicating macros.py's own nav-walk (see
    _page_is_appendix()/_count_top_level_headings() there) - the same
    number the website computes via heading_counter_reset() and the Lua
    filter computes via its own h1 counter, needed here because figure/table
    captions (see "Captions" in customise.md) are numbered "Figure
    <chapter>.<n>" during this preprocessing pass, before pages are
    concatenated and the Lua filter's counter exists. caption_state is a
    shared dict threaded across every page's preprocess_markdown() call,
    collecting id="..." values that requested a prepended (top) position so
    main() can emit a targeted caption-side CSS rule for exactly those,
    once every page has been preprocessed - see "prepend_table_ids" below.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.lstrip('\ufeff')

    if content.strip().startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2]

    # Fixes issue #16: give this page a linkable anchor, and rewrite any
    # links to *other* pages so they point at that anchor instead of a
    # "target.md" file path that means nothing once every page is
    # concatenated into one PDF document. See build_page_anchor_map().
    docs_dir = config.get('docs_dir', 'docs')
    current_docs_rel_path = os.path.normpath(os.path.relpath(file_path, docs_dir)).replace('\\', '/')
    own_anchor = page_anchor_map.get(current_docs_rel_path)
    if own_anchor:
        extra_class = 'appendix' if page_is_appendix(file_path) else None
        content = tag_first_heading(content, own_anchor, extra_class=extra_class)
    content = rewrite_internal_md_links(content, current_docs_rel_path, page_anchor_map)
    content = rewrite_repo_file_links(content, current_docs_rel_path, docs_dir, calculated_vars.get('repo_url', ''))

    content = render_mermaid_diagrams(content, temp_build_dir, mermaid_state)

    content = re.sub(r'^.*user-select.*$\n?', '', content, flags=re.MULTILINE | re.IGNORECASE)

    # Strips the website-only heading_counter_reset(page) Jinja macro call (injects a
    # CSS counter-reset <style> block for the live site); the PDF numbers headings
    # separately via the Lua filter's Header() function, so this has no PDF equivalent
    # and would otherwise leak through as literal text since Pandoc doesn't render Jinja.
    content = re.sub(r'^[ \t]*\{\{\s*heading_counter_reset\([^)]*\)\s*\}\}[ \t]*\n?', '', content, flags=re.MULTILINE)

    # Strips the website-only reference_style() Jinja macro call (injects a CSS
    # override <style> block on the References page for the live site); the PDF
    # gets the equivalent CSS added directly to the compiled stylesheet instead
    # (see reference_style_enabled below), since Pandoc doesn't render Jinja and
    # would otherwise leak this through as literal text.
    content = re.sub(r'^[ \t]*\{\{\s*reference_style\(\s*\)\s*\}\}[ \t]*\n?', '', content, flags=re.MULTILINE)

    # Replaces the website-only nav_snippet() Jinja macro call with the same
    # extracted nav = [...] text it would render on the website (Pandoc
    # doesn't render Jinja, so the literal "{{ nav_snippet() }}" would
    # otherwise leak through as-is into the PDF).
    content = re.sub(r'\{\{\s*nav_snippet\(\s*\)\s*\}\}', lambda _: nav_snippet_text, content)

    # References, acronyms, and glossary pages only: rewrite attr_list
    # `{: #id .class }` entries into Pandoc-compatible raw HTML (see
    # convert_reference_attr_list_paragraphs).
    if os.path.basename(file_path) in ('references.md', 'acronyms.md', 'glossary.md'):
        content = convert_reference_attr_list_paragraphs(content)

    # Every page: rewrite the six text-alignment utility classes' attr_list
    # `{: .text-center }` entries into Pandoc-compatible raw HTML (see
    # convert_text_alignment_attr_list_paragraphs).
    content = convert_text_alignment_attr_list_paragraphs(content)

    # AUTOMATED VIDEO EMBEDDING INTERCEPTOR ENGINE
    def video_iframe_replacer(match):
        indent = match.group(1) or ""
        iframe_tag = match.group(2)
        
        src_match = re.search(r'src=["\']([^"\']+)["\']', iframe_tag, re.IGNORECASE)
        title_match = re.search(r'title=["\']([^"\']+)["\']', iframe_tag, re.IGNORECASE)
        
        if not src_match:
            return match.group(0)
            
        video_url = src_match.group(1)
        if "youtube.com/embed/" in video_url:
            video_url = video_url.replace("youtube.com/embed/", "youtube.com/watch?v=").split('?')[0]
            
        video_title = title_match.group(1).strip() if title_match else "Video Tutorial"
        
        return (
            f"\n\n{indent}!!! info \"{video_title}\"\n"
            f"{indent}    **[Watch Video]({video_url})**\n\n"
        )

    content = re.sub(
        r'^([ \t]*)(?:<div[^>]*>[\s\r\n]*)?(<iframe[^>]+>.*?<\/iframe>)(?:[\s\r\n]*<\/div>)?',
        video_iframe_replacer,
        content,
        flags=re.MULTILINE | re.IGNORECASE | re.DOTALL
    )

    # AUTOMATED ZENSICAL CAPTION BLOCK TRANSLATION ENGINE
    # Handles both the plain, unnumbered "caption" type (unchanged from
    # before - no id, no prefix) and the numbered "figure-caption" type
    # (see "Captions" in customise.md): auto-numbered "Figure <chapter>.<n>"
    # using this page's own chapter_id plus a per-page counter mirroring
    # pymdownx.blocks.caption's own website-side counter, a manual number
    # override (honoured if given, and the auto-counter picks up from
    # there), and a custom #id/.class in place of the auto-generated id -
    # see parse_caption_modifier(). figure-caption always appends (image,
    # then caption) to match this template's own usage; a "| <"/"| >"
    # modifier is still parsed for completeness but isn't expected to be
    # used with figures in this template's own docs.
    figure_counter = 0
    def zensical_caption_replacer(match):
        nonlocal figure_counter
        indent = match.group(1)
        alt_text = match.group(2)
        img_url = match.group(3)
        image_attrs = match.group(4)
        caption_type = match.group(5)
        modifier = match.group(6)
        caption_body = match.group(7).strip()

        prepend, manual_number, custom_id, extra_classes = parse_caption_modifier(modifier)
        classes = list(extra_classes)
        figure_id = custom_id

        if caption_type == 'figure-caption':
            figure_counter = max(figure_counter, manual_number) if manual_number else figure_counter + 1
            this_number = manual_number if manual_number is not None else figure_counter
            number_text = f"{chapter_id}.{this_number}." if chapter_id else f"{this_number}."
            prefix_html = f'<span class="caption-prefix">Figure {number_text}</span> '
            if figure_id is None:
                figure_id = f"figure-{(chapter_id or 'x').lower()}-{this_number}"
            classes.insert(0, 'zendoc-figure-caption')
        else:
            prefix_html = ''

        class_attr = f' class="{" ".join(classes)}"' if classes else ''
        id_attr = f' id="{figure_id}"' if figure_id else ''

        img_html = f"{indent}  <img src=\"{img_url}\" alt=\"{alt_text}\"{image_attrs_to_html(image_attrs)} />\n"
        figcaption_html = f"{indent}  <figcaption class=\"text-center-italic\" style=\"margin-top: 8px;\">{prefix_html}{caption_body}</figcaption>\n"
        body = (figcaption_html + img_html) if prepend else (img_html + figcaption_html)

        return (
            f"\n\n{indent}<figure{id_attr}{class_attr}>\n"
            f"{body}"
            f"{indent}</figure>\n\n"
        )

    content = apply_outside_fences(content, lambda text: re.sub(
        r'^([ \t]*)!\[([^\]]*)\]\(([^)]*)\)(?:\{([^}]*)\})?[ \t]*\n(?:[ \t]*\n)*\1///\s*(figure-caption|caption)(?:[ \t]*\|[ \t]*([^\n]*))?[ \t]*\n(.*?)\n\1///',
        zensical_caption_replacer,
        text,
        flags=re.MULTILINE | re.DOTALL
    ))

    # AUTOMATED ZENSICAL TABLE CAPTION TRANSLATION ENGINE
    # Converts a caption block following a table into Pandoc's native table-caption
    # syntax ("Table: ..." immediately after the table {#id .class}), which Pandoc
    # renders as a real <caption> bound inside the <table> element - keeping it
    # structurally attached to the table so it can't be orphaned from it across a
    # page break. Caption must come AFTER the table: pymdownx.blocks.caption (used
    # on the live site) attaches a caption block to whichever sibling precedes it,
    # so a caption placed before the table would wrongly attach to the paragraph
    # above instead.
    #
    # Numbering/id/class work exactly like figure-caption above, sharing the same
    # chapter_id and parse_caption_modifier() logic, but with a separate counter
    # (tables and figures are numbered independently). Position is different: Pandoc's
    # native table-caption syntax always places the caption line *after* the table in
    # the source, so genuinely moving it before the table isn't possible without
    # hand-rolling table markup Pandoc would otherwise parse for us - "prepend" here
    # instead means a real, per-table caption-side: top CSS override (added once every
    # page has been preprocessed - see caption_state/prepend_table_ids in main()),
    # visually equivalent to a true prepend without the risk of a hand-written
    # Markdown-table-to-HTML conversion. The plain "caption" type keeps this template's
    # original default of always showing at the top, for backward compatibility.
    table_counter = 0
    anon_table_counter = 0
    def table_caption_replacer(match):
        nonlocal table_counter, anon_table_counter
        table_lines = match.group(1)
        caption_type = match.group(3)
        modifier = match.group(4)
        caption_body = match.group(5).strip()

        prepend, manual_number, custom_id, extra_classes = parse_caption_modifier(modifier)
        attrs = []

        if caption_type == 'table-caption':
            table_counter = max(table_counter, manual_number) if manual_number else table_counter + 1
            this_number = manual_number if manual_number is not None else table_counter
            number_text = f"{chapter_id}.{this_number}." if chapter_id else f"{this_number}."
            caption_text = f"Table {number_text} {caption_body}"
            table_id = custom_id or f"table-{(chapter_id or 'x').lower()}-{this_number}"
            wants_top = prepend is True
        else:
            caption_text = caption_body
            # A plain caption doesn't get a numbered id, but still needs a
            # unique one so the top-position CSS override below (which is
            # id-targeted, not a blanket rule - see the note above) can
            # still apply to it for backward compatibility.
            anon_table_counter += 1
            table_id = custom_id or f"table-{(chapter_id or 'x').lower()}-caption-{anon_table_counter}"
            wants_top = prepend is not False  # unset defaults to this template's original top placement

        if table_id:
            attrs.append(f'#{table_id}')
        attrs.extend(f'.{c}' for c in extra_classes)

        if wants_top and table_id and caption_state is not None:
            caption_state.setdefault('prepend_table_ids', set()).add(table_id)

        attr_block = f" {{{' '.join(attrs)}}}" if attrs else ''
        return f"{table_lines}\nTable: {caption_text}{attr_block}\n\n"

    content = apply_outside_fences(content, lambda text: re.sub(
        r'((?:^[ \t]*\|[^\n]*\n)+)(?:[ \t]*\n)*^([ \t]*)///\s*(table-caption|caption)(?:[ \t]*\|[ \t]*([^\n]*))?[ \t]*\n(.*?)\n\2///[ \t]*\n?',
        table_caption_replacer,
        text,
        flags=re.MULTILINE | re.DOTALL
    ))

    # GLOBAL LOCAL ASSET BASE64 ENCODING ENGINE
    def to_base64_data_uri(img_src, base_dir):
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

    # Helper function to allocate safe alphanumeric tokens
    def register_icon_token(abs_svg_path, raw_svg_data=None):
        try:
            if raw_svg_data:
                b64_payload = base64.b64encode(raw_svg_data.encode('utf-8')).decode('utf-8')
            else:
                if not abs_svg_path or not os.path.exists(abs_svg_path): return None
                with open(abs_svg_path, 'rb') as f:
                    b64_payload = base64.b64encode(f.read()).decode('utf-8')
                    
            for key, val in placeholder_map.items():
                if val == b64_payload: return key
                
            token_key = f"ZICALICONPAD{len(placeholder_map):04d}"
            placeholder_map[token_key] = b64_payload
            return token_key
        except Exception:
            return None

    # Resolves an admonition type (note, warning, tip, ...) to an inline icon
    # token, using the same icon set configured for the website's admonitions
    # in project.theme.icon.admonition (zensical.toml) - see
    # https://zensical.org/docs/authoring/admonitions/#supported-types
    admonition_icon_shortcodes = {}
    project_cfg = config.get('project')
    if isinstance(project_cfg, dict):
        theme_cfg = project_cfg.get('theme')
        if isinstance(theme_cfg, dict):
            icon_cfg = theme_cfg.get('icon')
            if isinstance(icon_cfg, dict):
                adm_icon_cfg = icon_cfg.get('admonition')
                if isinstance(adm_icon_cfg, dict):
                    admonition_icon_shortcodes = adm_icon_cfg

    # Mirrors the border-left-color set per admonition type in the .admonition.<type>
    # CSS rules below, so the icon matches the coloured bar rather than rendering
    # in its raw (black) fill.
    admonition_accent_colors = {
        "note": "#448aff", "abstract": "#00b0ff", "info": "#00b8d4", "tip": "#00bfa5",
        "success": "#00c853", "question": "#64dd17", "warning": "#ff9100", "failure": "#ff5252",
        "danger": "#ff1744", "bug": "#ec407a", "example": "#651fff", "quote": "#9e9e9e",
    }

    def resolve_admonition_icon_token(adm_type):
        shortcode = admonition_icon_shortcodes.get(adm_type)
        if not shortcode:
            return None
        key = shortcode.strip('/').lower().replace('/', '-')
        abs_path = icon_registry.get(key)
        if not abs_path:
            return None
        accent_color = admonition_accent_colors.get(adm_type)
        if not accent_color:
            return register_icon_token(abs_path)
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                svg_data = f.read()
            # "currentColor" resolves against the CSS `color` property, not `fill` -
            # setting fill="..." on the <svg> root has no effect on a descendant
            # path's fill="currentColor", so replace it directly instead.
            svg_data = re.sub(r'currentColor', accent_color, svg_data, flags=re.IGNORECASE)
            return register_icon_token(None, raw_svg_data=svg_data)
        except Exception:
            return register_icon_token(abs_path)

    # AUTOMATED SIMPLE ICONS HTML EMBED INTERCEPTOR ENGINE
    def simple_icons_html_replacer(match):
        full_tag = match.group(0)
        color_slug = match.group(1).strip('/')
        alt_match = re.search(r'alt=["\']([^"\']+)["\']', full_tag, re.IGNORECASE)
        
        if not alt_match:
            return full_tag
            
        icon_name = alt_match.group(1).lower().replace(' icon', '').replace(' ', '-').strip()
        abs_path = icon_registry.get(f"simple-{icon_name}") or icon_registry.get(icon_name)
        
        if abs_path:
            try:
                with open(abs_path, 'r', encoding='utf-8') as svg_file:
                    svg_data = svg_file.read()
                if color_slug:
                    svg_data = re.sub(r'<svg\s+', f'<svg fill="{color_slug}" ', svg_data, flags=re.IGNORECASE)
                token = register_icon_token(None, raw_svg_data=svg_data)
                if token: return token
            except Exception:
                pass
        return full_tag

    content = re.sub(
        r'<img[^>]+src=["\']https?://simpleicons\.org([^"\']*)["\'][^>]*>',
        simple_icons_html_replacer,
        content,
        flags=re.IGNORECASE
    )

    # Encode standard markdown image links directly into the body
    def md_img_replacer(match):
        alt, src = match.group(1), match.group(2)
        return f"![{alt}]({to_base64_data_uri(src, os.path.dirname(file_path))})"
    # Fence-aware (see apply_outside_fences): otherwise an example showing
    # ![...](...)  syntax as literal text inside a fenced code block (e.g.
    # docs/starthere/customise.md's "Captions" section) gets "helpfully"
    # resolved to a real file and inlined as a base64 data URI instead.
    content = apply_outside_fences(content, lambda text: re.sub(
        r'!\[([^\]]*)\]\(((?!data:)[^)]+)\)', md_img_replacer, text
    ))

    # Encode all inline standard HTML image references directly into the body
    def html_img_replacer(match):
        full_tag = match.group(0)
        src = match.group(1)
        if src.startswith('data:') or 'simpleicons.org' in src:
            return full_tag
        return full_tag.replace(src, to_base64_data_uri(src, os.path.dirname(file_path)))
    content = re.sub(r'<img[^>]+src=["\']([^"\']+)["\']', html_img_replacer, content, flags=re.IGNORECASE)

    # Pandoc's markdown reader treats a standalone "---" line as a Setext H2
    # underline (turning the preceding paragraph into a heading) rather than a
    # thematic break, so rewrite it to the unambiguous "***" form - but only
    # outside fenced code blocks, so literal "---" shown as example syntax
    # (e.g. YAML frontmatter delimiters, horizontal rule examples) survives intact.
    def _dashes_to_asterisks_outside_fences(text):
        lines = text.split('\n')
        in_fence, fence_char, fence_len = False, None, 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not in_fence:
                fence_match = re.match(r'^(`{3,}|~{3,})', stripped)
                if fence_match:
                    in_fence = True
                    fence_char = fence_match.group(1)[0]
                    fence_len = len(fence_match.group(1))
                elif re.match(r'^\s*---\s*$', line):
                    lines[i] = '***'
            else:
                close_match = re.match(r'^(`{3,}|~{3,})\s*$', stripped)
                if close_match and close_match.group(1)[0] == fence_char and len(close_match.group(1)) >= fence_len:
                    in_fence = False
        return '\n'.join(lines)

    content = _dashes_to_asterisks_outside_fences(content)

    # AUTOMATED ATTR_LIST TO BRACKETED-SPAN TRANSLATION ENGINE
    # Python-Markdown's inline attr_list syntax (**text**{: .class}) isn't understood by
    # Pandoc; rewrite it to Pandoc's native bracketed-span syntax ([**text**]{.class}).
    def attr_list_span_replacer(match):
        if match.group(1) or match.group(2): return match.group(0)
        inline_text = match.group(3)
        attrs = match.group(4).strip()
        return f"[{inline_text}]{{{attrs}}}"

    content = re.sub(
        r'(```[\s\S]*?```)|(`[^`\n]*`)|(\*\*[^*\n]+\*\*|\*[^*\n]+\*)\{:\s*([^}]+)\}',
        attr_list_span_replacer,
        content
    )

    # PYMDOWNX.MARK / PYMDOWNX.CARET (INSERT) / PYMDOWNX.KEYS TO RAW HTML
    # Pandoc's markdown reader has no native support for ==mark== or
    # ++keys++, so both leak through as literal text; ^^insert^^ silently
    # collides with Pandoc's own single-caret superscript syntax and produces
    # empty <sup></sup> tags instead of an underline (issue #72). Rewrite all
    # three to raw HTML - which Pandoc's reader passes through untouched -
    # before Pandoc ever sees them, the same way html_img_replacer() above
    # does for <img> tags.
    def mark_replacer(match):
        if match.group(1) or match.group(2): return match.group(0)
        return f"<mark>{match.group(3)}</mark>"

    content = re.sub(
        r'(```[\s\S]*?```)|(`[^`\n]*`)|==(?!\s)([^\n]+?)(?<!\s)==',
        mark_replacer,
        content
    )

    def insert_replacer(match):
        if match.group(1) or match.group(2): return match.group(0)
        return f"<ins>{match.group(3)}</ins>"

    content = re.sub(
        r'(```[\s\S]*?```)|(`[^`\n]*`)|\^\^(?!\s)([^\n]+?)(?<!\s)\^\^',
        insert_replacer,
        content
    )

    # pymdownx.keys' own key-alias database (184 entries mapping shorthand
    # like "pg-up" to "Page Up", plus the CSS classes for each key) isn't
    # worth reimplementing by hand - reuse it directly via a dedicated
    # Markdown instance rather than hand-rolling the lookup table.
    _keys_md = markdown.Markdown(extensions=['pymdownx.keys'])

    def keys_replacer(match):
        if match.group(1) or match.group(2): return match.group(0)
        _keys_md.reset()
        html = _keys_md.convert(match.group(0))
        return html[len('<p>'):-len('</p>')] if html.startswith('<p>') else html

    content = re.sub(
        r'(```[\s\S]*?```)|(`[^`\n]*`)|\+{2}([\w\-]+(?:\+[\w\-]+)*?)\+{2}',
        keys_replacer,
        content
    )

    content = re.sub(r'\{\s*target=[^}]*\}', '', content, flags=re.IGNORECASE)
    content = re.sub(r'^(#{1,6})\s+Footnotes\s*$', r'\1 Footnotes {#custom-footnotes-heading}', content, flags=re.MULTILINE | re.IGNORECASE)

    if re.search(r'<style>.*?\.md-typeset\s+h1\s*\{\s*display:\s*none;?\s*\}.*?</style>', content, flags=re.DOTALL | re.IGNORECASE):
        def hide_matching_h1(match):
            line = match.group(0)
            if '{.' in line: return line.replace('{.', '{.hidden .unnumbered .unlisted .')
            elif '{' in line: return line.replace('{', '{.hidden .unnumbered .unlisted}')
            return f"{line} {{.hidden .unnumbered .unlisted}}"
        content = re.sub(r'^#\s+.*$', hide_matching_h1, content, flags=re.MULTILINE)

    # 🎯 FIX: Syntax-aware shortcut lookup engine skips code elements via alternate capture tracking
    def icon_replacer(match):
        if match.group(1) or match.group(2):
            return match.group(0)
            
        shortcode = match.group(3).lower().strip()
        abs_path = icon_registry.get(shortcode) or icon_registry.get(shortcode.replace('_', '-'))
        
        if not abs_path:
            if shortcode.startswith("material-"):
                alt_shortcode = shortcode.replace("material-", "mdi-", 1)
                abs_path = icon_registry.get(alt_shortcode) or icon_registry.get(alt_shortcode.replace('_', '-'))
            elif shortcode.startswith("mdi-"):
                alt_shortcode = shortcode.replace("mdi-", "material-", 1)
                abs_path = icon_registry.get(alt_shortcode) or icon_registry.get(alt_shortcode.replace('_', '-'))
        
        if not abs_path:
            pure_name = shortcode
            for prefix in ["material-", "mdi-", "fontawesome-", "lucide-", "octicons-", "simple-", "fa-solid-", "fa-regular-", "fa-brands-", "fa-"]:
                if shortcode.startswith(prefix):
                    pure_name = shortcode[len(prefix):]
                    break
            if not abs_path and "-" in shortcode:
                pure_name = shortcode.split("-", 1)[1]
            abs_path = icon_registry.get(pure_name) or icon_registry.get(pure_name.replace('_', '-'))
        
        if not abs_path:
            for suffix in ["-24", "-16", "-12"]:
                abs_path = icon_registry.get(f"{shortcode}{suffix}") or icon_registry.get(f"{pure_name}{suffix}")
                if abs_path: break

        if abs_path:
            token = register_icon_token(abs_path)
            if token: return token
            
        try:
            import emoji
            emojized = emoji.emojize(f":{shortcode}:", language='alias')
            if emojized != f":{shortcode}:":
                svg_data = resolve_twemoji_svg(emojized, icon_registry)
                if svg_data:
                    token = register_icon_token(None, raw_svg_data=svg_data)
                    if token: return token
                return emojized
        except Exception:
            pass
        return match.group(0)

    # Single-pass parsing configuration protecting inline code `...` and fenced blocks ```...```
    # Character class includes +/- so Gemoji-style shortcodes like :+1: and :-1: are matched too
    code_protected_shortcode_pattern = r'(```[\s\S]*?```)|(`[^`\n]*`)|:([a-zA-Z0-9_+-]+):'
    content = re.sub(code_protected_shortcode_pattern, icon_replacer, content)

    # AUTOMATED NATIVE LUCIDE HTML TAG INTERCEPTOR ENGINE
    def lucide_html_replacer(match):
        if match.group(1): return match.group(0)
        icon_name = match.group(2).lower().strip()
        abs_url = icon_registry.get(f"lucide-{icon_name}") or icon_registry.get(icon_name)
        if abs_url:
            token = register_icon_token(abs_url)
            if token: return token
        return match.group(0)

    content = re.sub(r'(```[\s\S]*?```|`[^`\n]*`)|<i[^>]+data-lucide=["\']([^"\']+)["\'][^>]*>.*?</i>', lucide_html_replacer, content, flags=re.IGNORECASE | re.DOTALL)

    # AUTOMATED FONTAWESOME HTML CODES INTERCEPTOR ENGINE
    def fontawesome_html_replacer(match):
        if not match.group(2): return match.group(0)
        style_class = match.group(2).lower().replace('fa-', '')
        icon_name = match.group(3).lower().strip()
        abs_url = icon_registry.get(f"fontawesome-{style_class}-{icon_name}") or icon_registry.get(f"fa-{style_class}-{icon_name}") or icon_registry.get(icon_name)
        if abs_url:
            token = register_icon_token(abs_url)
            if token: return token
        return match.group(0)

    content = re.sub(r'(```.*?```|`[^`]+`)|<i[^>]+class=["\'][^"\']*(fa-solid|fa-regular|fa-brands|fas|far|fab)\s+fa-([a-zA-Z0-9_-]+)[^"\']*["\'][^>]*>.*?</i>', fontawesome_html_replacer, content, flags=re.IGNORECASE | re.DOTALL)

    # AUTOMATED GITHUB OCTICONS HTML INTERCEPTOR ENGINE
    def octicons_html_replacer(match):
        if not match.group(2): return match.group(0)
        icon_name = match.group(2).lower().strip()
        abs_url = icon_registry.get(f"octicons-{icon_name}") or icon_registry.get(icon_name)
        if not abs_url:
            for suffix in ["-24", "-16"]:
                abs_url = icon_registry.get(f"octicons-{icon_name}{suffix}") or icon_registry.get(f"{icon_name}{suffix}")
                if abs_url: break
        if abs_url:
            token = register_icon_token(abs_url)
            if token: return token
        return match.group(0)

    content = re.sub(r'(```.*?```|`[^`]+`)|<span[^>]+class=["\'][^"\']*octicon-([a-zA-Z0-9_-]+)[^"\']*["\'][^>]*>.*?</span>', octicons_html_replacer, content, flags=re.IGNORECASE | re.DOTALL)

    content = re.sub(r'<script[^>]*src=["\']([^"\']*lucide[^"\']*)["\'][^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<script[^>]*>.*?lucide\.createIcons.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)

    # AUTOMATED COMMAND PROMPT INJECTOR ENGINE
    def shell_prompt_replacer(match):
        indent = match.group(1)
        lang = match.group(2)
        code_body = match.group(3)
        
        if lang.lower() in ['bash', 'sh', 'shell', 'zsh', 'console', 'cmd', 'powershell', 'terminal']:
            lines = code_body.splitlines()
            updated_lines = []
            in_continuation = False
            for line in lines:
                stripped = line.strip()
                if stripped:
                    if not in_continuation and not stripped.startswith('$') and not stripped.startswith('#'):
                        l_indent = len(line) - len(line.lstrip())
                        updated_lines.append(line[:l_indent] + '$ ' + line[l_indent:])
                    else:
                        updated_lines.append(line)
                    in_continuation = stripped.endswith('\\')
                else:
                    updated_lines.append(line)
                    in_continuation = False
            return f"{indent}```{lang}\n" + "\n".join(updated_lines) + f"\n{indent}```"
        return match.group(0)

    content = re.sub(r'^([ \t]*)```([a-zA-Z0-9_-]*)\s*\n(.*?)\n\1```', shell_prompt_replacer, content, flags=re.MULTILINE | re.DOTALL)

    # AUTOMATED SUPERFENCES ATTRIBUTE-LIST TRANSLATION ENGINE
    # pymdownx.superfences allows extended fence info strings like ```python hl_lines="2"
    # title="Code blocks"`, but Pandoc's markdown reader only recognises a bare language
    # name straight after the fence - anything trailing it isn't a valid info string, so
    # Pandoc gives up on the whole fence and falls back to a plain paragraph (fence
    # markers and attributes rendered as literal text). Rewrite it to Pandoc's own
    # attribute-list fence syntax (```{.python hl_lines="2" title="Code blocks"}`) so it's
    # parsed as a real, syntax-highlighted code block.
    def superfences_attr_replacer(match):
        indent, lang, attrs = match.group(1), match.group(2), match.group(3).strip()
        return f'{indent}```{{.{lang} {attrs}}}'

    content = re.sub(
        r'^([ \t]*)```[ \t]*([a-zA-Z][\w+-]*)[ \t]+(\S.*)$',
        superfences_attr_replacer,
        content,
        flags=re.MULTILINE
    )

    # THE IMAGE FILTER: Process light and dark mode asset rows line by line
    processed_lines = []
    for line in content.splitlines():
        if '#only-dark' in line: continue  
        if '#only-light' in line: line = line.replace('#only-light', '')  
        processed_lines.append(line)
    content = '\n'.join(processed_lines)

    project_vars = config.get('project', {})
    extra_vars = config.get('extra', {})
    vars_dict = {}
    if isinstance(project_vars, dict): vars_dict.update(project_vars)
    if isinstance(extra_vars, dict): vars_dict.update(extra_vars)
    if isinstance(project_vars, dict):
        proj_extra = project_vars.get('extra', {})
        if isinstance(proj_extra, dict): vars_dict.update(proj_extra)
    vars_dict.update(calculated_vars)
    
    docs_dir = config.get('docs_dir', 'docs')

    # Evaluate Template Conditional Rules
    lines = content.splitlines()
    filtered_lines = []
    state_stack = []
    in_raw = False

    for line in lines:
        # {% raw %}...{% endraw %} marks literal example syntax (e.g. showing
        # `{% if is_surrey %}` or `{{ word_count }}` in documentation) that must
        # NOT be treated as a real directive below - the same protection Jinja's
        # own raw block gives on the live website. Must run before the if/else/
        # endif matching, since that would otherwise happily "execute" an
        # example directive shown inside a code fence.
        has_raw_open = bool(re.search(r'\{%-?\s*raw\s*-?%\}', line))
        has_raw_close = bool(re.search(r'\{%-?\s*endraw\s*-?%\}', line))
        if in_raw or has_raw_open:
            clean_line = re.sub(r'\{%-?\s*raw\s*-?%\}', '', line)
            clean_line = re.sub(r'\{%-?\s*endraw\s*-?%\}', '', clean_line)
            if all(is_active for _, is_active in state_stack):
                filtered_lines.append(clean_line)
            # A block opened on this line stays protected on subsequent lines
            # until a (possibly later) line closes it; already being in_raw
            # only ends once this line's close is seen.
            in_raw = not has_raw_close
            continue

        if re.search(r'[{(]%\s*if\s+(\w+)\s*%', line):
            match = re.search(r'if\s+(\w+)', line)
            var_name = match.group(1)
            raw_val = vars_dict.get(var_name, False)
            condition_active = raw_val.lower() in ('true', '1', 'yes', 'on') if isinstance(raw_val, str) else bool(raw_val)
            state_stack.append(('if', condition_active))
            continue
        elif re.search(r'[{(]%\s*else\s*%', line):
            if state_stack and state_stack[-1][0] == 'if':
                state_stack[-1] = ('else', not state_stack[-1][1])
            continue
        elif re.search(r'[{(]%\s*endif\s*%', line):
            if state_stack: state_stack.pop()
            continue
        if not all(is_active for _, is_active in state_stack): continue
        filtered_lines.append(line)

    content = '\n'.join(filtered_lines)

    if is_index:
        content = re.sub(r'[<]![-\s]*.*?[- \s]*[>]', '', content, flags=re.DOTALL)
        content = re.sub(r'\[:material-file-pdf-box: PDF\].*$', '', content, flags=re.MULTILINE)
        def tag_unnumbered(match):
            line = match.group(0)
            if '{.' in line: return line.replace('{.', '{.hidden .unnumbered .unlisted .')
            elif '{' in line: return line.replace('{', '{.hidden .unnumbered .unlisted}')
            return f"{line} {{.hidden .unnumbered .unlisted}}"
        content = re.sub(r'^#{1,6}\s+.*$', tag_unnumbered, content, flags=re.MULTILINE)
        content = f'<div class="cover-page">\n{content}\n</div>\n'

    # INDENTATION PASSTHROUGH STATE MACHINE
    final_lines = content.splitlines()
    new_lines = []
    in_tab, in_admonition, in_gridcard, in_card_item = False, False, False, False
    gridcard_base_indent, tab_indent_level, adm_indent_level = 0, 0, 0
    adm_output_prefix = ''
    gridcard_output_prefix = ''
    gridcard_block_start = 0

    for line in final_lines:
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)
        if stripped == "":
            new_lines.append("")
            continue

        if not in_gridcard:
            grid_div_match = re.search(r'<div[^>]*class=["\']([^"\']*(?:grid\s+cards|cards\s+grid)[^"\']*)["\'][^>]*>', stripped, re.IGNORECASE)
            if grid_div_match:
                in_gridcard = True
                gridcard_base_indent = current_indent
                # Same rule as admonitions/tabs (see the matching comment further
                # below): Pandoc only treats this ::: fence as *continuing* the
                # enclosing list item (keeping items 1/2/3 in one <ol>) if it's
                # indented to the item's content column - the state machine below
                # builds the card's content already de-indented flat against the
                # card, so the whole block gets this prefix re-applied afterwards
                # rather than threading it through every intermediate line.
                gridcard_output_prefix = '   ' if gridcard_base_indent > 0 else ''
                gridcard_block_start = len(new_lines)
                style_match = re.search(r'style=["\']([^"\']*)["\']', line, re.IGNORECASE)
                style_attr = f' style="{style_match.group(1)}"' if style_match else ''
                new_lines.append(f"\n::: {{.gridcard-matrix{style_attr}}}\n")
                continue

        if in_gridcard:
            if stripped.startswith('</div>'):
                # Close whatever's still open inside the card, innermost first
                # (a tab or admonition can still be open here, since the card
                # markup often ends right after their content with no dedented
                # line in between to trigger their own natural close below).
                # Without this, their in_tab/in_admonition state leaks past
                # the card, wrongly closing the next thing that happens to
                # dedent far enough outside it and leaving a stray, unmatched
                # ::: behind as literal text.
                if in_admonition:
                    new_lines.append(f"\n{adm_output_prefix}:::\n")
                    in_admonition = False
                if in_tab:
                    new_lines.append("\n:::\n")
                    in_tab = False
                if in_card_item: new_lines.append("\n:::\n")
                in_gridcard, in_card_item = False, False
                new_lines.append("\n:::\n")
                if gridcard_output_prefix:
                    for idx in range(gridcard_block_start, len(new_lines)):
                        new_lines[idx] = "\n".join(
                            (gridcard_output_prefix + sub) if sub.strip() else sub
                            for sub in new_lines[idx].split("\n")
                        )
                continue
            card_strip_count = gridcard_base_indent + 4
            relative_line = line[card_strip_count:] if line.startswith(' ' * card_strip_count) else line.lstrip()
            rel_stripped = relative_line.lstrip()
            if rel_stripped.startswith('-') and not rel_stripped.startswith('***'):
                if in_card_item: new_lines.append("\n:::\n")
                in_card_item = True
                new_lines.append("\n::: {.gridcard-item}\n")
                title_text = re.sub(r'^-\s+', '', rel_stripped)
                title_text = re.sub(r'\{\s*[^}]*\}', '', title_text)
                title_text = title_text.strip()
                new_lines.append(f'::: {{.gridcard-title}}\n{title_text}\n:::\n')
                continue
            line, stripped = relative_line, rel_stripped
            current_indent = len(line) - len(stripped)

        if in_tab and not stripped.startswith('==='):
            if current_indent <= tab_indent_level:
                if in_admonition:
                    new_lines.append("\n:::\n")
                    in_admonition = False
                new_lines.append("\n:::\n")
                in_tab = False

        if in_admonition and not in_tab and not stripped.startswith(('!!!', '???')):
            if current_indent < adm_indent_level + 4:
                in_admonition = False
                new_lines.append(f"\n{adm_output_prefix}:::\n")

        if stripped.startswith('==='):
            if in_tab:
                if in_admonition:
                    new_lines.append("\n:::\n")
                new_lines.append("\n:::\n")
            match = re.search(r'^===\s*["\'\u201c\u2018]?(.*?)["\'\u201d\u2019]?\s*$', stripped)
            tab_title = match.group(1).strip() if match else "Tab"
            tab_indent_level = current_indent
            in_tab, in_admonition = True, False
            new_lines.append(f'\n::: {{.tabbox title="{tab_title}"}}')
            continue

        if not in_tab and stripped.startswith(('!!!', '???')):
            if in_admonition: new_lines.append(f"\n{adm_output_prefix}:::\n")
            parts = stripped.split(maxsplit=2)
            adm_type = parts[1].lower() if len(parts) > 1 else "note"
            adm_title = parts[2].strip('"\'') if len(parts) > 2 else adm_type.capitalize()
            adm_indent_level = current_indent
            # Nesting an admonition inside a list item matters for two reasons: (1)
            # visually, it should render indented under that item, matching the live
            # site; (2) numerically, Pandoc only treats content as *continuing* the
            # list (keeping items 1/2/3 in one <ol>) if it's indented to the item's
            # content column - otherwise it starts a new <ol start="2">, which
            # WeasyPrint then ignores, rendering every split-off list as "1.". Pandoc
            # only recognises a ::: fence as nested content at exactly that column
            # (3 spaces, matching a single-digit "N. " marker) - going deeper, e.g.
            # to match this doc's own 4-space code-fence indent convention, makes
            # Pandoc treat the ::: fence as literal paragraph text instead.
            adm_output_prefix = '   ' if adm_indent_level > 0 else ''
            adm_icon_token = resolve_admonition_icon_token(adm_type)
            adm_title_text = f"{adm_icon_token} {adm_title}" if adm_icon_token else adm_title
            new_lines.append(f"\n{adm_output_prefix}::: {{.admonition .{adm_type}}}")
            new_lines.append(f"{adm_output_prefix}::: {{.admonition-title}}\n{adm_output_prefix}{adm_title_text}\n{adm_output_prefix}:::\n")
            in_admonition = True
            continue

        if in_tab:
            strip_count = tab_indent_level + 4
            content_line = line[strip_count:] if len(line) >= strip_count and line.startswith(' ' * strip_count) else line.lstrip()
            content_stripped = content_line.lstrip()
            if content_stripped.startswith(('!!!', '???')):
                if in_admonition: new_lines.append(f"\n{adm_output_prefix}:::\n")
                parts = content_stripped.split(maxsplit=2)
                adm_type = parts[1].lower() if len(parts) > 1 else "note"
                adm_title = parts[2].strip('"\'') if len(parts) > 2 else adm_type.capitalize()
                # See the matching comment above: Pandoc requires this ::: fence at
                # exactly a 3-space indent to be recognised as nested list-item
                # content (rather than as flattened column-0 or this doc's own
                # 4-space code-fence convention, both of which break either the
                # list numbering or the fence recognition itself).
                adm_indent_level = len(content_line) - len(content_stripped)
                adm_output_prefix = '   ' if adm_indent_level > 0 else ''
                adm_icon_token = resolve_admonition_icon_token(adm_type)
                adm_title_text = f"{adm_icon_token} {adm_title}" if adm_icon_token else adm_title
                new_lines.append(f"\n{adm_output_prefix}::: {{.admonition .{adm_type}}}")
                new_lines.append(f"{adm_output_prefix}::: {{.admonition-title}}\n{adm_output_prefix}{adm_title_text}\n{adm_output_prefix}:::\n")
                in_admonition = True
                continue
            if in_admonition:
                content_indent = len(content_line) - len(content_stripped)
                if content_indent < adm_indent_level + 4 and not content_stripped.startswith(('!!!', '???')):
                    in_admonition = False
                    new_lines.append(f"\n{adm_output_prefix}:::\n")
                if in_admonition:
                    new_lines.append(adm_output_prefix + (content_line[adm_indent_level + 4:] if content_line.startswith(' ' * (adm_indent_level + 4)) else content_stripped))
                else:
                    new_lines.append(content_line)
            else:
                new_lines.append(content_line)
        elif in_admonition:
            new_lines.append(adm_output_prefix + (line[adm_indent_level + 4:] if line.startswith(' ' * (adm_indent_level + 4)) else stripped))
        else:
            new_lines.append(line)

    if in_tab: new_lines.append("\n:::\n")
    if in_admonition: new_lines.append("\n:::\n")

    # FENCED CODE BLOCK LAZY-CONTINUATION GUARD
    # Pandoc's markdown reader only lets a fenced code block interrupt an
    # immediately preceding text line (list item text, tab/admonition content, etc.)
    # when the fence has zero indentation. Any indented fence - unavoidable for code
    # nested inside list items, tabs, or admonitions - gets swallowed as a lazy
    # continuation of the prior line when there's no blank line before it, so it
    # renders as inline text instead of a code block. Force a separating blank line
    # before every indented fence opener that doesn't already have one.
    guarded_lines = []
    in_fence, fence_char, fence_len = False, None, 0
    for line in new_lines:
        stripped = line.strip()
        if not in_fence:
            fence_match = re.match(r'^(`{3,}|~{3,})', stripped)
            if fence_match:
                indent = len(line) - len(line.lstrip())
                if indent > 0 and guarded_lines and guarded_lines[-1].strip() != "":
                    guarded_lines.append("")
                in_fence = True
                fence_char = fence_match.group(1)[0]
                fence_len = len(fence_match.group(1))
        else:
            close_match = re.match(r'^(`{3,}|~{3,})\s*$', stripped)
            if close_match and close_match.group(1)[0] == fence_char and len(close_match.group(1)) >= fence_len:
                in_fence = False
        guarded_lines.append(line)
    new_lines = guarded_lines

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

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

    # PDF equivalent of the website's {{ nav_snippet() }} macro (see
    # macros.py): reuses the same _get_nav_snippet() helper directly, since
    # it's already loaded as a real module here - no need to duplicate the
    # extraction logic the way reference_style's CSS had to be, since here
    # both outputs just need the identical extracted text.
    nav_snippet_text = macros_module._get_nav_snippet() if macros_module and hasattr(macros_module, '_get_nav_snippet') else ''

    # Each nav page's own chapter number ("7") or appendix letter ("A"),
    # keyed by its docs_dir-relative path - needed for figure/table caption
    # numbering (see preprocess_markdown()'s chapter_id parameter). Mirrors
    # macros.py's own _heading_start_counts()/_appendix_letters(), reusing
    # its _page_is_appendix()/_count_top_level_headings() helpers directly
    # (already loaded above) rather than re-implementing the same nav walk
    # a third time.
    chapter_identifiers = {}
    if macros_module and hasattr(macros_module, '_page_is_appendix') and hasattr(macros_module, '_count_top_level_headings'):
        numeric_chapter = 0
        appendix_index = 0
        for f in md_files:
            full_path = os.path.join(docs_dir, f)
            if macros_module._page_is_appendix(full_path):
                appendix_index += 1
                chapter_identifiers[f] = chr(ord('A') + appendix_index - 1)
            elif macros_module._count_top_level_headings(full_path) > 0:
                numeric_chapter += 1
                chapter_identifiers[f] = str(numeric_chapter)

    caption_state = {}

    theme_section = project_section.get('theme', {}) if isinstance(project_section, dict) else config.get('theme', {})
    font_section = theme_section.get('font', {}) if isinstance(theme_section, dict) else {}
    main_font, mono_font = "Inter", "JetBrains Mono"
    if isinstance(font_section, dict):
        main_font = font_section.get('text', main_font)
        mono_font = font_section.get('code', mono_font)

    copyright_text = project_section.get('copyright') or config.get('copyright') or "Copyright 2026"
    site_name_text = project_section.get('site_name') or config.get('site_name') or ""

    icon_dirs = discover_icon_dirs(config)
    icon_registry = build_icon_registry(icon_dirs)

    temp_build_dir = "pdf_build_workspace"
    os.makedirs(temp_build_dir, exist_ok=True)
    
    # Global state tracker maps unfragmented safe tokens to their Base64 payloads
    global_placeholder_map = {}
    mermaid_state = {'count': 0}

    print("🧹 Preprocessing markdown file layouts...")
    processed_paths = []
    for path in valid_paths:
        safe_name = path.replace('/', '_').replace('\\', '_')
        temp_out_path = os.path.join(temp_build_dir, safe_name)
        is_index = "index.md" in os.path.basename(path).lower()
        rel_path = os.path.normpath(os.path.relpath(path, docs_dir)).replace('\\', '/')
        chapter_id = chapter_identifiers.get(rel_path)
        preprocess_markdown(path, temp_out_path, config, calculated_vars, icon_registry, global_placeholder_map, temp_build_dir, mermaid_state, page_anchor_map, nav_snippet_text, is_index=is_index, chapter_id=chapter_id, caption_state=caption_state)
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

    toc_trigger_path = os.path.join(temp_build_dir, "toc_trigger_temp.md")
    with open(toc_trigger_path, "w", encoding="utf-8") as f:
        f.write("\n# Table of Contents {.unnumbered .unlisted}\n\n<div class=\"page-break\"></div>\n")

    compiled_paths = [processed_paths[0], toc_trigger_path] + processed_paths[1:] if "index.md" in os.path.basename(valid_paths[0]).lower() else [toc_trigger_path] + processed_paths

    output_pdf = "docs/site_documentation.pdf"

    temp_master_md = os.path.join(temp_build_dir, "_temp_master_compiled.md")
    with open(temp_master_md, "w", encoding="utf-8") as out_f:
        for chunk_path in compiled_paths:
            with open(chunk_path, "r", encoding="utf-8") as in_f:
                out_f.write(in_f.read() + "\n\n")

    lua_table_entries = []
    for token_key, b64_payload in global_placeholder_map.items():
        lua_table_entries.append(f'  ["{token_key}"] = "{b64_payload}"')

    lua_icon_db_string = "local icon_db = {\n" + ",\n".join(lua_table_entries) + "\n}\n\n"

    math_dir = os.path.abspath(os.path.join(temp_build_dir, "math_diagrams"))
    os.makedirs(math_dir, exist_ok=True)
    tex2svg_script = os.path.abspath(os.path.join("tools", "mathjax", "tex2svg.js"))
    mathjax_available = os.path.exists(os.path.join("tools", "mathjax", "node_modules", "mathjax-full"))

    lua_filter_path = os.path.join(temp_build_dir, "tabbox_filter.lua")
    with open(lua_filter_path, "w", encoding="utf-8") as f:
        f.write(lua_icon_db_string)
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
            "function Div(el)\n"
            "  if el.classes:includes('tabbox') then\n"
            "    local title = el.attributes['title'] or 'Tab'\n"
            "    local header = pandoc.Div({pandoc.Plain({pandoc.Str(title)})}, {class='tabbox-header'})\n"
            "    local body = pandoc.Div(el.content, {class='tabbox-body'})\n"
            "    el.content = {header, body}\n"
            "    el.classes = {'tabbox-container'}\n"
            "    return el\n"
            "  end\n"
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
            "function Note(el)\n"
            "  local html = pandoc.write(pandoc.Pandoc(el.content), 'html')\n"
            "  html = html:gsub('^%s*<p>', ''):gsub('</p>%s*$', '')\n"
            "  return pandoc.RawInline('html', '<span class=\"pdf-footnote\">' .. html .. '</span>')\n"
            "end\n\n"
            f"local mathjax_available = {'true' if mathjax_available else 'false'}\n"
            f"local math_dir = \"{math_dir}\"\n"
            f"local tex2svg_script = \"{tex2svg_script}\"\n"
            "local math_counter = 0\n\n"
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
            "function Str(el)\n"
            "  if icon_db[el.text] then\n"
            "    return pandoc.RawInline('html', '<img class=\"twemoji\" src=\"data:image/svg+xml;base64,' .. icon_db[el.text] .. '\" />')\n"
            "  end\n"
            "  return nil\n"
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
        font-size: 10pt !important;
        color: #555555 !important;
        vertical-align: bottom !important;
        border-bottom: 1px solid #e2e8f0 !important;
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
        font-size: 10pt !important;
        color: #555555 !important;
        vertical-align: bottom !important;
        border-bottom: 1px solid #e2e8f0 !important;
        padding-bottom: 8px !important;
        margin-bottom: 3mm !important;
        width: 50% !important;
        text-align: right !important;
    }
    @bottom-center { content: none !important; }
    @bottom-left {
        content: "__COPYRIGHT__" !important;
        font-family: "__MAIN_FONT__", sans-serif !important;
        font-size: 10pt !important;
        color: #555555 !important;
        vertical-align: top !important;
        border-top: 1px solid #e2e8f0 !important;
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
        font-size: 10pt !important;
        color: #555555 !important;
        vertical-align: top !important;
        border-top: 1px solid #e2e8f0 !important;
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
/* Bound inside <table> itself, so it can never be separated from the start
   of the table across a page break (unlike a plain preceding paragraph).
   caption-side itself isn't set here - it's added per-table, only for
   captions that actually asked to be shown at the top (see
   table_caption_replacer()/prepend_table_ids below) - Pandoc's own
   default (bottom) applies to any table caption that didn't. */
table caption {
    text-align: center !important;
    font-style: italic !important;
    margin-bottom: 8px !important;
    page-break-after: avoid !important;
    break-after: avoid-page !important;
}
table th { background-color: rgba(0, 0, 0, 0.1) !important; font-weight: bold !important; }
table th, table td {
    padding: 8px 12px !important;
    border-top: 0.25pt solid #555555 !important;
    border-bottom: 0.25pt solid #555555 !important;
    border-left: none !important; border-right: none !important;
}
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
   printed book), instead of Pandoc's default of collecting every footnote in
   the whole document into one section at the very end of the PDF. The Lua
   filter replaces each Note with this inline span at its reference point. */
.pdf-footnote {
    float: footnote !important;
    font-size: 9pt !important;
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
    color: #000000 !important; page-break-after: avoid !important; break-after: avoid !important;
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

/* #dddddd is another 5% darker than #e9e9e9 (itself 5% darker than
   #f5f5f5, --md-code-bg-color - the website's shading for both inline
   code and code blocks; see docs/stylesheets/extra.css / the Zensical
   default theme), kept identical between inline code and code blocks here. */
pre, code { font-family: "__MONO_FONT__", monospace !important; }
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
                                     .replace("__PDF_MARGIN_LEFT__", pdf_margin_left)

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
        reference_style_css = """
p.reference {
    padding-left: 1.27cm !important;
    text-indent: -1.27cm !important;
}
p.reference + p.reference {
    margin-top: 2em !important;
}
"""
    else:
        reference_style_css = """
p.reference + p.reference {
    margin-top: -0.8em !important;
}
"""

    # PDF equivalent of extra.css's ".md-typeset p.acronym + p.acronym" rule
    # (see docs/acronyms.md) - same reasoning as reference_style_css above:
    # Pandoc's HTML output has no ".md-typeset" wrapper, so this plain
    # ".acronym" selector is what actually applies the tight spacing here.
    acronym_style_css = """
p.acronym + p.acronym {
    margin-top: -0.8em !important;
}
"""

    # PDF equivalent of extra.css's ".md-typeset p.glossary + p.glossary" rule
    # (see docs/glossary.md) - same reasoning as reference_style_css above.
    glossary_style_css = """
p.glossary + p.glossary {
    margin-top: -0.8em !important;
}
"""

    # Every table caption id that requested the top position (either a
    # table-caption block with an explicit "| <", or a plain caption using
    # this template's original default - see table_caption_replacer() /
    # caption_state above), collected across every page's preprocessing
    # pass. table caption itself (in the static part of this stylesheet,
    # above) deliberately doesn't set caption-side at all, so Pandoc's own
    # default (bottom) applies to any table caption not listed here.
    caption_style_css = "\n".join(
        f'table caption[id="{table_id}"] {{ caption-side: top !important; }}'
        for table_id in sorted(caption_state.get('prepend_table_ids', set()))
    )

    with open(temp_compiled_css, "w", encoding="utf-8") as f:
        f.write(cleaned_original_css + "\n\n" + final_css_payload + "\n\n" + reference_style_css + "\n\n" + acronym_style_css + "\n\n" + glossary_style_css + "\n\n" + caption_style_css)

    cmd = [
        "pandoc",
        os.path.join(temp_build_dir, "_temp_master_compiled.md"),                
        "-o", output_pdf,
        "--pdf-engine=weasyprint",
        "--pdf-engine-opt=-q",
        "--mathjax",
        f"--lua-filter={lua_filter_path}",
        "-f", "markdown",
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