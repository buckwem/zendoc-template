# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""captions batch: checks the PDF-side translation of pymdownx.blocks.caption
(see "Captions" in customise.md and issue #43) - figure-caption/table-caption
auto-numbering ("Figure <chapter>.<n>."/"Table <chapter>.<n>."), the plain
caption type staying unnumbered, manual number overrides and their effect on
the following auto-number, custom #id/.class overrides, prepend/append
position, and appendix-letter chapter ids.

Most checks here call preprocess_markdown() directly on a hand-written
markdown snippet (mirroring test_fences.py's style) rather than requiring a
full build - this feature's logic lives entirely in that one function
(zensical_caption_replacer()/table_caption_replacer() inside it), so a
synthetic snippet exercises the real code without the cost of a full PDF
build. A couple of end-to-end checks at the bottom cross-check the same
behaviour against the real, already-built PDF."""

import re
from textwrap import dedent

FIGURE_NUMBER = re.compile(r'<span class="caption-prefix">Figure ([^<]+)</span>')
TABLE_CAPTION_LINE = re.compile(r'^Table: (.+?)(?:\s*\{[^}]*\})?$', re.MULTILINE)


def _preprocess(build_pdf_module, tmp_path, source, chapter_id=None, caption_state=None):
    src_file = tmp_path / "source.md"
    src_file.write_text(dedent(source), encoding="utf-8")
    out_file = tmp_path / "output.md"

    build_pdf_module.preprocess_markdown(
        file_path=str(src_file),
        output_path=str(out_file),
        config={"docs_dir": "docs"},
        calculated_vars={},
        icon_registry={},
        placeholder_map={},
        temp_build_dir=str(tmp_path),
        mermaid_state={"count": 0},
        page_anchor_map={},
        chapter_id=chapter_id,
        caption_state=caption_state,
    )

    return out_file.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# parse_caption_modifier() - pure function, no build required.
# ---------------------------------------------------------------------------

def test_parse_caption_modifier_with_no_modifier(build_pdf_module):
    assert build_pdf_module.parse_caption_modifier(None) == (None, None, None, [])
    assert build_pdf_module.parse_caption_modifier("") == (None, None, None, [])


def test_parse_caption_modifier_prepend_and_append(build_pdf_module):
    assert build_pdf_module.parse_caption_modifier("<")[0] is True
    assert build_pdf_module.parse_caption_modifier(">")[0] is False


def test_parse_caption_modifier_manual_number(build_pdf_module):
    assert build_pdf_module.parse_caption_modifier("7")[1] == 7


def test_parse_caption_modifier_custom_id_and_classes(build_pdf_module):
    _, _, custom_id, extra_classes = build_pdf_module.parse_caption_modifier(
        "#custom-id.some-class.another-class"
    )
    assert custom_id == "custom-id"
    assert extra_classes == ["some-class", "another-class"]


def test_parse_caption_modifier_combines_all_tokens_together(build_pdf_module):
    prepend, manual_number, custom_id, extra_classes = build_pdf_module.parse_caption_modifier(
        "< 5 #my-id.my-class"
    )
    assert (prepend, manual_number, custom_id, extra_classes) == (True, 5, "my-id", ["my-class"])


# ---------------------------------------------------------------------------
# image_attrs_to_html() - pure function, no build required (see issue #55).
# ---------------------------------------------------------------------------

def test_image_attrs_to_html_with_no_attrs(build_pdf_module):
    assert build_pdf_module.image_attrs_to_html(None) == ''
    assert build_pdf_module.image_attrs_to_html('') == ''


def test_image_attrs_to_html_percentage_width_becomes_a_style(build_pdf_module):
    assert build_pdf_module.image_attrs_to_html('width="40%"') == ' style="width:40%"'


def test_image_attrs_to_html_bare_integer_width_becomes_an_attribute(build_pdf_module):
    assert build_pdf_module.image_attrs_to_html('width=300') == ' width="300"'


def test_image_attrs_to_html_combines_width_and_height_into_one_style(build_pdf_module):
    result = build_pdf_module.image_attrs_to_html('width="40%" height="2cm"')
    assert result == ' style="width:40%; height:2cm"'


def test_image_attrs_to_html_other_keys_become_plain_attributes(build_pdf_module):
    assert build_pdf_module.image_attrs_to_html('loading=lazy') == ' loading="lazy"'


def test_image_attrs_to_html_class_token_becomes_the_class_attribute(build_pdf_module):
    """See issue #54: a ".screenshot" token frames a screenshot image the
    same way in both outputs - this is the <img>'s own class, distinct from
    the <figure>'s class (zendoc-figure-caption etc.)."""
    assert build_pdf_module.image_attrs_to_html('.screenshot') == ' class="screenshot"'


def test_image_attrs_to_html_combines_width_and_class(build_pdf_module):
    result = build_pdf_module.image_attrs_to_html('width="40%" .screenshot')
    assert 'class="screenshot"' in result
    assert 'style="width:40%"' in result


def test_image_attrs_to_html_id_token_becomes_the_id_attribute(build_pdf_module):
    assert build_pdf_module.image_attrs_to_html('#my-img-id') == ' id="my-img-id"'


# ---------------------------------------------------------------------------
# figure-caption: numbering, chapter id, manual override, custom id/class,
# position, and the plain "caption" type staying unnumbered.
# ---------------------------------------------------------------------------

def test_figure_caption_is_numbered_with_the_page_chapter_id(build_pdf_module, tmp_path):
    result = _preprocess(
        build_pdf_module, tmp_path,
        """
        ![alt text](image.png)
        /// figure-caption
        A worked example
        ///
        """,
        chapter_id="3",
    )
    assert FIGURE_NUMBER.search(result).group(1) == "3.1."


def test_figure_caption_without_a_chapter_id_omits_the_chapter_prefix(build_pdf_module, tmp_path):
    result = _preprocess(
        build_pdf_module, tmp_path,
        """
        ![alt text](image.png)
        /// figure-caption
        A worked example
        ///
        """,
        chapter_id=None,
    )
    assert FIGURE_NUMBER.search(result).group(1) == "1."


def test_figure_caption_auto_increments_across_a_page(build_pdf_module, tmp_path):
    result = _preprocess(
        build_pdf_module, tmp_path,
        """
        ![first](image1.png)
        /// figure-caption
        First figure
        ///

        ![second](image2.png)
        /// figure-caption
        Second figure
        ///
        """,
        chapter_id="2",
    )
    numbers = [m.group(1) for m in FIGURE_NUMBER.finditer(result)]
    assert numbers == ["2.1.", "2.2."]


def test_figure_caption_manual_number_override_continues_from_there(build_pdf_module, tmp_path):
    result = _preprocess(
        build_pdf_module, tmp_path,
        """
        ![first](image1.png)
        /// figure-caption | 5
        Manually numbered figure
        ///

        ![second](image2.png)
        /// figure-caption
        Next figure picks up after the override
        ///
        """,
        chapter_id="2",
    )
    numbers = [m.group(1) for m in FIGURE_NUMBER.finditer(result)]
    assert numbers == ["2.5.", "2.6."]


def test_figure_caption_custom_id_and_class(build_pdf_module, tmp_path):
    result = _preprocess(
        build_pdf_module, tmp_path,
        """
        ![alt text](image.png)
        /// figure-caption | #custom-fig-id.my-class
        A worked example
        ///
        """,
        chapter_id="1",
    )
    assert 'id="custom-fig-id"' in result
    assert 'class="zendoc-figure-caption my-class"' in result


def test_figure_caption_preserves_the_images_percentage_width(build_pdf_module, tmp_path):
    """Regression test for issue #55: zensical_caption_replacer() used to
    build the <img> tag by hand from just the alt text and src, silently
    dropping the "{ width="40%" }" attribute block entirely - Pandoc's own
    image attribute handling never runs on this hand-written HTML, so
    without image_attrs_to_html() re-applying it, the image fell back to
    its raw intrinsic size (driven by whatever DPI the source file happens
    to be saved at) instead of 40% of its container, rendering far too
    large in the PDF."""
    result = _preprocess(
        build_pdf_module, tmp_path,
        """
        ![alt text](image.png){ width="40%" }
        /// figure-caption
        A worked example
        ///
        """,
        chapter_id="1",
    )
    assert 'style="width:40%"' in result


def test_figure_caption_preserves_the_images_pixel_width(build_pdf_module, tmp_path):
    """A bare, unit-less width (e.g. "300") is Pandoc's legacy width="N"
    HTML attribute (pixels), not a CSS style - see image_attrs_to_html()."""
    result = _preprocess(
        build_pdf_module, tmp_path,
        """
        ![alt text](image.png){ width=300 }
        /// figure-caption
        A worked example
        ///
        """,
        chapter_id="1",
    )
    assert 'width="300"' in result
    assert 'style="width:300"' not in result


def test_figure_caption_preserves_the_screenshot_class_on_the_image(build_pdf_module, tmp_path):
    """See issue #54: ".screenshot" must land on the <img> itself (framing
    it with a border/shadow - see extra.css and the equivalent PDF rule in
    main()'s compiled CSS), not on the <figure> - the figure's own class
    (zendoc-figure-caption etc.) is a separate attribute, set independently
    by zensical_caption_replacer() itself, and must be unaffected."""
    result = _preprocess(
        build_pdf_module, tmp_path,
        """
        ![alt text](image.png){ width="40%" .screenshot }
        /// figure-caption
        A worked example
        ///
        """,
        chapter_id="1",
    )
    assert '<img src="image.png" alt="alt text" class="screenshot" style="width:40%" />' in result
    assert 'class="zendoc-figure-caption"' in result


def test_figure_caption_without_a_width_attribute_is_unaffected(build_pdf_module, tmp_path):
    """No "{ ... }" block at all (this template's plain, unnumbered caption
    examples, e.g. the reference-style screenshots in customise.md) must
    still produce a plain <img> with no stray style/width attribute."""
    result = _preprocess(
        build_pdf_module, tmp_path,
        """
        ![alt text](image.png)
        /// figure-caption
        A worked example
        ///
        """,
        chapter_id="1",
    )
    assert '<img src="image.png" alt="alt text" />' in result


def test_figure_caption_appendix_letter_chapter_id(build_pdf_module, tmp_path):
    result = _preprocess(
        build_pdf_module, tmp_path,
        """
        ![alt text](image.png)
        /// figure-caption
        A worked example
        ///
        """,
        chapter_id="A",
    )
    assert FIGURE_NUMBER.search(result).group(1) == "A.1."


def test_figure_caption_defaults_to_appending_after_the_image(build_pdf_module, tmp_path):
    result = _preprocess(
        build_pdf_module, tmp_path,
        """
        ![alt text](image.png)
        /// figure-caption
        A worked example
        ///
        """,
        chapter_id="1",
    )
    assert result.index("<img") < result.index("<figcaption")


def test_figure_caption_prepend_modifier_puts_caption_before_the_image(build_pdf_module, tmp_path):
    result = _preprocess(
        build_pdf_module, tmp_path,
        """
        ![alt text](image.png)
        /// figure-caption | <
        A worked example
        ///
        """,
        chapter_id="1",
    )
    assert result.index("<figcaption") < result.index("<img")


def test_plain_caption_type_stays_unnumbered(build_pdf_module, tmp_path):
    result = _preprocess(
        build_pdf_module, tmp_path,
        """
        ![alt text](image.png)
        /// caption
        A plain, unnumbered caption
        ///
        """,
        chapter_id="1",
    )
    assert "caption-prefix" not in result
    assert 'id="figure-1-1"' not in result
    assert "A plain, unnumbered caption" in result


def test_no_caption_syntax_leaks_into_the_figure_output(build_pdf_module, tmp_path):
    result = _preprocess(
        build_pdf_module, tmp_path,
        """
        ![alt text](image.png)
        /// figure-caption
        A worked example
        ///
        """,
        chapter_id="1",
    )
    assert "///" not in result


# ---------------------------------------------------------------------------
# table-caption: Pandoc's native "Table: ..." syntax, numbering, position
# (recorded in caption_state for main() to turn into a CSS override), and
# the plain "caption" type's original top-position default.
# ---------------------------------------------------------------------------

TABLE_SOURCE = """
| A | B |
| - | - |
| 1 | 2 |
"""


def test_table_caption_uses_pandocs_native_syntax_after_the_table(build_pdf_module, tmp_path):
    result = _preprocess(
        build_pdf_module, tmp_path,
        TABLE_SOURCE + """
        /// table-caption
        A worked example
        ///
        """,
        chapter_id="4",
    )
    m = TABLE_CAPTION_LINE.search(result)
    assert m is not None
    assert m.group(1).startswith("Table 4.1. ")
    assert result.index("| 1 | 2 |") < result.index("Table:")


def test_table_caption_auto_increments_independently_of_figures(build_pdf_module, tmp_path):
    result = _preprocess(
        build_pdf_module, tmp_path,
        TABLE_SOURCE + """
        /// table-caption
        First table
        ///
        """ + TABLE_SOURCE + """
        /// table-caption
        Second table
        ///
        """,
        chapter_id="1",
    )
    captions = [m.group(1) for m in TABLE_CAPTION_LINE.finditer(result)]
    assert captions[0].startswith("Table 1.1. ")
    assert captions[1].startswith("Table 1.2. ")


def test_table_caption_custom_id_and_class(build_pdf_module, tmp_path):
    result = _preprocess(
        build_pdf_module, tmp_path,
        TABLE_SOURCE + """
        /// table-caption | #custom-table-id.my-class
        A worked example
        ///
        """,
        chapter_id="1",
    )
    assert "#custom-table-id" in result
    assert ".my-class" in result


def test_table_caption_only_requests_top_position_when_explicitly_prepended(build_pdf_module, tmp_path):
    caption_state = {}
    _preprocess(
        build_pdf_module, tmp_path,
        TABLE_SOURCE + """
        /// table-caption
        Default position, no "| <" modifier
        ///
        """,
        chapter_id="1",
        caption_state=caption_state,
    )
    assert not caption_state.get("prepend_table_ids")


def test_table_caption_with_prepend_modifier_requests_top_position(build_pdf_module, tmp_path):
    caption_state = {}
    result = _preprocess(
        build_pdf_module, tmp_path,
        TABLE_SOURCE + """
        /// table-caption | <
        Explicitly prepended
        ///
        """,
        chapter_id="1",
        caption_state=caption_state,
    )
    m = re.search(r'\{#([\w-]+)', result)
    assert m is not None
    assert m.group(1) in caption_state.get("prepend_table_ids", set())


def test_plain_table_caption_defaults_to_top_position_for_backward_compatibility(build_pdf_module, tmp_path):
    caption_state = {}
    result = _preprocess(
        build_pdf_module, tmp_path,
        TABLE_SOURCE + """
        /// caption
        A plain, unnumbered table caption
        ///
        """,
        chapter_id="1",
        caption_state=caption_state,
    )
    m = TABLE_CAPTION_LINE.search(result)
    assert m is not None
    assert m.group(1) == "A plain, unnumbered table caption"
    id_match = re.search(r'\{#([\w-]+)', result)
    assert id_match is not None
    assert id_match.group(1) in caption_state.get("prepend_table_ids", set())


def test_no_caption_syntax_leaks_into_the_table_output(build_pdf_module, tmp_path):
    result = _preprocess(
        build_pdf_module, tmp_path,
        TABLE_SOURCE + """
        /// table-caption
        A worked example
        ///
        """,
        chapter_id="1",
    )
    assert "///" not in result


# ---------------------------------------------------------------------------
# End-to-end: the real, already-built PDF (see docs/starthere/installtooling.md's
# "Fork and Clone Comparison at a Glance" table) - cross-checks that the same
# behaviour verified above against synthetic snippets also holds for real
# content once concatenated, numbered, and rendered by Pandoc/WeasyPrint.
# ---------------------------------------------------------------------------

REAL_TABLE_NUMBER = re.compile(r"^Table (\d+\.\d+\.) Fork and Clone Comparison at a Glance", re.MULTILINE)


def test_real_fork_clone_table_caption_is_numbered_in_the_built_pdf(pdf_full_text):
    joined = "\n".join(pdf_full_text)
    m = REAL_TABLE_NUMBER.search(joined)
    assert m is not None, "Expected a numbered 'Fork and Clone Comparison at a Glance' table caption in the PDF"


CAPTION_SYNTAX_LEAK = re.compile(r"^\s*(?:///|--/)\s*(figure-caption|table-caption|caption)\b", re.MULTILINE)


def _chapter_page_range(pdf_full_text, heading_prefix):
    """Returns (start, end) page indexes [start, end) for the chapter whose H1
    starts with heading_prefix (e.g. "11. Customisation") - start is the page
    the heading itself is on, end is the page the *next* numbered H1 starts
    on (or len(pdf_full_text) if it's the last chapter)."""
    start = None
    for i, text in enumerate(pdf_full_text):
        if start is None and text.strip().startswith(heading_prefix):
            start = i
            continue
        if start is not None and re.match(r"^\d+\.\s", text.strip()):
            return start, i
    assert start is not None, f"Couldn't find a chapter starting with '{heading_prefix}' in the PDF"
    return start, len(pdf_full_text)


def test_no_unrelated_page_shows_literal_caption_block_syntax(pdf_full_text):
    """docs/starthere/zensicalbasics.md ("10. Zensical basics") and
    docs/starthere/customise.md's own "Captions" section ("11. Customisation")
    both intentionally show "/// figure-caption"/"/// table-caption"/
    "/// caption" as literal code-block example text (see test_content.py's
    similar carve-out for attr_list syntax). PyMuPDF's text extraction renders
    a literal "///" as "--/" (a font-ligature extraction artifact, confirmed
    against a rendered screenshot of the actual page - the real PDF glyphs are
    correct), so the leak check below looks for either spelling. Every other
    page's caption blocks should have been fully translated, not left as
    literal, visible syntax."""
    example_chapter_ranges = [
        _chapter_page_range(pdf_full_text, "10. Zensical basics"),
        _chapter_page_range(pdf_full_text, "11. Customisation"),
    ]
    leaked_pages = [
        i for i, text in enumerate(pdf_full_text)
        if CAPTION_SYNTAX_LEAK.search(text)
        and not any(start <= i < end for start, end in example_chapter_ranges)
    ]
    assert not leaked_pages, f"Leaked caption block syntax on PDF page(s): {leaked_pages}"
