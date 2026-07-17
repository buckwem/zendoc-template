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
    # WeasyPrint's float: footnote renders the footnote area in a narrow
    # fixed-width column (a known WeasyPrint limitation - see build_pdf.py's
    # ".pdf-footnote" comment), so short footnote text often wraps onto 2-3
    # lines instead of one - normalize whitespace rather than requiring it
    # stay on one line, which would be asserting on a rendering detail this
    # template's own CSS has no control over.
    normalized = " ".join(chapter_text.split())
    assert "This is the footnote." in normalized
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
    incorrect assumption that it did). build_pdf.py now renders the page
    through the real pymdownx.mark/pymdownx.caret/pymdownx.keys extensions
    (see render_page_html()) and hands Pandoc the resulting real HTML, which
    it passes through untouched, rather than hand-translating the markdown
    syntax itself; confirmed here against the actual built PDF page text,
    and separately by rendering the page to an image and visually checking
    the highlight/underline/kbd-box styling."""
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


# ---------------------------------------------------------------------------
# Grid cards and table styling (prodockit-template#92/#93)
# ---------------------------------------------------------------------------
# Zensical's native grid-card HTML (a plain <div class="grid cards"><ul><li>)
# isn't demonstrated as its own section in zensicalbasics.md, but is a real,
# load-bearing feature used throughout installtooling.md ("7. Install
# tooling") - checked here against the real, already-built PDF rather than a
# render() snippet, since every regression this guards against (render_page_
# html()'s own <svg>-><img> icon conversion, the CSS matching Zensical's real
# grid-card DOM instead of the old, dead .gridcard-matrix convention, and the
# page-break-inside value on both grid cards and table captions) only
# manifests through the full Pandoc/WeasyPrint pipeline. Table cell alignment
# is included here rather than in test_markdown_foundations.py for the same
# reason - it's a compiled-CSS/WeasyPrint concern, not something the website's
# own markdown.Markdown() pipeline that batch otherwise tests can exercise.

def test_real_grid_card_renders_as_a_bordered_box_not_a_plain_bullet_list(pdf_doc):
    """Regression test (prodockit-template#92): Zensical's real grid-card HTML
    is a plain <div class="grid cards"><ul><li>, not the old regex
    pipeline's own .gridcard-matrix/-item convention (retired along with the
    rest of preprocess_markdown()) - the compiled PDF CSS only had rules for
    the old, now-dead structure until this was fixed, so a real grid card
    rendered as an unstyled bullet list instead of the card box treatment.
    Checks the "Fork the documentation template" card (installtooling.md)
    for a filled background rectangle (the card box, #f4f8ff) behind it."""
    for page in pdf_doc:
        if "Fork the documentation template" not in page.get_text():
            continue
        filled = [
            d for d in page.get_drawings()
            if d.get("fill") and all(abs(c1 - c2) < 0.01 for c1, c2 in zip(d["fill"], (0.9569, 0.9725, 1.0)))
        ]
        assert filled, "Expected a filled background rectangle (the grid card box) behind 'Fork the documentation template'"
        return
    raise AssertionError("Expected to find the 'Fork the documentation template' grid card in the PDF")


def test_real_grid_card_title_icon_renders_as_an_image_not_missing(pdf_doc):
    """Regression test: a grid card title's icon shortcode
    (e.g. ":material-clock-fast:") renders as a raw inline <svg> from
    pymdownx.emoji - confirmed this doesn't survive Pandoc's HTML-to-HTML
    round trip through to WeasyPrint at all (isolated test: a <p>Before
    <svg>...</svg> After</p> rendered as "Before  After", no error, nothing
    visible). render_page_html() base64-embeds every remaining <svg> as an
    <img> instead - checks the "Fork the documentation template" card's page
    has at least one embedded image (the icon)."""
    for page in pdf_doc:
        if "Fork the documentation template" not in page.get_text():
            continue
        assert len(page.get_images()) > 0, "Expected the grid card title's icon to render as an embedded image"
        return
    raise AssertionError("Expected to find the 'Fork the documentation template' grid card in the PDF")


@pytest.mark.parametrize("parent_heading,child_heading", [
    ("7.1 Install Visual Studio Code", "7.1.1 Install Visual Studio Code"),
    ("7.2 Install Git with Visual Studio Code", "7.2.1 Install and configure Git"),
    # These two pairs (additionaltooling.md) have a different root cause
    # than the grid-card page-break-inside fix above: print.css's own
    # "h1..h6 { page-break-after: avoid }" is fine for h1/h2 (a short intro
    # follows), but for h3-h6 it couldn't be satisfied without pulling in
    # far more content than intended whenever a large grid card immediately
    # follows, so the *entire* heading (not just what follows it) got
    # pushed onto a fresh page - confirmed directly via an A/B rebuild
    # toggling "h3, h4, h5, h6 { page-break-after: auto }" on and off.
    ("12.3 Installing a GUI Git client", "12.3.1 Installing GitHub Desktop"),
    ("12.3.1 Installing GitHub Desktop", "12.3.2 Installing GitKraken"),
])
def test_real_grid_card_does_not_force_a_blank_page_gap_before_its_heading(pdf_doc, parent_heading, child_heading):
    """Regression test (prodockit-template#93): a real grid card commonly wraps
    a whole tabbed-set (e.g. installtooling.md's per-OS install
    instructions, all three OS tabs stacked since WeasyPrint can't do
    interactive tabs) - often taller than a full page. The grid-card CSS's
    page-break-inside: avoid forced the entire oversized card onto a fresh
    page as one atomic unit (unable to actually fit there either), leaving a
    large blank gap on the previous page - confirmed directly against the
    built PDF for both heading pairs below, each immediately followed by
    exactly this kind of grid card. Both headings in a pair should land on
    the same page."""
    parent_page = child_page = None
    for i, page in enumerate(pdf_doc):
        text = page.get_text()
        if parent_heading in text:
            parent_page = i
        if child_heading in text:
            child_page = i
        if parent_page is not None and child_page is not None:
            break
    assert parent_page is not None, f"Expected to find '{parent_heading}' in the PDF"
    assert child_page is not None, f"Expected to find '{child_heading}' in the PDF"
    assert parent_page == child_page, (
        f"Expected '{child_heading}' on the same page as '{parent_heading}' (page {parent_page}), "
        f"found it on page {child_page} instead - possible page-break regression"
    )


def test_real_table_body_text_is_left_aligned_not_centered(pdf_doc):
    """Regression test: table th/td had no explicit text-align, so cell
    content silently inherited text-align: center from a table-caption's
    own wrapping container (div.prodockit-table-caption, or the pre-existing
    "figure {}" rule for the append-position case) - confirmed directly,
    every real table's body text was centering rather than reading
    left-aligned. Checks the real 'Basic navigation commands' table
    (shcommands.md): the left edge of each row's second-column text should
    line up, which centered text (whose left edge shifts with each row's
    text length) would not."""
    x0s = []
    for page in pdf_doc:
        if "Basic navigation commands" not in page.get_text():
            continue
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line["spans"]:
                    if span["text"].strip().startswith(("Print Working", "List:", "Cleans up")):
                        x0s.append(round(span["bbox"][0], 1))
        break
    assert len(x0s) >= 2, "Expected at least two matching table body cells in the PDF"
    assert max(x0s) - min(x0s) < 1, f"Expected consistent left-aligned x-positions, got {x0s}"


def test_real_table_body_font_size_is_smaller_than_body_text(pdf_doc):
    """Companion to the alignment fix above - table th/td font-size is
    reduced to 10pt (see build_pdf.py's "table th, table td" rule), smaller
    than surrounding body text, so a dense grid of short cells reads better.
    Checks the real 'Basic navigation commands' table body text is smaller
    than this same chapter's own intro paragraph text."""
    table_size = paragraph_size = None
    for page in pdf_doc:
        text = page.get_text()
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line["spans"]:
                    if "Print Working Directory" in span["text"]:
                        table_size = span["size"]
                    if "Knowing where you are and how to move" in span["text"]:
                        paragraph_size = span["size"]
        if table_size is not None and paragraph_size is not None:
            break
    assert table_size is not None, "Expected to find table body text in the PDF"
    assert paragraph_size is not None, "Expected to find the chapter's own intro paragraph in the PDF"
    assert table_size < paragraph_size, (
        f"Expected table body text ({table_size}pt) smaller than body text ({paragraph_size}pt)"
    )


def test_real_heading_does_not_force_a_blank_page_gap_after_a_short_preceding_admonition(pdf_doc):
    """Regression test: a plain <p> had no break-inside/orphans/widows
    protection at all. Simply making every <p> unsplittable (break-inside:
    avoid) over-corrected - a short (e.g. 2-line) paragraph immediately
    after a heading became atomic with that heading too, and if the
    combined size didn't fit the page's remaining space, the *whole*
    heading+paragraph pair was pushed to a fresh page, leaving a large
    blank gap behind (confirmed directly for "8.2 Synchronise your
    updates" - startediting.md). orphans: 1 / widows: 2 replaces the
    blanket avoid: a short paragraph can still leave as few as 1 line
    behind (no gap forced) while a longer one avoids an ugly single-line
    widow if it does split. Checks the Tip admonition's own last line
    (startediting.md, immediately before "8.2") lands on the same page as
    the "8.2" heading and the start of its own paragraph."""
    admonition_page = heading_page = None
    for i, page in enumerate(pdf_doc):
        text = page.get_text()
        if "See Build the PDF below to preview the PDF output." in text:
            admonition_page = i
        if "8.2 Synchronise your updates" in text:
            heading_page = i
        if admonition_page is not None and heading_page is not None:
            break
    assert admonition_page is not None, "Expected to find the Tip admonition's own last line in the PDF"
    assert heading_page is not None, "Expected to find the '8.2 Synchronise your updates' heading in the PDF"
    assert admonition_page == heading_page, (
        f"Expected '8.2 Synchronise your updates' on the same page as the preceding Tip "
        f"admonition (page {admonition_page}), found it on page {heading_page} instead - "
        f"possible page-break regression"
    )


def test_real_footnote_lands_near_its_reference_and_is_smaller(pdf_doc):
    """Regression test (prodockit-template#93): Zensical's own markdown
    pipeline renders a footnote as a <div class="footnote"> collecting
    every footnote's own text at the *end* of the page, never a
    Pandoc-native Note element (that only exists when Pandoc's own
    markdown reader parses "[^1]" syntax directly - not when it's handed
    pre-rendered HTML, as render_page_html() does). The Lua filter's
    Note()/.pdf-footnote float: footnote mechanism was written for that
    native-Note case and silently never fired here - confirmed directly,
    the footnote's own text used to render *several chapters* after its
    own reference, at regular body-text size. render_page_html() now moves
    each footnote's text inline at its own reference point instead, so
    WeasyPrint's float: footnote can at least attempt to anchor it nearby.

    WeasyPrint's own placement isn't pixel-perfect even with this fix -
    confirmed directly that unrelated layout changes elsewhere in the same
    chapter (e.g. the h3-h6/admonition-title page-break-after fixes above)
    can still shift the footnote text onto the chapter's last page rather
    than its own exact reference page - a further symptom of the same
    WeasyPrint limitation tracked in prodockit-template#95, not something
    build_pdf.py's CSS can pin down further. Checks the real "Here's a
    sentence with a footnote." example (zensicalbasics.md): its footnote
    text should land somewhere in the same chapter as the reference (not
    several chapters away, as before this fix), smaller than body text."""
    start, end = chapter_page_range(pdf_doc, "10. Zensical basics")
    body_size = None
    footnote_size = None
    for i in range(start, end):
        for block in pdf_doc[i].get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line["spans"]:
                    if "Here's a sentence with a footnote" in span["text"]:
                        body_size = span["size"]
                    elif "This is" == span["text"].strip() or "the footnote." in span["text"]:
                        footnote_size = span["size"]
    assert body_size is not None, "Expected to find the footnote reference sentence in the PDF"
    assert footnote_size is not None, (
        "Expected to find the footnote's own text somewhere in the '10. Zensical basics' chapter"
    )
    assert footnote_size < body_size, (
        f"Expected footnote text ({footnote_size}pt) smaller than body text ({body_size}pt)"
    )


def test_real_short_heading_and_its_own_paragraph_do_not_separate(pdf_doc):
    """Regression test: h3-h6's page-break-after: auto (see the h3,h4,h5,h6
    rule above) fixed the blank-gap regression, but on its own could leave
    a heading orphaned alone at the bottom of a page with its own
    paragraph starting completely fresh on the next - confirmed directly
    for "7.2.2 Generate and configure ssh keys for Git" (installtooling.md):
    its own intro paragraph is only 2 lines, shorter than the previous
    orphans: 3 / widows: 3 combined minimum (6 lines), so no split was
    legal at all and the whole paragraph moved away from the heading.
    orphans: 1 / widows: 2 (only 3 combined) fixes this - checks the
    heading and the start of its own paragraph now land on the same page."""
    heading_page = paragraph_page = None
    for i, page in enumerate(pdf_doc):
        text = page.get_text()
        if "7.2.2 Generate and configure ssh keys for Git" in text:
            heading_page = i
        if "Now generate the ssh keys to use for authentication" in text:
            paragraph_page = i
        if heading_page is not None and paragraph_page is not None:
            break
    assert heading_page is not None, "Expected to find the '7.2.2' heading in the PDF"
    assert paragraph_page is not None, "Expected to find its own paragraph's start in the PDF"
    assert heading_page == paragraph_page, (
        f"Expected '7.2.2 Generate and configure ssh keys for Git' on the same page as the "
        f"start of its own paragraph (heading page {heading_page}, paragraph page "
        f"{paragraph_page}) - possible orphaned-heading regression"
    )


def test_real_admonition_does_not_force_a_blank_page_gap_before_it(pdf_doc):
    """Regression test: .admonition-title's own page-break-after: avoid had
    the same WeasyPrint quirk as h3-h6's own page-break-after (see both
    rules above) - even though .admonition itself already uses
    page-break-inside: auto, the title's own avoid-after still forced the
    *entire* admonition onto a fresh page rather than letting it start on
    the current one, leaving a large blank gap behind - confirmed directly
    for "The Four Space Rule" admonition (zensicalbasics.md), whose own
    body is only 2-3 short lines, easily small enough to have fit. Checks
    the admonition lands on the same page as the paragraph immediately
    before it."""
    preceding_page = admonition_page = None
    for i, page in enumerate(pdf_doc):
        text = page.get_text()
        if "the original Markdown specification." in text:
            preceding_page = i
        if "Four Space Rule" in text:
            admonition_page = i
        if preceding_page is not None and admonition_page is not None:
            break
    assert preceding_page is not None, "Expected to find the paragraph preceding the admonition in the PDF"
    assert admonition_page is not None, "Expected to find 'The Four Space Rule' admonition in the PDF"
    assert preceding_page == admonition_page, (
        f"Expected 'The Four Space Rule' admonition on the same page as the preceding "
        f"paragraph (page {preceding_page}), found it on page {admonition_page} instead - "
        f"possible page-break regression"
    )


def test_real_large_code_block_does_not_force_a_blank_page_gap_before_it(pdf_doc):
    """Regression test: print.css's own "img, pre, blockquote,
    .tabbox-container { page-break-inside: avoid }" is fine for img/
    blockquote (naturally short/atomic) and is already overridden back to
    auto for .tabbox-container elsewhere in this stylesheet - but pre
    wasn't, so a large fenced code block hit the same WeasyPrint quirk
    already fixed for grid cards/table captions/admonitions/headings
    above. Confirmed directly against the built PDF: customise.md's own
    ~34-line "nav = [...]" example (illustrating zensical.toml's own nav
    list, rendered live via the {{ nav_snippet() }} macro) forced itself
    entirely onto a fresh page rather than splitting, leaving a large
    blank gap on the previous page. Checks the paragraph introducing the
    example ("...matches what's actually configured:") lands on the same
    page as the start of the code block."""
    preceding_page = code_page = None
    for i, page in enumerate(pdf_doc):
        text = page.get_text()
        if "matches what's actually configured" in text:
            preceding_page = i
        if "nav = [" in text:
            code_page = i
        if preceding_page is not None and code_page is not None:
            break
    assert preceding_page is not None, "Expected to find the paragraph introducing the nav example in the PDF"
    assert code_page is not None, "Expected to find the 'nav = [' code example in the PDF"
    assert preceding_page == code_page, (
        f"Expected the 'nav = [...]' code example on the same page as its introducing "
        f"paragraph (page {preceding_page}), found it on page {code_page} instead - "
        f"possible page-break regression"
    )
