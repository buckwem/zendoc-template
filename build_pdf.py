# Copyright (c) 2025-2026 Mark Buckwell and contributors
# SPDX-License-Identifier: MIT

"""Builds docs/site_documentation.pdf from this project's own zensical.toml.

The actual Pandoc/WeasyPrint pipeline (HTML fixups, Lua filter, CSS,
Mermaid/icon handling) now lives in zendoc.pdf (see zendoc-extension#96) -
this script is left with only what's specific to this template: the cover
page's {WORDCOUNT}/{REPOURL}/{RELEASE}/{{ site_name }} markers (see
index.md), the word count itself (see "Word count" in customise.md), and
loading this project's own docs/stylesheets/extra.css and print.css into
zendoc.pdf.build_pdf()'s extra_css.

A project with no such cover-page markers of its own can just run
`zendoc pdf` directly instead - see zendoc.pdf's own documentation."""

import base64
import json
import os
import re
import shutil
import sys
import urllib.parse
import urllib.request

import zensical.config as zensical_config
from zensical.markdown.render import render as zensical_render

from zendoc.pdf import Page, PdfBuildError, build_pdf
from zendoc.pdf.icons import build_icon_registry, discover_icon_dirs
from zendoc.pdf.mermaid import render_mermaid_diagram


def _flatten_nav(nav_items):
    """Walks Zensical's own already-resolved nav tree (parse_config()'s
    nav, not zensical.toml's raw structure) into an ordered list of real
    pages only - a nav group heading (url is None, only children)
    contributes just its descendants, not an entry of its own."""
    pages = []
    for item in nav_items:
        if item.get('url'):
            pages.append(item)
        pages.extend(_flatten_nav(item.get('children') or []))
    return pages


def _strip_front_matter(text):
    """Removes a leading YAML front matter block, matching what
    zensical.markdown.render.render() already does internally before
    conversion - used here so compute_pdf_word_count() never counts a
    page's own front matter keys as prose."""
    if not text.startswith('---'):
        return text
    parts = text.split('---', 2)
    return parts[2] if len(parts) >= 3 else text


def compute_pdf_word_count(texts):
    """Rough prose word count across the given already-front-matter-
    stripped markdown source texts: strips fenced/HTML code blocks
    (including a ```mermaid fence - a diagram's own source was never
    "content"), inline code, HTML comments/tags, and markdown link/image/
    emphasis syntax before splitting on whitespace. Used to fill in the
    cover page's {WORDCOUNT} marker (see index.md); excludes the cover page
    itself and any page flagged exclude_from_word_count (see "Word count"
    in customise.md)."""
    total_words = 0
    for text in texts:
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


def _css_escape_content_string(text):
    """Collapses text to a single line and escapes it for safe use inside a
    CSS `content: "..."` string - zendoc.pdf.css.build_css() substitutes
    copyright_text/site_name directly into such a string without escaping
    it itself (its own docs note both "should already be CSS-content-
    string-safe"), and zensical.toml's copyright is a triple-quoted string
    that commonly spans multiple lines - passed through unescaped, a raw
    newline or `"` breaks the generated CSS rule outright, silently
    dropping the whole running header/footer entry."""
    clean_text = text.strip().replace('\n', ' ').replace('\r', ' ')
    sanitized_text = clean_text.replace('&copy;', '©').replace('&#169;', '©')
    escaped_text = "".join(f"\\{ord(char):04X} " if ord(char) > 127 else char for char in sanitized_text)
    return escaped_text.replace('"', '\\"')


def _find_mmdc_bin():
    """Path to this project's own local mermaid-cli install (see "Mermaid
    diagrams" in installtooling.md), or None if it isn't installed - a
    diagram is simply left unrendered in that case, rather than failing the
    whole build."""
    mmdc_bin = os.path.abspath(os.path.join("tools", "mermaid", "node_modules", ".bin", "mmdc"))
    return mmdc_bin if os.path.exists(mmdc_bin) else None


