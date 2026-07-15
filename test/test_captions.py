# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""captions batch: checks pymdownx.blocks.caption's figure-caption/
table-caption auto-numbering (see "Captions" in customise.md and issue #43)
against the real, already-built PDF.

Before zendoc-template#92, this batch mostly called preprocess_markdown()
directly on hand-written snippets to exercise build_pdf.py's own regex
reimplementation of pymdownx.blocks.caption's numbering/position/id/class
handling (zensical_caption_replacer()/table_caption_replacer()). That
reimplementation is gone: build_pdf.py now renders every page through the
real pymdownx.blocks.caption extension (see render_page_html()), so manual
number overrides, custom ids/classes, and prepend/append position are
pymdownx's own, already-tested behaviour, identical to the website's -
nothing build_pdf.py-specific left to unit-test there. The one thing that
*is* build_pdf.py-specific is prepending the current chapter number/
appendix letter in front of pymdownx's own per-page auto-number (the
Figure() Lua handler in main()) - covered below against real content."""

import re

from conftest import chapter_page_range

REAL_TABLE_NUMBER = re.compile(r"^Table (\d+\.\d+\.) Fork and Clone Comparison at a Glance", re.MULTILINE)


def test_real_fork_clone_table_caption_is_numbered_in_the_built_pdf(pdf_full_text):
    joined = "\n".join(pdf_full_text)
    m = REAL_TABLE_NUMBER.search(joined)
    assert m is not None, "Expected a numbered 'Fork and Clone Comparison at a Glance' table caption in the PDF"


def test_real_figure_caption_image_is_horizontally_centered_under_its_caption(pdf_doc):
    """Regression test: a <figure>'s own default centering relies on the
    compiled stylesheet's "figure { text-align: center }" rule (see
    build_pdf.py's main()) - the <img> is a naturally inline-level element,
    positioned by its parent's text-align, so without it the image sits at
    its default left-aligned position while the figcaption text ends up
    centered anyway (WeasyPrint's own default for figcaption), visibly
    misaligning the image under its own caption. Checks the real "Initial
    commit" figure in the built PDF: the image's horizontal center should
    match its caption's."""
    image_bbox = None
    caption_bbox = None
    for page in pdf_doc:
        blocks = page.get_text("dict")["blocks"]
        image_bboxes = [b["bbox"] for b in blocks if b.get("type") == 1]
        for block in blocks:
            if block.get("type") != 0:
                continue
            text = "".join(s["text"] for line in block.get("lines", []) for s in line["spans"])
            if "Figure" in text and "Initial commit" in text:
                caption_bbox = block["bbox"]
                # The image directly above this caption - not necessarily
                # adjacent in blocks[] order (images can be listed out of
                # visual reading order - see the vertical-gap match here
                # instead of relying on list position).
                above = [b for b in image_bboxes if b[3] <= caption_bbox[1] + 1]
                if above:
                    image_bbox = min(above, key=lambda b: caption_bbox[1] - b[3])
                break
        if caption_bbox is not None:
            break

    assert caption_bbox is not None, "Expected to find the 'Initial commit' figure caption in the PDF"
    assert image_bbox is not None, "Expected an image immediately before the 'Initial commit' caption"

    image_center = (image_bbox[0] + image_bbox[2]) / 2
    caption_center = (caption_bbox[0] + caption_bbox[2]) / 2
    assert abs(image_center - caption_center) < 1, (
        f"Image center ({image_center}) doesn't match caption center ({caption_center})"
    )


CAPTION_SYNTAX_LEAK = re.compile(r"^\s*(?:///|--/)\s*(figure-caption|table-caption|caption)\b", re.MULTILINE)


def test_no_unrelated_page_shows_literal_caption_block_syntax(pdf_doc, pdf_full_text):
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
        chapter_page_range(pdf_doc, "10. Zensical basics"),
        chapter_page_range(pdf_doc, "11. Customisation"),
    ]
    leaked_pages = [
        i for i, text in enumerate(pdf_full_text)
        if CAPTION_SYNTAX_LEAK.search(text)
        and not any(start <= i < end for start, end in example_chapter_ranges)
    ]
    assert not leaked_pages, f"Leaked caption block syntax on PDF page(s): {leaked_pages}"
