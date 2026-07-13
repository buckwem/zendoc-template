# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""markdown_foundations batch: checks the core Markdown syntax taught in
docs/starthere/markdown.md ("9. Markdown basics") - headings, text
formatting, links/images, lists (including the 4-space nesting rule),
code blocks, tables, horizontal rules, task lists, and blockquotes -
actually renders the way that page says it does.

Renders hand-written snippets through a real markdown.Markdown() instance,
built from this project's own zensical.toml extension config (see
_markdown_extensions() below) rather than a hardcoded extension list, so a
change to zensical.toml's [project.markdown_extensions.*] section is
automatically reflected here instead of silently drifting out of sync.
This is the same "call the real thing on a synthetic snippet" approach
test_fences.py uses, extended to Zensical's website-side Markdown pipeline
(markdown.md's syntax isn't PDF-specific, so there's no build_pdf.py
function to call directly the way test_fences.py does) - so, like that
batch, this one runs without building anything first."""

import textwrap

import markdown
import pytest


def dedent(text):
    return textwrap.dedent(text).strip("\n") + "\n"


def _flatten_extensions(extensions_config, prefix=""):
    """Flattens zensical.toml's nested [project.markdown_extensions.*]
    tables into markdown.Markdown()'s flat "dotted.name" extension list -
    e.g. {"pymdownx": {"betterem": {}}} becomes "pymdownx.betterem". A
    table counts as a nested group (recursed into) only if every one of its
    own values is itself a table - otherwise it's a leaf extension's own
    config dict (e.g. pymdownx.highlight's anchor_linenums/line_spans/
    pygments_lang_class are config values, not nested extensions)."""
    flat = {}
    for key, value in extensions_config.items():
        dotted = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict) and value and all(isinstance(v, dict) for v in value.values()):
            flat.update(_flatten_extensions(value, dotted))
        else:
            flat[dotted] = value
    return flat


def _markdown_extensions(zensical_config):
    """Returns (extensions, extension_configs) for markdown.Markdown(),
    built from this project's real [project.markdown_extensions.*] config.
    Skips zensical.extensions.* (glightbox, macros) - these are Zensical's
    own runtime integrations, not standalone pip-installable Markdown
    extensions, and skips pymdownx.emoji - its emoji_index/emoji_generator
    config values are dotted references to zensical.extensions.emoji
    callables that only Zensical's own loader resolves; plain
    markdown.Markdown() takes them as literal (non-callable) strings and
    errors. Neither is needed to exercise anything documented in "Markdown
    basics" (emoji is covered separately in "Zensical basics")."""
    raw = zensical_config.get("project", {}).get("markdown_extensions", {})
    flat = _flatten_extensions(raw)
    extensions = [
        name for name in flat
        if not name.startswith("zensical.extensions") and name != "pymdownx.emoji"
    ]
    extension_configs = {name: flat[name] for name in extensions if flat[name]}
    return extensions, extension_configs


@pytest.fixture(scope="module")
def render(zensical_config):
    """Returns a render(markdown_text) -> html function, backed by one
    shared markdown.Markdown() instance (rebuilding it per call is
    unnecessary work - Markdown.reset() clears per-document state like
    heading-id collision counters between calls, matching what a fresh
    instance would give each snippet)."""
    extensions, extension_configs = _markdown_extensions(zensical_config)
    md = markdown.Markdown(extensions=extensions, extension_configs=extension_configs)

    def render(text):
        md.reset()
        return md.convert(dedent(text) if not text.endswith("\n") else text)

    return render


# ---------------------------------------------------------------------------
# Headings
# ---------------------------------------------------------------------------

def test_all_six_heading_levels_render(render):
    html = render("""
        # H1 Heading
        ## H2 Heading
        ### H3 Heading
        #### H4 Heading
        ##### H5 Heading
        ###### H6 Heading
    """)
    for level in range(1, 7):
        assert f"<h{level}" in html, f"h{level} missing from: {html}"