def _load_extra_css(docs_dir):
    """Loads this project's own docs/stylesheets/extra.css and print.css,
    inlining any relative url(...) reference as a base64 data: URI (the
    compiled CSS zendoc.pdf.build_pdf() writes lives in a different,
    temporary directory, where the original relative paths wouldn't
    resolve) and stripping @charset/user-select rules WeasyPrint doesn't
    need. Passed to build_pdf()'s own extra_css parameter, layered
    underneath the CSS it generates - see "Screenshots"/"References and
    bibliography" in customise.md for why a few rules need a PDF-specific
    copy at all (Pandoc's HTML has no .md-typeset wrapper for extra.css's
    own rules to match against)."""
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

    original_css_content = ""
    for css_src in [os.path.join(docs_dir, "stylesheets", "extra.css"), os.path.join(docs_dir, "stylesheets", "print.css")]:
        if os.path.exists(css_src):
            with open(css_src, "r", encoding="utf-8") as f:
                original_css_content += inline_css_urls(f.read(), os.path.dirname(css_src)) + "\n"

    cleaned = re.sub(r'@charset[^;{]*(\{.*?\}|;)', '', original_css_content, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'^.*user-select.*$\n?', '', cleaned, flags=re.MULTILINE | re.IGNORECASE)
    return cleaned


