# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""markdown_foundations batch: checks the core Markdown syntax that used to
be taught on the User Guide's markdown.md page (see issue #49 - that page
moved to the separate prodockit-userguide repo) - headings, text
formatting, links/images, lists (including the 4-space nesting rule),
code blocks, tables, horizontal rules, task lists, and blockquotes -
actually renders the way that page says it does.

Renders hand-written snippets through a real markdown.Markdown() instance,
built from this project's own zensical.toml extension config (see
conftest.py's markdown_extension_config fixture) rather than a hardcoded
extension list, so a change to zensical.toml's
[project.markdown_extensions.*] section is automatically reflected here
instead of silently drifting out of sync. This is the same "call the real
thing on a synthetic snippet" approach test_fences.py uses, extended to
Zensical's website-side Markdown pipeline (markdown.md's syntax isn't
PDF-specific, so there's no PDF-pipeline function to call directly the way
test_fences.py does) - so, like that batch, this one runs without building
anything first. One exception: test_pandoc_nests_a_two_space_list_unlike_python_markdown
shells out to the real `pandoc` binary directly (same tool, same invocation
shape the PDF pipeline itself uses) to check a genuine website/PDF rendering
discrepancy - see issue #70."""

import subprocess
import textwrap

import markdown
import pytest


def dedent(text):
    return textwrap.dedent(text).strip("\n") + "\n"


@pytest.fixture(scope="module")
def render(markdown_extension_config):
    """Returns a render(markdown_text) -> html function, backed by one
    shared markdown.Markdown() instance (rebuilding it per call is
    unnecessary work - Markdown.reset() clears per-document state like
    heading-id collision counters between calls, matching what a fresh
    instance would give each snippet)."""
    extensions, extension_configs = markdown_extension_config
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


def test_pandoc_nests_a_two_space_list_unlike_python_markdown():
    """Not a synthetic markdown.Markdown() check like the rest of this
    file - a real subprocess call to the actual `pandoc` binary
    prodockit.pdf.build.build_pdf() itself shells out to, since this is
    specifically about how the *PDF's* engine, not the website's, handles
    the same source.

    Documents a general engine discrepancy worth knowing about (see issue
    #70): Pandoc's markdown reader nests a sub-list at just 2-space
    indentation - no 4-space requirement - unlike Python-Markdown's strict
    4-space rule (test_nested_list_at_two_spaces_does_not_nest, once in
    this file, was deleted once markdown.md's own 2-space example - the
    concrete case that first surfaced this - was fixed to use 4 spaces).
    Both engines agree at 4 spaces, so any *current* content in this
    template is unaffected; this is a tripwire for the next time someone
    writes a 2-space nested list assuming "it renders the same everywhere" -
    it doesn't, the two outputs would disagree on the actual structure,
    not just look different."""
    result = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "html"],
        input="- Item 1\n- Item 2\n  - Nested item\n",
        capture_output=True, text=True, check=True,
    )
    flat_html = result.stdout.replace("\n", "")
    assert "<li>Item 2<ul>" in flat_html, (
        "Pandoc no longer nests a 2-space sub-list - the cross-output "
        "inconsistency this test documents may have resolved itself; "
        "worth a comment on issue #70 either way"
    )


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
