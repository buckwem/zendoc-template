# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""zensical_basics batch: checks the Zensical-specific Markdown extensions
that used to be taught on the User Guide's zensicalbasics.md page (see
issue #49 - that page, and most of the rest of docs/starthere/, moved to
the separate prodockit-userguide repo) - admonitions, collapsible details,
code blocks, content tabs, images, diagrams, footnotes, formatting,
icons/emojis, maths, task lists, and tooltips - render the way the fuller
upstream zensical.org/docs/authoring/* pages say they do.

Like test_markdown_foundations.py, this renders hand-written snippets
through a real markdown.Markdown() instance built from this project's own
zensical.toml extension config (see conftest.py's markdown_extension_config
fixture), so tests can't silently drift out of sync with it. Unlike that
batch, this one also wires up a *working* pymdownx.emoji config - real
zensical.extensions.emoji callables, not the dotted-string references
markdown_extension_config deliberately omits - since "Icons, emojis" was a
section on that page.

Each section below cross-checks against the corresponding
zensical.org/docs/authoring/* page, not just one worked example, per issue
#50 - e.g. all 12 configured admonition types, not just a note/warning
pair; all 5 officially-supported Mermaid diagram types, not just one
flowchart example.

Not covered: the "Commands" section (zensical new/serve/build) - these are
CLI behaviour, not Markdown syntax, and aren't meaningfully testable by
rendering a snippet the way everything else here is."""

import textwrap

import markdown
import pytest

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
    (website) / mermaid-cli (PDF, see prodockit.pdf.mermaid.render_mermaid_diagram()
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
# Real, synthetic-but-real-pipeline PDF checks
# ---------------------------------------------------------------------------
# Everything above renders synthetic snippets through the website's own
# Markdown pipeline - a faithful proxy for the *website*, since that's
# literally what powers it, but not evidence either way for the *PDF*,
# which goes through a completely different parser (Pandoc) that
# prodockit.pdf has to explicitly teach about each pymdownx extension one at
# a time (see #25/#28's "every feature needs its own bespoke regex pass").
#
# These used to check zensicalbasics.md's own "each with a live example"
# content in the actual, already-built site PDF - see issue #49: that page
# moved to the separate prodockit-userguide repo, so these now build their
# own small pages through the real Zensical-render + prodockit.pdf Pandoc/
# WeasyPrint pipeline instead (see conftest.py's build_synthetic_pdf
# fixture), keeping the regression coverage independent of which report
# content happens to exist here.

def test_admonitions_render_styled_not_leaked(build_synthetic_pdf):
    doc = build_synthetic_pdf([("test.md", """# Test Chapter

!!! note

    This is a **note** admonition. Use it to provide helpful information.

!!! warning

    This is a **warning** admonition. Be careful!
""")])
    try:
        text = "\n".join(page.get_text() for page in doc)
        assert "Note" in text and "This is a" in text and "note admonition" in text
        assert "Warning" in text and "warning admonition" in text
        assert "!!! note" not in text and "!!! warning" not in text
    finally:
        doc.close()


def test_collapsible_details_renders_content_not_leaked(build_synthetic_pdf):
    doc = build_synthetic_pdf([("test.md", """# Test Chapter

??? info "Click to expand for more info"

    This content is hidden until you click to expand it.
    Great for FAQs or long explanations.
""")])
    try:
        text = "\n".join(page.get_text() for page in doc)
        assert "Click to expand for more info" in text
        assert "hidden until you click to expand" in text
        assert "??? info" not in text
    finally:
        doc.close()


def test_content_tabs_render_both_tabs_content_not_leaked(build_synthetic_pdf):
    """The PDF is static - there's no interactive tab-switching - so both
    tabs' content should appear (sequentially), not just one, and
    definitely not the raw === "Tab" marker syntax."""
    doc = build_synthetic_pdf([("test.md", '''# Test Chapter

=== "Python"

    ``` python
    print("Hello from Python!")
    ```

=== "Rust"

    ``` rs
    println!("Hello from Rust!");
    ```
''')])
    try:
        text = "\n".join(page.get_text() for page in doc)
        assert 'print("Hello from Python!")' in text
        assert 'println!("Hello from Rust!")' in text
        assert '=== "Python"' not in text
    finally:
        doc.close()


def test_mermaid_diagram_is_a_real_embedded_diagram_not_leaked_text(build_synthetic_pdf):
    """prodockit.pdf.mermaid.render_mermaid_diagram() pre-renders ```mermaid
    fences to static images via mermaid-cli (see test_fences.py for the
    function itself) - confirms that actually reaches the real PDF: real
    vector drawing content (WeasyPrint renders the resulting SVG as native
    vector paths/text, not a raster image XObject - get_drawings(), not
    get_image_info()), and no literal "```mermaid" text."""
    doc = build_synthetic_pdf([("test.md", """# Test Chapter

``` mermaid
graph LR
  A[Start] --> B{Error?}
```
""")])
    try:
        found_drawing = False
        for page in doc:
            if "```mermaid" in page.get_text() or "``` mermaid" in page.get_text():
                raise AssertionError("Leaked literal mermaid fence syntax")
            if page.get_drawings():
                found_drawing = True
        assert found_drawing, "No rendered diagram drawing found anywhere in the PDF"
    finally:
        doc.close()


def test_math_is_rendered_not_leaked_as_literal_dollar_syntax(build_synthetic_pdf):
    """mathjax-full pre-renders $...$/$$...$$ to static images for the PDF
    (see tools/mathjax/, and .github/workflows/docs.yml's own comment on
    why - WeasyPrint has no JS engine to run MathJax client-side). Confirms
    the literal dollar-delimited source doesn't leak through unconverted."""
    doc = build_synthetic_pdf([("test.md", r"""# Test Chapter

$$
\cos x=\sum_{k=0}^{\infty}\frac{(-1)^k}{(2k)!}x^{2k}
$$
""")])
    try:
        text = "\n".join(page.get_text() for page in doc)
        assert r"\cos x" not in text, "Raw LaTeX source leaked instead of being rendered to an image"
    finally:
        doc.close()


def test_task_list_renders_real_checkboxes_not_leaked(build_synthetic_pdf):
    doc = build_synthetic_pdf([("test.md", """# Test Chapter

* [x] Install Zensical
* [ ] Deploy anywhere
""")])
    try:
        text = "\n".join(page.get_text() for page in doc)
        assert "Install Zensical" in text
        assert "- [x] Install Zensical" not in text
        assert "- [ ] Deploy anywhere" not in text
    finally:
        doc.close()


def test_footnote_renders_with_backlink_not_leaked(build_synthetic_pdf):
    doc = build_synthetic_pdf([("test.md", """# Test Chapter

Here's a sentence with a footnote.[^1]

[^1]: This is the footnote.
""")])
    try:
        text = "\n".join(page.get_text() for page in doc)
        normalized = " ".join(text.split())
        assert "This is the footnote." in normalized
        assert "footnote.[^1]" not in text
    finally:
        doc.close()


def test_icons_and_emoji_render_as_real_glyphs_not_leaked(build_synthetic_pdf):
    """Twemoji's SVGs come through as native vector drawings once WeasyPrint
    rasterizes/vectorizes them (get_drawings(), not get_image_info() - the
    same as a real Mermaid diagram's own SVG, confirmed above), not an
    embedded raster image."""
    doc = build_synthetic_pdf([("test.md", """# Test Chapter

* :sparkles: :rocket: :tada:
""")])
    try:
        found_drawing = any(page.get_drawings() for page in doc)
        assert found_drawing, "Expected the emoji/icon shortcodes to render as real vector glyphs"
        text = "\n".join(page.get_text() for page in doc)
        assert ":sparkles:" not in text and ":rocket:" not in text and ":tada:" not in text
    finally:
        doc.close()


def test_mark_insert_and_keys_render_styled_not_leaked(build_synthetic_pdf):
    """issue #72: Pandoc's markdown reader has no native support for
    pymdownx.mark (==highlight==) or pymdownx.keys (++key+combo++), so both
    used to leak through as literal, unrendered text; pymdownx.caret's insert
    mode (^^underline^^) used to silently collide with Pandoc's own
    single-caret superscript syntax and produce an empty, invisible
    <sup></sup> instead. prodockit.pdf now renders the page through the real
    pymdownx.mark/pymdownx.caret/pymdownx.keys extensions (see
    render_page_html()) and hands Pandoc the resulting real HTML, which it
    passes through untouched, rather than hand-translating the markdown
    syntax itself."""
    doc = build_synthetic_pdf([("test.md", """# Test Chapter

- ==This was marked (highlight)==
- ^^This was inserted (underline)^^
- ~~This was deleted (strikethrough)~~
- ++ctrl+alt+del++
""")])
    try:
        text = "\n".join(page.get_text() for page in doc)

        assert "This was marked (highlight)" in text
        assert "==This was marked (highlight)==" not in text

        assert "This was inserted (underline)" in text
        assert "^^This was inserted (underline)^^" not in text

        assert "Ctrl" in text and "Alt" in text and "Del" in text
        assert "++ctrl+alt+del++" not in text

        # The extension's sibling, for contrast - confirms this is
        # specifically the mark/insert/keys fix, not a regression elsewhere.
        assert "This was deleted (strikethrough)" in text
        assert "~~This was deleted (strikethrough)~~" not in text
    finally:
        doc.close()


# ---------------------------------------------------------------------------
# Grid cards and table styling (prodockit-template#92/#93)
# ---------------------------------------------------------------------------
# Zensical's native grid-card HTML (a plain <div class="grid cards"><ul><li>)
# isn't demonstrated as its own section on this page, but is a real,
# load-bearing feature used throughout the User Guide's installtooling.md
# (see issue #49) - checked here against a real synthetic PDF rather than a
# render() snippet, since every regression this guards against (render_page_
# html()'s own <svg>-><img> icon conversion, and the CSS matching Zensical's
# real grid-card DOM instead of the old, dead .gridcard-matrix convention)
# only manifests through the full Pandoc/WeasyPrint pipeline. Table cell
# alignment is included here rather than in test_markdown_foundations.py for
# the same reason - it's a compiled-CSS/WeasyPrint concern, not something
# the website's own markdown.Markdown() pipeline that batch otherwise tests
# can exercise.

GRID_CARD_MD = """
<div class="grid cards one-column" markdown>

-   :material-clock-fast:{ .lg .middle } __Do a thing__

    1. First step.
    2. Second step.

</div>
"""


def test_real_grid_card_renders_as_a_bordered_box_not_a_plain_bullet_list(build_synthetic_pdf):
    """Regression test (prodockit-template#92): Zensical's real grid-card HTML
    is a plain <div class="grid cards"><ul><li>, not the old regex
    pipeline's own .gridcard-matrix/-item convention (retired along with the
    rest of preprocess_markdown()) - the compiled PDF CSS only had rules for
    the old, now-dead structure until this was fixed, so a real grid card
    rendered as an unstyled bullet list instead of the card box treatment.
    Checks for a filled background rectangle (the card box, #f4f8ff) behind
    a real grid card."""
    doc = build_synthetic_pdf([("test.md", f"# Test Chapter\n{GRID_CARD_MD}")])
    try:
        for page in doc:
            if "Do a thing" not in page.get_text():
                continue
            filled = [
                d for d in page.get_drawings()
                if d.get("fill") and all(abs(c1 - c2) < 0.01 for c1, c2 in zip(d["fill"], (0.9569, 0.9725, 1.0)))
            ]
            assert filled, "Expected a filled background rectangle (the grid card box) behind the grid card"
            return
        raise AssertionError("Expected to find the grid card in the PDF")
    finally:
        doc.close()


def test_real_grid_card_title_icon_renders_as_an_image_not_missing(build_synthetic_pdf):
    """Regression test: a grid card title's icon shortcode
    (e.g. ":material-clock-fast:") renders as a raw inline <svg> from
    pymdownx.emoji - confirmed this doesn't survive Pandoc's HTML-to-HTML
    round trip through to WeasyPrint at all (isolated test: a <p>Before
    <svg>...</svg> After</p> rendered as "Before  After", no error, nothing
    visible). render_page_html() base64-embeds every remaining <svg> as an
    <img> instead - checks the grid card's page has real vector content for
    the icon (get_drawings() - WeasyPrint renders the embedded SVG as native
    vector paths, not a raster image XObject, same as the emoji/mermaid
    checks above), rather than nothing at all."""
    doc = build_synthetic_pdf([("test.md", f"# Test Chapter\n{GRID_CARD_MD}")])
    try:
        for page in doc:
            if "Do a thing" not in page.get_text():
                continue
            assert page.get_drawings(), "Expected the grid card title's icon to render as real vector content"
            return
        raise AssertionError("Expected to find the grid card in the PDF")
    finally:
        doc.close()


TABLE_MD = """
/// table-caption
Basic navigation commands
///

| Command | Description |
|---|---|
| Print Working Directory | pwd |
| List working directory contents | ls |
"""


def test_real_table_body_text_is_left_aligned_not_centered(build_synthetic_pdf):
    """Regression test: table th/td had no explicit text-align, so cell
    content silently inherited text-align: center from a table-caption's
    own wrapping container (div.prodockit-table-caption, or the pre-existing
    "figure {}" rule for the append-position case) - confirmed directly,
    every real table's body text was centering rather than reading
    left-aligned. Checks two rows' left edges line up, which centered text
    (whose left edge shifts with each row's text length) would not."""
    doc = build_synthetic_pdf([("test.md", f"# Test Chapter\n{TABLE_MD}")])
    try:
        x0s = []
        for page in doc:
            if "Basic navigation commands" not in page.get_text():
                continue
            for block in page.get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        if span["text"].strip().startswith(("Print Working", "List working")):
                            x0s.append(round(span["bbox"][0], 1))
            break
        assert len(x0s) >= 2, "Expected at least two matching table body cells in the PDF"
        assert max(x0s) - min(x0s) < 1, f"Expected consistent left-aligned x-positions, got {x0s}"
    finally:
        doc.close()


def test_real_table_body_font_size_is_smaller_than_body_text(build_synthetic_pdf):
    """Companion to the alignment fix above - table th/td font-size is
    reduced to 10pt (see prodockit.pdf.css's "table th, table td" rule),
    smaller than surrounding body text, so a dense grid of short cells
    reads better."""
    doc = build_synthetic_pdf([("test.md", f"""# Test Chapter

Knowing where you are and how to move around is essential.
{TABLE_MD}""")])
    try:
        table_size = paragraph_size = None
        for page in doc:
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
        assert paragraph_size is not None, "Expected to find the intro paragraph in the PDF"
        assert table_size < paragraph_size, (
            f"Expected table body text ({table_size}pt) smaller than body text ({paragraph_size}pt)"
        )
    finally:
        doc.close()


# ---------------------------------------------------------------------------
# Pagination: no forced blank-page gaps (prodockit-template#93)
# ---------------------------------------------------------------------------
# These page-break/orphans/widows rules all live in the external
# prodockit-extensions package's own compiled CSS now (prodockit.pdf.css),
# not in this repo - see build.py's `prodockit.pdf` import. What's still
# worth checking from this repo's own test suite is the *integration*: this
# repo's currently-pinned prodockit version, combined with this repo's own
# extra.css/print.css, still avoids leaving a large forced blank gap before
# a heading/admonition/code block that immediately follows a nearly-full
# page - the exact failure mode each of these was originally caught from
# (a real page whose content happened to land at just the wrong point).
# Rather than reproducing each historical page's exact wording (fragile, and
# most of that content left for prodockit-userguide - see issue #49), these
# build a page with enough filler paragraphs to push the element under test
# close to a page boundary, then assert the *previous* page stays
# well-utilized (a small footer-sized gap, not a large forced one) - a more
# robust signal than requiring two specific pieces of text land on an exact
# page number, which normal, non-buggy reflow can also produce.

FILLER_PARAGRAPH = (
    "This is a filler paragraph used only to push subsequent content toward "
    "the bottom of the page, so the real element under test lands near a "
    "page boundary the way genuine report prose eventually would, without "
    "depending on any specific piece of report content to still exist. "
)

BLANK_GAP_THRESHOLD_PT = 150


def _filler(n):
    return "\n\n".join([FILLER_PARAGRAPH] * n)


def _blank_space_before_page_with(doc, marker):
    """Returns (blank_pt, target_page) - blank_pt is the unused vertical
    space at the bottom of the page immediately before the first page
    (after the Table of Contents) containing marker."""
    target_page = None
    for i in range(1, doc.page_count):
        if marker in doc[i].get_text():
            target_page = i
            break
    assert target_page is not None and target_page > 0, f"Expected to find {marker!r} on a page after the ToC"
    prev_page = doc[target_page - 1]
    blocks = [b for b in prev_page.get_text("dict")["blocks"] if b.get("type") == 0]
    max_y = max((b["bbox"][3] for b in blocks), default=0)
    return prev_page.rect.height - max_y, target_page


def test_real_grid_card_does_not_force_a_blank_page_gap_before_it(build_synthetic_pdf):
    """Regression test: a real grid card commonly wraps a whole tabbed-set
    (e.g. per-OS install instructions, all tabs stacked since WeasyPrint
    can't do interactive tabs) - often taller than a full page. The
    grid-card CSS's page-break-inside: avoid used to force the entire
    oversized card onto a fresh page as one atomic unit (unable to actually
    fit there either), leaving a large blank gap on the previous page."""
    doc = build_synthetic_pdf([("test.md", f"""# Filler Chapter

{_filler(15)}

### Target Heading

<div class="grid cards one-column" markdown>

-   :material-clock-fast:{{ .lg .middle }} __Do a thing__

    === "Option A"

        1. First step for option A.
        2. Second step for option A.
        3. Third step for option A.
        4. Fourth step for option A.

    === "Option B"

        1. First step for option B.
        2. Second step for option B.
        3. Third step for option B.
        4. Fourth step for option B.

    === "Option C"

        1. First step for option C.
        2. Second step for option C.
        3. Third step for option C.
        4. Fourth step for option C.

</div>
""")])
    try:
        blank, _ = _blank_space_before_page_with(doc, "Target Heading")
        assert blank < BLANK_GAP_THRESHOLD_PT, f"Expected a well-utilized page before the grid card, got {blank:.0f}pt of blank space"
    finally:
        doc.close()


def test_real_heading_and_its_short_paragraph_do_not_force_a_blank_page_gap(build_synthetic_pdf):
    """Regression test: a plain <p> had no break-inside/orphans/widows
    protection at all. Simply making every <p> unsplittable (break-inside:
    avoid) over-corrected - a short (e.g. 2-line) paragraph immediately
    after a heading became atomic with that heading too, and if the
    combined size didn't fit the page's remaining space, the *whole*
    heading+paragraph pair was pushed to a fresh page, leaving a large
    blank gap behind. orphans: 1 / widows: 2 replaces the blanket avoid: a
    short paragraph can still leave as few as 1 line behind (no gap
    forced) while a longer one avoids an ugly single-line widow if it does
    split."""
    doc = build_synthetic_pdf([("test.md", f"""# Filler Chapter

{_filler(15)}

### Target Heading

A short two-line paragraph immediately follows this heading, with nothing
else keeping them apart.
""")])
    try:
        blank, _ = _blank_space_before_page_with(doc, "Target Heading")
        assert blank < BLANK_GAP_THRESHOLD_PT, f"Expected a well-utilized page before the heading, got {blank:.0f}pt of blank space"
    finally:
        doc.close()


def test_real_admonition_does_not_force_a_blank_page_gap_before_it(build_synthetic_pdf):
    """Regression test: .admonition-title's own page-break-after: avoid had
    the same WeasyPrint quirk as headings' own page-break-after - even
    though .admonition itself already uses page-break-inside: auto, the
    title's own avoid-after still forced the *entire* admonition onto a
    fresh page rather than letting it start on the current one, leaving a
    large blank gap behind, even for a short 2-3 line admonition body that
    would easily have fit."""
    doc = build_synthetic_pdf([("test.md", f"""# Filler Chapter

{_filler(15)}

!!! note "Target Admonition"
    A short admonition body, only two or three lines long.
""")])
    try:
        blank, _ = _blank_space_before_page_with(doc, "Target Admonition")
        assert blank < BLANK_GAP_THRESHOLD_PT, f"Expected a well-utilized page before the admonition, got {blank:.0f}pt of blank space"
    finally:
        doc.close()


def test_real_large_code_block_does_not_force_a_blank_page_gap_before_it(build_synthetic_pdf):
    """Regression test: print.css's own "img, pre, blockquote,
    .tabbox-container { page-break-inside: avoid }" is fine for img/
    blockquote (naturally short/atomic) and is already overridden back to
    auto for .tabbox-container elsewhere in this stylesheet - but pre
    wasn't, so a large fenced code block hit the same WeasyPrint quirk
    already fixed for grid cards/table captions/admonitions/headings
    above: it forced itself entirely onto a fresh page rather than
    splitting, leaving a large blank gap on the previous page."""
    code_lines = "\n".join(f"line_{i} = {i}" for i in range(40))
    doc = build_synthetic_pdf([("test.md", f"""# Filler Chapter

{_filler(15)}

Introducing a large code example:

``` python
{code_lines}
```
""")])
    try:
        blank, _ = _blank_space_before_page_with(doc, "line_0 = 0")
        assert blank < BLANK_GAP_THRESHOLD_PT, f"Expected a well-utilized page before the code block, got {blank:.0f}pt of blank space"
    finally:
        doc.close()


def test_real_footnote_lands_near_its_reference_and_is_smaller(build_synthetic_pdf):
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
    Checks the footnote text lands on the same page as its reference,
    smaller than body text."""
    doc = build_synthetic_pdf([("test.md", """# Test Chapter

Here's a sentence with a footnote.[^1]

[^1]: This is the footnote.
""")])
    try:
        body_size = footnote_size = None
        body_page = footnote_page = None
        for i in range(1, doc.page_count):
            for block in doc[i].get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        if "Here's a sentence with a footnote" in span["text"]:
                            body_size, body_page = span["size"], i
                        elif "the footnote." in span["text"] or span["text"].strip() == "This is":
                            footnote_size, footnote_page = span["size"], i
        assert body_size is not None, "Expected to find the footnote reference sentence in the PDF"
        assert footnote_size is not None, "Expected to find the footnote's own text in the PDF"
        assert footnote_page == body_page, (
            f"Expected the footnote text on the same page as its reference (page {body_page}), "
            f"found it on page {footnote_page} instead"
        )
        assert footnote_size < body_size, (
            f"Expected footnote text ({footnote_size}pt) smaller than body text ({body_size}pt)"
        )
    finally:
        doc.close()