def test_heading_gets_a_toc_permalink_anchor(render):
    """toc's permalink = true (zensical.toml) - the "¶" anchor markdown.md
    itself describes next to every heading on the live site."""
    html = render("# Some Heading")
    assert 'class="headerlink"' in html
    assert "&para;" in html


def test_attr_list_overrides_a_heading_id(render):
    html = render("## Heading {: #custom-id }")
    assert 'id="custom-id"' in html


# ---------------------------------------------------------------------------
# Text formatting
# ---------------------------------------------------------------------------

def test_bold_italic_strikethrough_and_inline_code(render):
    html = render("**bold text** *italic text* ***bold and italic*** ~~strikethrough~~ `inline code`")
    assert "<strong>bold text</strong>" in html
    assert "<em>italic text</em>" in html
    assert "<em><strong>bold and italic</strong></em>" in html or "<strong><em>bold and italic</em></strong>" in html
    assert "<del>strikethrough</del>" in html
    assert "<code>inline code</code>" in html


def test_betterem_handles_nested_mixed_emphasis(render):
    """pymdownx.betterem's whole reason for being here, per markdown.md:
    more consistent than core Python-Markdown at exactly this case."""
    html = render("**bold _and italic_**")
    assert "<strong>" in html and "<em>" in html
    assert "and italic" in html


def test_tilde_subscript_and_caret_superscript_underline(render):
    """pymdownx.caret's ^^text^^ renders as the semantic <ins> tag (not
    <u>) with no insert="u" option set in zensical.toml - browsers
    underline <ins> by default, which is why markdown.md can accurately
    describe it as "underline" even though the tag itself is <ins>."""
    html = render("H~2~O and A^T^A and ^^underline^^")
    assert "<sub>2</sub>" in html
    assert "<sup>T</sup>" in html
    assert "<ins>underline</ins>" in html


# ---------------------------------------------------------------------------
# Links and images
# ---------------------------------------------------------------------------

def test_basic_link_and_titled_link(render):
    html = render("""
        [Link text](https://example.com)
        [Link with title](https://example.com "Hover title")
    """)
    assert '<a href="https://example.com">Link text</a>' in html
    assert 'title="Hover title"' in html


def test_reference_style_link_resolves(render):
    html = render("""
        [Reference-style link][example-ref]

        [example-ref]: https://example.com "Hover title"
    """)
    assert '<a href="https://example.com"' in html
    assert "Reference-style link" in html


def test_image_and_titled_image(render):
    html = render("""
        ![Alt text](image.jpg)
        ![Image with title](image.jpg "Image title")
    """)
    assert '<img alt="Alt text" src="image.jpg"' in html
    assert 'title="Image title"' in html


def test_attr_list_on_a_link(render):
    html = render('[Link text](https://example.com){: .external-link }')
    assert 'class="external-link"' in html


def test_magiclink_autolinks_a_bare_url(render):
    html = render("See https://example.com for details.")
    assert '<a href="https://example.com"' in html


# ---------------------------------------------------------------------------
# Lists - including the 4-space nesting rule
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("marker", ["-", "*", "+"])
def test_unordered_list_markers(render, marker):
    html = render(f"{marker} Item 1\n{marker} Item 2\n")
    assert html.count("<li>") == 2


def test_nested_list_at_four_spaces_actually_nests(render):
    """Python-Markdown's own "4-space rule" (see
    https://python-markdown.github.io/#differences): a sub-list must be
    indented by exactly 4 spaces (or one tab) per nesting level to be
    recognised as nested rather than a sibling item at the same level."""
    html = render("- Item 1\n- Item 2\n    - Nested item\n")
    assert "<li>Item 2<ul>" in html.replace("\n", ""), html


