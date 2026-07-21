# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""captions batch: checks pymdownx.blocks.caption's figure-caption/
table-caption auto-numbering (see "Captions" in the User Guide's
customise.md and issue #43) against a real, synthetic PDF built through the
actual production pipeline (see conftest.py's build_synthetic_pdf fixture).

Before prodockit-template#92, this batch mostly called preprocess_markdown()
directly on hand-written snippets to exercise a since-removed regex
reimplementation of pymdownx.blocks.caption's numbering/position/id/class
handling (zensical_caption_replacer()/table_caption_replacer()). That
reimplementation is gone: prodockit.pdf now renders every page through the
real pymdownx.blocks.caption extension (see render_page_html()), so manual
number overrides, custom ids/classes, and prepend/append position are
pymdownx's own, already-tested behaviour, identical to the website's -
nothing PDF-pipeline-specific left to unit-test there. The one thing that
*is* PDF-pipeline-specific is prepending the current chapter number/
appendix letter in front of pymdownx's own per-page auto-number (the
Figure() Lua handler prodockit.pdf.build.build_pdf() generates) - covered
below.

These used to check specific real pages (installtooling.md/customise.md's
"Fork and Clone Comparison at a Glance" table, customise.md/startediting.md's
"Initial commit" figure, shcommands.md's "Basic navigation commands" table,
originality.md's AI-use table) - see issue #49: most of those pages moved to
the separate prodockit-userguide repo, so the tests below now build their own
small synthetic pages through the real pipeline instead, keeping the
regression coverage independent of which report content happens to exist."""

import re

_ITALIC_FLAG = 1 << 1

CAPTION_SYNTAX_LEAK = re.compile(r"^\s*(?:///|--/)\s*(figure-caption|table-caption|caption)\b", re.MULTILINE)


def test_real_table_caption_is_numbered_with_its_chapter_prefix(build_synthetic_pdf):
    doc = build_synthetic_pdf([
        ("test.md", """# Test Chapter

/// table-caption
Fork and Clone Comparison at a Glance
///

| Feature | Fork | Clone |
|----|----|---|
| Where's the copy made? | Remote host | Local computer |
"""),
    ])
    try:
        joined = "\n".join(page.get_text() for page in doc)
        assert re.search(r"Table \d+\.\d+\. Fork and Clone Comparison at a Glance", joined), (
            "Expected a chapter-prefixed, numbered table caption in the PDF"
        )
    finally:
        doc.close()


def test_real_figure_caption_image_is_horizontally_centered_under_its_caption(build_synthetic_pdf):
    """Regression test: a <figure>'s own default centering relies on the
    compiled stylesheet's "figure { text-align: center }" rule (see
    prodockit.pdf.build.build_pdf()) - the <img> is a naturally inline-level element,
    positioned by its parent's text-align, so without it the image sits at
    its default left-aligned position while the figcaption text ends up
    centered anyway (WeasyPrint's own default for figcaption), visibly
    misaligning the image under its own caption."""
    doc = build_synthetic_pdf([
        ("test.md", """# Test Chapter

![Test image](assets/logo_black.png){ width="40%" .screenshot }
/// figure-caption
Test figure caption
///
"""),
    ])
    try:
        image_bbox = None
        caption_bbox = None
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            image_bboxes = [b["bbox"] for b in blocks if b.get("type") == 1]
            for block in blocks:
                if block.get("type") != 0:
                    continue
                text = "".join(s["text"] for line in block.get("lines", []) for s in line["spans"])
                if "Figure" in text and "Test figure caption" in text:
                    caption_bbox = block["bbox"]
                    above = [b for b in image_bboxes if b[3] <= caption_bbox[1] + 1]
                    if above:
                        image_bbox = min(above, key=lambda b: caption_bbox[1] - b[3])
                    break
            if caption_bbox is not None:
                break

        assert caption_bbox is not None, "Expected to find the figure caption in the PDF"
        assert image_bbox is not None, "Expected an image immediately before the figure caption"

        image_center = (image_bbox[0] + image_bbox[2]) / 2
        caption_center = (caption_bbox[0] + caption_bbox[2]) / 2
        assert abs(image_center - caption_center) < 1, (
            f"Image center ({image_center}) doesn't match caption center ({caption_center})"
        )
    finally:
        doc.close()


def test_real_prepend_table_caption_appears_above_its_table(build_synthetic_pdf):
    """Regression test (prodockit-template#93): pymdownx.blocks.caption's own
    HTML places a "| <" (prepend) caption physically before its table in
    the DOM, but Pandoc's Figure AST node stores Caption and content as two
    separate fields regardless of source order, and Pandoc's own HTML
    writer always re-emits the caption *after* the content when
    serializing Figure back to HTML - discarding the prepend positioning
    entirely (confirmed directly, isolated test: a <figcaption> placed
    first in the source HTML still came out last in Pandoc's own HTML
    writer output). render_page_html() works around this by retagging a
    prepend-position caption to a <div> before Pandoc parses it (a Div's
    children ARE emitted in original document order)."""
    doc = build_synthetic_pdf([
        ("test.md", """# Test Chapter

/// table-caption | <
Prepend Position Example
///

| Tool Used | Explain How Used |
|---|---|
| ChatGPT | Drafting an outline |
"""),
    ])
    try:
        caption_y = None
        header_y = None
        for page in doc:
            for block in page.get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue
                text = "".join(s["text"] for line in block.get("lines", []) for s in line["spans"])
                if "Prepend Position Example" in text:
                    caption_y = block["bbox"][1]
                if "Tool Used" in text and "Explain How Used" in text:
                    header_y = block["bbox"][1]
            if caption_y is not None and header_y is not None:
                break
        assert caption_y is not None, "Expected to find the prepend-position table caption in the PDF"
        assert header_y is not None, "Expected to find the table's own header row in the PDF"
        assert caption_y < header_y, (
            f"Expected the prepend-position caption (y={caption_y}) above its table's header row "
            f"(y={header_y}) - found it below instead"
        )
    finally:
        doc.close()


def test_real_table_caption_is_italicised(build_synthetic_pdf):
    """Regression test: the compiled stylesheet's caption-styling rule used
    to be "table caption {}", which only ever matches a literal
    <table><caption> element - something pymdownx.blocks.caption never
    produces (a <figcaption> inside a <figure> for the default
    append-position case, or a first-child <p> once render_page_html()
    unwraps a prepend-position caption into a <div>) - dead code left over
    from the old regex pipeline, silently never matching once that
    pipeline was retired."""
    doc = build_synthetic_pdf([
        ("test.md", """# Test Chapter

/// table-caption
Basic navigation commands
///

| Command | Description |
|---|---|
| ls | list files |
"""),
    ])
    try:
        for page in doc:
            for block in page.get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        if "Basic navigation commands" in span["text"]:
                            assert span["flags"] & _ITALIC_FLAG, (
                                f"Expected the table caption to be italicised, got flags={span['flags']}"
                            )
                            return
        raise AssertionError("Expected to find the table caption in the PDF")
    finally:
        doc.close()


def test_caption_syntax_shown_as_a_code_example_does_not_leak_elsewhere(build_synthetic_pdf):
    """Documentation pages (see the User Guide's zensicalbasics.md/
    customise.md "Captions" sections) intentionally show "/// figure-caption"/
    "/// table-caption"/"/// caption" as literal code-block example text -
    that's correct, expected output there. Every *other* page's real caption
    blocks should be fully translated instead, never left as literal, visible
    syntax. Builds one page showing the syntax inside a fenced code example
    (expected to leak, since that's the point of a code example) and a
    second page using the same syntax for real (expected not to leak), and
    checks the leak only shows up on the illustrative page."""
    doc = build_synthetic_pdf([
        ("example.md", """# Example Chapter

Here's how to caption a table:

``` markdown
/// table-caption
My caption
///
```
"""),
        ("real.md", """# Real Chapter

/// table-caption
My real caption
///

| A | B |
|---|---|
| 1 | 2 |
"""),
    ])
    try:
        pdf_full_text = [page.get_text() for page in doc]
        leaked_pages = [i for i, text in enumerate(pdf_full_text) if CAPTION_SYNTAX_LEAK.search(text)]
        joined = "\n".join(pdf_full_text)
        assert leaked_pages, "Expected the fenced code example to show the literal caption syntax"
        assert "My real caption" in joined, "Expected the real caption block to render its caption text"
        for i in leaked_pages:
            assert "Example Chapter" in pdf_full_text[i] or "1. Example Chapter" in pdf_full_text[i], (
                f"Literal caption syntax leaked outside the code-example page, on PDF page {i}: {pdf_full_text[i]!r}"
            )
    finally:
        doc.close()
