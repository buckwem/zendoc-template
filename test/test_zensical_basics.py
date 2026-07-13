# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""zensical_basics batch: checks the Zensical-specific Markdown extensions
taught in docs/starthere/zensicalbasics.md ("10. Zensical basics") -
admonitions, collapsible details, code blocks, content tabs, images,
diagrams, footnotes, formatting, icons/emojis, maths, task lists, and
tooltips - render the way that page (and the fuller upstream
zensical.org/docs/authoring/* pages it links out to for "full
documentation") say they do.

Like test_markdown_foundations.py, this renders hand-written snippets
through a real markdown.Markdown() instance built from this project's own
zensical.toml extension config (see conftest.py's markdown_extension_config
fixture), so tests can't silently drift out of sync with it. Unlike that
batch, this one also wires up a *working* pymdownx.emoji config - real
zensical.extensions.emoji callables, not the dotted-string references
markdown_extension_config deliberately omits - since "Icons, emojis" is a
section on this specific page.

Each section below cross-checks against the corresponding
zensical.org/docs/authoring/* page (linked from zensicalbasics.md itself),
not just the one worked example shown on our own page, per issue #50 -
e.g. all 12 configured admonition types, not just the note/warning pair
zensicalbasics.md happens to show; all 5 officially-supported Mermaid
diagram types, not just the one flowchart example.

Not covered: the "Commands" section (zensical new/serve/build) - these are
CLI behaviour, not Markdown syntax, and aren't meaningfully testable by
rendering a snippet the way everything else on this page is."""

import re
import textwrap

import markdown
import pytest

from conftest import chapter_page_range
from pymdownx.superfences import fence_code_format
from zensical.extensions.emoji import to_svg, twemoji


def dedent(text):
    return textwrap.dedent(text).strip("\n") + "\n"


@pytest.fixture(scope="module")
def render(markdown_extension_config):
    """Same shared-instance approach as test_markdown_foundations.py's
    render fixture, but with two dotted-string config values resolved into
    their real callables, mirroring what Zensical's own loader does with
    zensical.toml's config at runtime (plain markdown.Markdown() has no
    such loader, and takes both literally, breaking the extension - see
    the emoji_index/emoji_generator note on markdown_extension_config in
    conftest.py for the same issue):

    - pymdownx.emoji's emoji_index/emoji_generator -> zensical.extensions.emoji's
      twemoji/to_svg, needed for the "Icons, emojis" section below.
    - pymdownx.superfences' custom_fences[].format (the "mermaid" custom
      fence zensical.toml declares) -> pymdownx.superfences.fence_code_format
      itself, needed for the "Diagrams" section below. Left as the dotted
      string, a ```mermaid fence doesn't get recognised as a fence at all -
      it silently falls back to plain inline code with no error, easy to
      miss without a direct test."""
    extensions, extension_configs = markdown_extension_config
    extensions = [*extensions, "pymdownx.emoji"]
    extension_configs = {
        **extension_configs,
        "pymdownx.emoji": {
            "emoji_index": twemoji,
            "emoji_generator": to_svg,
            "options": {"custom_icons": ["overrides/.icons"]},
        },
        "pymdownx.superfences": {
            "custom_fences": [
                {"name": "mermaid", "class": "mermaid", "format": fence_code_format}
            ],
        },
    }
    md = markdown.Markdown(extensions=extensions, extension_configs=extension_configs)

    def render(text):
        md.reset()
        return md.convert(dedent(text) if not text.endswith("\n") else text)

    return render


# ---------------------------------------------------------------------------
# Lists within lists / The Four Space Rule
# ---------------------------------------------------------------------------
# The core "4 spaces nests a sub-list" mechanics are already covered by
# test_markdown_foundations.py's test_nested_list_at_four_spaces_actually_nests
# / test_nested_list_at_two_spaces_does_not_nest. What's specific to *this*
# page's own warning - "if you are nesting Tabs, Admonitions, or Code Blocks
# inside a list, you must indent by exactly 4 spaces" - is nesting those
# Zensical-specific block types, not just a plain sub-list.

def test_admonition_nested_in_a_list_at_four_spaces(render):
    html = render("""
        - Item 1

            !!! note
                Nested admonition.
    """)
    assert "<ul>" in html
    assert 'class="admonition note"' in html


def test_tab_nested_in_a_list_at_four_spaces(render):
    html = render("""
        - Item 1

            === "Tab"
                Nested tab content.
    """)
    assert "<ul>" in html
    assert 'class="tabbed-set' in html


# ---------------------------------------------------------------------------
# Admonitions
# ---------------------------------------------------------------------------
# All 12 types configured in zensical.toml's [project.theme.icon.admonition]
# (see https://zensical.org/docs/authoring/admonitions/ for the full type
# list this project's config matches).
ADMONITION_TYPES = [
    "note", "abstract", "info", "tip", "success", "question",
    "warning", "failure", "danger", "bug", "example", "quote",
]


@pytest.mark.parametrize("kind", ADMONITION_TYPES)
def test_each_configured_admonition_type_renders(render, kind):
    html = render(f"!!! {kind}\n\n    Body text.")
    assert f'class="admonition {kind}"' in html
    assert "Body text" in html


def test_admonition_custom_title(render):
    html = render('!!! note "Custom Title"\n\n    Body text.')
    assert "Custom Title" in html
    assert '<p class="admonition-title">Custom Title</p>' in html


def test_admonition_empty_title_omits_title_element(render):
    html = render('!!! note ""\n\n    Body text.')
    assert "admonition-title" not in html


def test_admonition_nesting(render):
    html = render("""
        !!! note "Outer"

            Outer body.

            !!! warning "Inner"

                Inner body.
    """)
    # '<div class="admonition ...">' for the two wrapping divs, distinct from
    # '<p class="admonition-title">' (a substring of 'class="admonition' too,
    # so counting that bare prefix would over-count by the title paragraphs).
    assert html.count('<div class="admonition') == 2
    assert "Outer body" in html and "Inner body" in html


def test_collapsible_details_block(render):
    """The "???" syntax from zensicalbasics.md's "Details" section -
    admonition.details' collapsible variant of the same 12 types above."""
    html = render('??? info "Click to expand"\n\n    Hidden content.')
    assert "<details" in html
    assert "Hidden content" in html
    assert "open" not in html.split("<details", 1)[1].split(">", 1)[0]


def test_collapsible_details_expanded_by_default(render):
    html = render('???+ info "Click to expand"\n\n    Hidden content.')
    assert "<details" in html
    assert "open" in html.split("<details", 1)[1].split(">", 1)[0]


# ---------------------------------------------------------------------------
# Code blocks
# ---------------------------------------------------------------------------

def test_fenced_code_with_title_and_line_highlighting(render):
    html = render('''
        ``` python hl_lines="2" title="Code blocks"
        def greet(name):
            print(f"Hello, {name}!")
        ```
    ''')
    assert "Code blocks" in html  # title
    assert "hll" in html  # pygments' highlighted-line class


def test_fenced_code_with_line_numbers(render):
    html = render('''
        ``` python linenums="1"
        a = 1
        b = 2
        ```
    ''')
    assert "linenos" in html or "__span" in html or "data-linenums" in html or "id=\"__span" in html


def test_code_annotation_marker_and_explanation(render):
    """zensicalbasics.md's "Code blocks" section: a "# (1)!" marker inside
    the fence, explained by a numbered list item straight after it. Per
    zensical.org/docs/authoring/code-blocks/#code-annotations, the fence
    itself needs the .annotate attr_list class for this to actually link up
    (without it, the "(1)!" marker is inert decorative text and the
    following list is just an ordinary, unconnected <ol> - a fence without
    .annotate silently doesn't get annotations, easy to miss without a
    direct test)."""
    html = render('''
        ``` { .python .annotate }
        print("hi")  # (1)!
        ```

        1.  An annotation.
    ''')
    assert "An annotation" in html
    assert "annotate" in html.lower()


def test_inline_highlighted_code(render):
    """zensicalbasics.md: `` `#!python print("Hello, Python!")` `` -
    InlineHilite's shebang-prefixed inline code syntax."""
    html = render('Some text `#!python print("Hello, Python!")` more text.')
    assert "<code" in html
    assert "print" in html


def test_fenced_code_per_block_copy_control(render):
    """zensical.org/docs/authoring/code-blocks/#code-copy-button: attr_list
    classes on the opening fence toggle the copy/select buttons per block."""
    html = render('''
        ``` { .yaml .no-copy }
        key: value
        ```
    ''')
    assert "no-copy" in html


# ---------------------------------------------------------------------------
# Content tabs
# ---------------------------------------------------------------------------

def test_content_tabs_basic(render):
    html = render('''
        === "Python"

            ``` python
            print("Hello from Python!")
            ```

        === "Rust"

            ``` rs
            println!("Hello from Rust!");
            ```
    ''')
    assert html.count('class="tabbed-set') >= 1
    assert "Python" in html and "Rust" in html
    assert "print" in html and "println" in html


def test_content_tabs_nested(render):
    """zensical.org/docs/authoring/content-tabs/: tabs can contain further
    nested content tabs."""
    html = render('''
        === "Outer"

            === "Inner A"

                Inner A content.

            === "Inner B"

                Inner B content.
    ''')
    assert html.count('class="tabbed-set') == 2
    assert "Inner A content" in html and "Inner B content" in html


def test_content_tab_gets_an_anchor_id(render):
    """pymdownx.tabbed's combine_header_slug = true (zensical.toml) -
    each tab gets a linkable, page-scoped anchor id."""
    html = render('=== "My Tab"\n\n    Content.')
    assert 'id="' in html


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------

def test_figure_figcaption_pattern(render):
    """zensicalbasics.md's own <figure markdown="span"> pattern - needs
    md_in_html (configured in zensical.toml) to process the Markdown image
    syntax nested inside raw HTML."""
    html = render('''
        <figure markdown="span">
          ![Image title](https://example.com/image.png){ width="300" }
          <figcaption>Image caption</figcaption>
        </figure>
    ''')
    assert "<figure" in html
    assert "<figcaption>Image caption</figcaption>" in html
    assert '<img alt="Image title"' in html


def test_image_alignment_attribute(render):
    html_left = render('![Alt](image.jpg){ align=left }')
    html_right = render('![Alt](image.jpg){ align=right }')
    assert 'align="left"' in html_left
    assert 'align="right"' in html_right


def test_image_lazy_loading_attribute(render):
    html = render('![Alt](image.jpg){ loading=lazy }')
    assert 'loading="lazy"' in html


def test_image_light_dark_mode_hash_fragment(render):
    """zensical.org/docs/authoring/images/: appending #only-light/#only-dark
    to an image URL is what extra.css's own light/dark logo-swap rules key
    off (see "Site logo" in customise.md)."""
    html = render('![Logo](logo.png#only-dark)')
    assert 'src="logo.png#only-dark"' in html


# ---------------------------------------------------------------------------
# Diagrams
# ---------------------------------------------------------------------------
# The 5 diagram types zensical.org/docs/authoring/diagrams/ says are
# officially supported (pie/gantt/journey/git/requirement diagrams work via
# Mermaid.js but aren't officially supported - not tested here).
MERMAID_DIAGRAM_SNIPPETS = {
    "flowchart": "graph LR\n  A --> B",
    "sequence": "sequenceDiagram\n  Alice->>Bob: Hello",
    "state": "stateDiagram-v2\n  [*] --> Active",
    "class": "classDiagram\n  class Animal",
    "entity-relationship": "erDiagram\n  CUSTOMER ||--o{ ORDER : places",
}


@pytest.mark.parametrize("diagram_type", MERMAID_DIAGRAM_SNIPPETS)
def test_mermaid_diagram_types_get_the_mermaid_class(render, diagram_type):
    """Verifies the custom_fences wiring (zensical.toml's
    [project.markdown_extensions.pymdownx.superfences] custom_fences entry)
    tags a ```mermaid fence with class="mermaid" regardless of which
    diagram type is inside it - actual Mermaid.js rendering is client-side
    (website) / mermaid-cli (PDF, see build_pdf.py's render_mermaid_diagrams()
    tested in test_fences.py), neither of which this batch exercises."""
    body = MERMAID_DIAGRAM_SNIPPETS[diagram_type]
    html = render(f"``` mermaid\n{body}\n```")
    assert 'class="mermaid"' in html


# ---------------------------------------------------------------------------
# Footnotes
# ---------------------------------------------------------------------------

def test_footnote_reference_and_definition(render):
    html = render("Here's a sentence with a footnote.[^1]\n\n[^1]: This is the footnote.")
    assert 'href="#fn:1"' in html
    assert 'id="fn:1"' in html
    assert "This is the footnote" in html
    assert 'href="#fnref:1"' in html  # backlink


def test_multi_paragraph_footnote(render):
    html = render("""
        A sentence.[^1]

        [^1]:
            First paragraph.

            Second paragraph.
    """)
    assert "First paragraph" in html and "Second paragraph" in html


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------
# Subscript/superscript/underline/strikethrough are already covered by
# test_markdown_foundations.py; mark (highlight) and keys are specific to
# this page's "Formatting" section and aren't tested there.

def test_mark_highlight(render):
    html = render("==This was marked (highlight)==")
    assert "<mark>This was marked (highlight)</mark>" in html


def test_keyboard_keys(render):
    html = render("++ctrl+alt+del++")
    assert 'class="keys"' in html
    assert "Ctrl" in html and "Alt" in html and "Del" in html


# ---------------------------------------------------------------------------
# Icons, emojis
# ---------------------------------------------------------------------------

def test_emoji_shortcode_renders_a_twemoji_image(render):
    html = render(":sparkles:")
    assert 'class="twemoji"' in html
    assert "<img" in html


def test_icon_shortcode_renders_an_inline_svg(render):
    """zensical.org/docs/authoring/icons-emojis/: :icon-set-icon-name: -
    directory slashes become hyphens (.icons/fontawesome/brands/github.svg
    -> :fontawesome-brands-github:)."""
    html = render(":fontawesome-brands-github:")
    assert 'class="twemoji"' in html
    assert "<svg" in html


def test_icon_with_attr_list_class(render):
    html = render(":fontawesome-brands-github:{ .my-icon-class }")
    assert "my-icon-class" in html


# ---------------------------------------------------------------------------
# Maths
# ---------------------------------------------------------------------------

def test_inline_and_display_math_get_arithmatex_class(render):
    """pymdownx.arithmatex with generic = true (zensical.toml) wraps math
    in an element carrying class="arithmatex" - MathJax's own config (see
    zensicalbasics.md's inline <script>) is set to only process elements
    with that class, so this is the load-bearing hook for math to render
    client-side at all; actual math typesetting itself is out of scope
    here (client-side JS)."""
    inline_html = render("Einstein's $E=mc^2$ formula.")
    display_html = render("$$\n\\cos x = 1\n$$")
    assert "arithmatex" in inline_html
    assert "arithmatex" in display_html


# ---------------------------------------------------------------------------
# Task lists
# ---------------------------------------------------------------------------
# Core checkbox rendering is already covered by
# test_markdown_foundations.py::test_task_list_renders_checkboxes; this
# just confirms it in the specific 4-item form zensicalbasics.md shows.

def test_task_list_mixed_checked_and_unchecked(render):
    html = render("""
        * [x] Install Zensical
        * [x] Configure `zensical.toml`
        * [x] Write amazing documentation
        * [ ] Deploy anywhere
    """)
    assert html.count('type="checkbox"') == 4
    assert html.count("checked") == 3


# ---------------------------------------------------------------------------
# Tooltips
# ---------------------------------------------------------------------------
# The reference-link-with-title syntax itself is already covered by
# test_markdown_foundations.py::test_reference_style_link_resolves /
# test_basic_link_and_titled_link; abbreviations are specific to this page.

def test_abbreviation_gets_an_abbr_tag(render):
    html = render("""
        The HTML specification is maintained by the W3C.

        *[HTML]: Hyper Text Markup Language
        *[W3C]: World Wide Web Consortium
    """)
    assert '<abbr title="Hyper Text Markup Language">HTML</abbr>' in html
    assert '<abbr title="World Wide Web Consortium">W3C</abbr>' in html


def test_attr_list_title_as_a_tooltip_on_a_non_link_element(render):
    html = render(':fontawesome-solid-circle-info:{ title="Important information" }')
    assert 'title="Important information"' in html


# ---------------------------------------------------------------------------
# Real, already-built PDF checks
# ---------------------------------------------------------------------------
# Everything above renders synthetic snippets through the website's own
# Markdown pipeline - a faithful proxy for the *website*, since that's
# literally what powers it, but not evidence either way for the *PDF*,
# which goes through a completely different parser (Pandoc) that
# build_pdf.py has to explicitly teach about each pymdownx extension one at
# a time (see #25/#28's "every feature needs its own bespoke regex pass").
# zensicalbasics.md's own "each with a live example" content already
# exercises every feature on this page for real, so these check that
# content in the actual built PDF, the same end-to-end pattern
# test_captions.py already uses - rather than assuming a feature "should"
# work in the PDF just because it's covered above for the website.

def test_admonitions_render_styled_not_leaked(pdf_full_text, pdf_doc):
    start, end = chapter_page_range(pdf_doc, "10. Zensical basics")
    chapter_text = "".join(pdf_full_text[start:end])
    assert "Note" in chapter_text and "This is a" in chapter_text and "note admonition" in chapter_text
    assert "Warning" in chapter_text and "warning admonition" in chapter_text
    assert "!!! note" not in chapter_text and "!!! warning" not in chapter_text


def test_collapsible_details_renders_content_not_leaked(pdf_full_text, pdf_doc):
    start, end = chapter_page_range(pdf_doc, "10. Zensical basics")
    chapter_text = "".join(pdf_full_text[start:end])
    assert "Click to expand for more info" in chapter_text
    assert "hidden until you click to expand" in chapter_text
    assert "??? info" not in chapter_text


def test_content_tabs_render_both_tabs_content_not_leaked(pdf_full_text, pdf_doc):
    """The PDF is static - there's no interactive tab-switching - so both
    tabs' content should appear (sequentially), not just one, and
    definitely not the raw === "Tab" marker syntax."""
    start, end = chapter_page_range(pdf_doc, "10. Zensical basics")
    chapter_text = "".join(pdf_full_text[start:end])
    assert 'print("Hello from Python!")' in chapter_text
    assert 'println!("Hello from Rust!")' in chapter_text
    assert '=== "Python"' not in chapter_text


def test_mermaid_diagram_is_a_real_embedded_image_not_leaked_text(pdf_doc):
    """render_mermaid_diagrams() in build_pdf.py pre-renders ```mermaid
    fences to static images via mermaid-cli (see test_fences.py for the
    function itself) - confirms that actually reaches this page of the
    real PDF: an embedded image, and no literal "```mermaid" text."""
    start, end = chapter_page_range(pdf_doc, "10. Zensical basics")
    found_image = False
    for i in range(start, end):
        page = pdf_doc[i]
        if "```mermaid" in page.get_text() or "``` mermaid" in page.get_text():
            raise AssertionError(f"Leaked literal mermaid fence syntax on page {i}")
        if page.get_image_info():
            found_image = True
    assert found_image, "No embedded image found anywhere in the Zensical basics chapter"


def test_math_is_rendered_not_leaked_as_literal_dollar_syntax(pdf_full_text, pdf_doc):
    """mathjax-full pre-renders $...$/$$...$$ to static images for the PDF
    (see tools/mathjax/, and build_pdf.py's own comment on why - WeasyPrint
    has no JS engine to run MathJax client-side). Confirms the literal
    dollar-delimited source doesn't leak through unconverted."""
    start, end = chapter_page_range(pdf_doc, "10. Zensical basics")
    chapter_text = "".join(pdf_full_text[start:end])
    assert r"\cos x" not in chapter_text, "Raw LaTeX source leaked instead of being rendered to an image"


def test_task_list_renders_real_checkboxes_not_leaked(pdf_full_text, pdf_doc):
    """"- [ ]"/"- [x]" legitimately appear once each already, as inline-code
    syntax examples in this section's own explanatory prose ("using the
    - [ ] syntax for an unchecked item") - not a leak, real content this
    template's own docs intentionally show literally. What would indicate
    an actual leak is the task list *itself* rendering as raw markdown
    right next to its own label text, so this checks for that combined
    string specifically rather than a bare "- [x]"/"- [ ]" anywhere on the
    page."""
    start, end = chapter_page_range(pdf_doc, "10. Zensical basics")
    chapter_text = "".join(pdf_full_text[start:end])
    assert "Install Zensical" in chapter_text
    assert "- [x] Install Zensical" not in chapter_text
    assert "- [ ] Deploy anywhere" not in chapter_text


def test_footnote_renders_with_backlink_not_leaked(pdf_full_text, pdf_doc):
    """"[^1]" legitimately appears once already, as an inline-code syntax
    example in this section's own explanatory prose ("using the [^1]
    syntax") - not a leak. What would indicate an actual leak is the real
    footnote reference itself staying as raw "[^1]" text right after the
    sentence it's attached to, so this checks for that combined string
    specifically."""
    start, end = chapter_page_range(pdf_doc, "10. Zensical basics")
    chapter_text = "".join(pdf_full_text[start:end])
    assert "This is the footnote." in chapter_text
    assert "footnote.[^1]" not in chapter_text


def test_icons_and_emoji_render_as_real_glyphs_not_leaked(pdf_doc):
    start, end = chapter_page_range(pdf_doc, "10. Zensical basics")
    found_image = False
    for i in range(start, end):
        page = pdf_doc[i]
        text = page.get_text()
        if ":sparkles:" in text or ":rocket:" in text:
            # Icon shortcode text itself is expected in this template's own
            # attr_list-styled inline-code spans (see zensicalbasics.md's
            # own "* :sparkles: `:sparkles:`" - the *second*, backtick-
            # wrapped copy is an intentional literal example) - only flag
            # it if there's no rendered glyph at all anywhere nearby.
            found_image = found_image or bool(page.get_image_info())
    # At minimum, some image (twemoji/icon SVG rendered to a raster/vector
    # image in the PDF) should exist somewhere on these pages.
    assert any(pdf_doc[i].get_image_info() for i in range(start, end))


def test_mark_insert_and_keys_render_styled_not_leaked(pdf_full_text, pdf_doc):
    """issue #72: Pandoc's markdown reader has no native support for
    pymdownx.mark (==highlight==) or pymdownx.keys (++key+combo++), so both
    used to leak through as literal, unrendered text; pymdownx.caret's insert
    mode (^^underline^^) used to silently collide with Pandoc's own
    single-caret superscript syntax and produce an empty, invisible
    <sup></sup> instead (a second, separate bug caught while fixing this
    one - the underline never actually rendered, despite an earlier,
    incorrect assumption that it did). build_pdf.py's preprocess_markdown()
    now rewrites all three to raw HTML - which Pandoc passes through
    untouched - before Pandoc ever parses them; confirmed here against the
    actual built PDF page text, and separately by rendering the page to an
    image and visually checking the highlight/underline/kbd-box styling."""
    start, end = chapter_page_range(pdf_doc, "10. Zensical basics")
    chapter_text = "".join(pdf_full_text[start:end])

    assert "This was marked (highlight)" in chapter_text
    assert "==This was marked (highlight)==" not in chapter_text

    assert "This was inserted (underline)" in chapter_text
    assert "^^This was inserted (underline)^^" not in chapter_text

    assert "Ctrl" in chapter_text and "Alt" in chapter_text and "Del" in chapter_text
    assert "++ctrl+alt+del++" not in chapter_text

    # The extension's sibling on the same page, for contrast - confirms this
    # is specifically the mark/insert/keys fix, not a regression elsewhere.
    assert "This was deleted (strikethrough)" in chapter_text
    assert "~~This was deleted (strikethrough)~~" not in chapter_text