def main():
    if not os.path.exists('zensical.toml'):
        print("❌ Error: zensical.toml not found in the current directory.")
        sys.exit(1)

    config = zensical_config.parse_config('zensical.toml')

    nav_pages = _flatten_nav(config.get('nav') or [])
    if not nav_pages:
        print("❌ Error: No 'nav' section found in zensical.toml.")
        sys.exit(1)

    docs_dir = config.get('docs_dir') or 'docs'
    valid_nav_pages = [p for p in nav_pages if os.path.exists(os.path.join(docs_dir, p['url']))]
    if not valid_nav_pages:
        print("❌ Error: No valid markdown files found.")
        sys.exit(1)

    extra = config.get('extra') or {}
    theme = config.get('theme') or {}
    font = theme.get('font') or {}
    admonition_icon_config = (theme.get('icon') or {}).get('admonition') or {}
    repo_url = config.get('repo_url') or ''
    copyright_text = config.get('copyright') or "Copyright 2026"
    site_name_text = config.get('site_name') or ''
    # Escaped copies for the running header/footer CSS (see
    # _css_escape_content_string()) - kept separate from the raw values
    # above, which the {{ site_name }} cover-page marker substitution below
    # still needs unescaped (it's substituted into HTML, not CSS).
    copyright_css_text = _css_escape_content_string(copyright_text)
    site_name_css_text = _css_escape_content_string(site_name_text)

    icon_registry = build_icon_registry(discover_icon_dirs(docs_dir))

    # Scratch space for Mermaid/math intermediate files, outside docs_dir so
    # it's never mistaken for real content - removed again in main()'s own
    # finally block below, the same as the old pipeline's temp_build_dir.
    workspace_dir = os.path.abspath("pdf_build_workspace")
    os.makedirs(workspace_dir, exist_ok=True)

    mmdc_bin = _find_mmdc_bin()
    mermaid_state = {'count': 0}
    render_mermaid = None
    if mmdc_bin:
        mermaid_dir = os.path.join(workspace_dir, "mermaid_diagrams")

        def render_mermaid(source):
            mermaid_state['count'] += 1
            return render_mermaid_diagram(source, mmdc_bin, mermaid_dir, mermaid_state['count'])

    # zendoc.pdf.lua.build_lua_filter()'s math_dir "must already exist or be
    # creatable by the caller" (its own SVGs are written by the Lua filter
    # itself via io.open(), which doesn't create directories) - unlike
    # render_mermaid_diagram()'s output_dir, which creates itself.
    math_dir = os.path.join(workspace_dir, "math_diagrams")
    os.makedirs(math_dir, exist_ok=True)
    tex2svg_script = os.path.abspath(os.path.join("tools", "mathjax", "tex2svg.js"))
    mathjax_available = os.path.exists(os.path.join("tools", "mathjax", "node_modules", "mathjax-full"))

    print("🧹 Rendering pages via Zensical...")
    pages = []
    page_source_text = {}
    for nav_page in valid_nav_pages:
        docs_rel_path = nav_page['url']
        full_path = os.path.join(docs_dir, docs_rel_path)
        with open(full_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
        result = zensical_render(raw_text, docs_rel_path, docs_rel_path)
        meta = result['meta']
        pages.append(
            Page(
                docs_rel_path=docs_rel_path,
                html=result['content'],
                is_index=bool(nav_page.get('is_index')),
                is_appendix=bool(meta.get('is_appendix', False)),
            )
        )
        page_source_text[docs_rel_path] = (raw_text, bool(meta.get('exclude_from_word_count', False)))

    # Fill in the cover page's {WORDCOUNT}/{REPOURL}/{RELEASE} markers (see
    # index.md), if present - PDF-only cover-page behaviour with no
    # equivalent in zendoc.pdf itself (see zendoc-extension#96).
    if pages and pages[0].is_index and len(pages) > 1:
        cover = pages[0]
        cover_html = cover.html
        if '{WORDCOUNT}' in cover_html:
            # Word count of the actual content pages: everything except the
            # cover page itself, and any page opted out via
            # exclude_from_word_count - e.g. References, Acronyms,
            # Glossary, Originality & AI Use.
            counted_texts = [
                _strip_front_matter(raw_text)
                for path, (raw_text, excluded) in page_source_text.items()
                if path != cover.docs_rel_path and not excluded
            ]
            word_count = compute_pdf_word_count(counted_texts)
            cover_html = cover_html.replace('{WORDCOUNT}', f'{word_count:,}')
        if '{REPOURL}' in cover_html:
            cover_html = cover_html.replace('{REPOURL}', repo_url)
        if '{RELEASE}' in cover_html:
            # Unlike {WORDCOUNT}/{REPOURL}, which are always locally
            # computable, most forks of this template will never have a
            # published release, so an empty result drops the whole line
            # rather than leaving a bare "Release: " label behind.
            release_tag = get_latest_release_tag(repo_url)
            if release_tag:
                cover_html = cover_html.replace('{RELEASE}', release_tag)
            else:
                cover_html = re.sub(r'^.*\{RELEASE\}.*\n?', '', cover_html, flags=re.MULTILINE)
        if '{{ site_name }}' in cover_html:
            # zendoc.pdf never evaluates Jinja, so the exact same literal
            # "{{ site_name }}" text used for the website's macro variable
            # can just be substituted directly here too - one line in
            # index.md works for both outputs, no separate marker.
            cover_html = cover_html.replace('{{ site_name }}', site_name_text)
        cover.html = cover_html

    extra_css = _load_extra_css(docs_dir)
    output_path = os.path.join(docs_dir, "site_documentation.pdf")

    print("🚀 Building PDF via zendoc.pdf...")
    try:
        build_pdf(
            pages,
            output_path,
            docs_dir=docs_dir,
            extra_css=extra_css,
            repo_url=repo_url,
            admonition_icon_config=admonition_icon_config,
            icon_registry=icon_registry,
            render_mermaid=render_mermaid,
            main_font=font.get('text') or "Inter",
            mono_font=font.get('code') or "JetBrains Mono",
            copyright_text=copyright_css_text,
            site_name=site_name_css_text,
            page_size=extra.get('pdf_page_size') or "A4",
            margin_top=extra.get('pdf_margin_top') or "2cm",
            margin_right=extra.get('pdf_margin_right') or "2cm",
            margin_bottom=extra.get('pdf_margin_bottom') or "2cm",
            margin_left=extra.get('pdf_margin_left') or "2cm",
            header_footer_font_size=extra.get('pdf_header_footer_font_size') or "10pt",
            header_footer_color=extra.get('pdf_header_footer_color') or "#555555",
            header_footer_divider_color=extra.get('pdf_header_footer_divider_color') or "#e2e8f0",
            reference_style_global=str(extra.get('reference_style') or 'european').strip().lower() == 'global',
            reference_spacing_european=extra.get('reference_spacing_european') or "-0.8em",
            reference_indent_global=extra.get('reference_indent_global') or "1.27cm",
            reference_spacing_global=extra.get('reference_spacing_global') or "2em",
            heading_numbering_enabled=bool(extra.get('heading_numbering', True)),
            mathjax_available=mathjax_available,
            math_dir=math_dir,
            tex2svg_script=tex2svg_script,
        )
    except PdfBuildError as error:
        print(f"\n❌ Error: {error}")
        if error.stderr:
            print(error.stderr)
        sys.exit(1)
    finally:
        shutil.rmtree(workspace_dir, ignore_errors=True)

    print(f"\n🎉 Success! The document compiled cleanly. PDF ready at: {output_path}")


if __name__ == "__main__":
    main()