def test_nested_list_at_two_spaces_does_not_nest(render):
    """The flip side of the 4-space rule, and a real trap: markdown.md's
    own "Unordered lists" example currently uses 2-space indentation for
    its "Nested item" line - per Python-Markdown's strict 4-space
    requirement, that does NOT nest; it renders as a third flat, sibling
    list item (see issue #70). This test documents that as the actual,
    current rendered behaviour of that example - once #70 fixes the
    example to use 4 spaces, this test should be deleted (and
    test_nested_list_at_four_spaces_actually_nests above already covers
    the correct, 4-space form)."""
    html = render("- Item 1\n- Item 2\n  - Nested item\n")
    flat_html = html.replace("\n", "")
    assert "<li>Item 2<ul>" not in flat_html, (
        "2-space indentation now nests - Python-Markdown's tab_length must have "
        "changed from the default of 4; markdown.md's own example may need revisiting"
    )
    assert flat_html.count("<li>") == 3


def test_ordered_list_renumbers_from_the_first_number(render):
    """markdown.md: Python-Markdown renumbers based on the *first* number
    used, so repeating "1." for every item is a common shorthand."""
    html = render("1. First item\n1. Second item\n1. Third item\n")
    assert "<ol>" in html
    assert html.count("<li>") == 3


def test_definition_list(render):
    html = render("""
        Term
        :   Definition of the term, indented under it.

        Second term
        :   First definition.
        :   A second definition for the same term.
    """)
    assert "<dl>" in html
    assert "<dt>Term</dt>" in html
    assert html.count("<dd>") == 3


# ---------------------------------------------------------------------------
# Code blocks
# ---------------------------------------------------------------------------

def test_fenced_code_block_with_language_gets_highlighted(render):
    html = render("""
        ```javascript
        function hello() {
          console.log("Hello, world!");
        }
        ```
    """)
    assert "<pre" in html
    assert "highlight" in html or "codehilite" in html


def test_superfences_nests_a_fence_inside_a_list_at_four_spaces(render):
    """markdown.md: superfences (unlike core fenced_code) lets a fenced
    code block nest inside a list item - subject to the same 4-space rule
    as any other nested block content."""
    html = render("""
        - Item with a nested code block:

            ```python
            print("nested")
            ```
    """)
    assert "<ul>" in html
    assert "print" in html
    assert "<pre" in html


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

def test_table_with_column_alignment(render):
    html = render("""
        | Left-aligned | Centred | Right-aligned |
        |:-------------|:-------:|--------------:|
        | Row 1        | Data    | Data          |
        | Row 2        | Data    | Data          |
    """)
    assert "<table>" in html
    assert 'style="text-align: left;"' in html
    assert 'style="text-align: center;"' in html
    assert 'style="text-align: right;"' in html


# ---------------------------------------------------------------------------
# Horizontal rule
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rule", ["---", "***", "___"])
def test_horizontal_rule_variants(render, rule):
    html = render(f"Above\n\n{rule}\n\nBelow")
    assert "<hr" in html


# ---------------------------------------------------------------------------
# Task lists
# ---------------------------------------------------------------------------

def test_task_list_renders_checkboxes(render):
    html = render("- [x] Completed task\n- [ ] Incomplete task\n")
    assert html.count('type="checkbox"') == 2
    assert "checked" in html


# ---------------------------------------------------------------------------
# Blockquotes
# ---------------------------------------------------------------------------

def test_blockquote_and_nested_blockquote(render):
    html = render("> This is a blockquote\n> Multiple lines\n>> Nested quote\n")
    assert html.count("<blockquote>") == 2


# ---------------------------------------------------------------------------
# Quick tips
# ---------------------------------------------------------------------------

def test_escaped_character_is_not_formatted(render):
    html = render(r"\*not italic\*")
    assert "<em>" not in html
    assert "*not italic*" in html


def test_attr_list_on_a_paragraph(render):
    html = render("A paragraph with a class.\n{: .my-class }")
    assert 'class="my-class"' in html


def test_line_break_needs_two_trailing_spaces(render):
    """markdown.md: two-or-more trailing spaces before the newline forces a
    line break within the same paragraph; a single trailing space (or
    none) doesn't."""
    with_break = render("Line one  \nLine two\n")
    without_break = render("Line one\nLine two\n")
    assert "<br" in with_break
    assert "<br" not in without_break
