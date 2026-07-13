# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""numbering batch: checks the PDF's chapter/appendix numbering (see issue
#24) is internally consistent - numeric chapters sequential with no gaps or
duplicates, appendix letters sequential starting at A, and sub-heading
numbers ("2.1", "A.1") matching whichever chapter/appendix they're under.

Headings are told apart from Table of Contents entries (which repeat the
same "N. Title" text at body-text size) by font size and boldness, both of
which this template's print.css gives real H1/H2/H3 text but not TOC rows -
see _iter_headings() below. This mirrors font size/weight rather than
scanning plain extracted text, so it doesn't need to know which page number
the real content starts on."""

import re

import pytest

BOLD_FLAG = 1 << 4
H1_MIN_SIZE = 20
H2_MIN_SIZE = 15
H3_MIN_SIZE = 12

H1_NUMERIC = re.compile(r"^(\d+)\.\s")
H1_APPENDIX = re.compile(r"^Appendix ([A-Z])\.\s")
H2_NUMERIC = re.compile(r"^(\d+)\.(\d+)\s")
H2_APPENDIX = re.compile(r"^([A-Z])\.(\d+)\s")


def _raw_heading_spans(pdf_doc):
    """Yields (level, text, x0, y0, y1) for every bold, heading-sized text
    span in the PDF, in reading order - one entry *per line*, so a long
    heading that wraps onto a second line (e.g. "14.3 Move regex-based
    processing into proper" / "extensions") comes through as two separate
    entries here. _iter_headings() below merges those back together."""
    for page in pdf_doc:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    if not span["flags"] & BOLD_FLAG:
                        continue
                    size = span["size"]
                    text = span["text"].strip()
                    if not text:
                        continue
                    x0, y0, _x1, y1 = span["bbox"]
                    if size >= H1_MIN_SIZE:
                        yield 1, text, x0, y0, y1
                    elif size >= H2_MIN_SIZE:
                        yield 2, text, x0, y0, y1
                    elif size >= H3_MIN_SIZE:
                        yield 3, text, x0, y0, y1


def _iter_headings(pdf_doc):
    """Yields (level, text) for every real H1/H2/H3 in the PDF, in reading
    order, skipping anything at body-text size (Table of Contents rows) or
    not bold (this template's headings are always bold - see print.css).

    A heading long enough to wrap onto a second line lands as two separate,
    same-level spans starting at the same left edge with only a normal
    line-height gap between them (see _raw_heading_spans()) - merged back
    into one heading here rather than being treated as a second heading."""
    previous = None  # (level, x0, y1, size)
    text_parts = []

    def flush():
        if text_parts:
            yield previous[0], " ".join(text_parts)

    for level, text, x0, y0, y1 in _raw_heading_spans(pdf_doc):
        size = y1 - y0
        is_wrapped_continuation = (
            previous is not None
            and previous[0] == level
            and abs(previous[1] - x0) < 1
            and 0 <= (y0 - previous[2]) < previous[3] * 1.5
        )
        if is_wrapped_continuation:
            text_parts.append(text)
        else:
            yield from flush()
            text_parts = [text]
        previous = (level, x0, y1, size)

    yield from flush()


@pytest.fixture(scope="module")
def headings(pdf_doc):
    return list(_iter_headings(pdf_doc))


def test_numeric_chapters_are_sequential_with_no_gaps_or_duplicates(headings):
    numbers = [
        int(m.group(1))
        for level, text in headings
        if level == 1
        for m in [H1_NUMERIC.match(text)]
        if m
    ]
    assert numbers, "No numeric H1 chapters found in the PDF"
    expected = list(range(numbers[0], numbers[0] + len(numbers)))
    assert numbers == expected, f"Numeric chapters aren't sequential: {numbers}"


def test_appendix_letters_are_sequential_starting_at_a(headings):
    letters = [
        m.group(1)
        for level, text in headings
        if level == 1
        for m in [H1_APPENDIX.match(text)]
        if m
    ]
    if not letters:
        pytest.skip("No appendix pages in this document")
    expected = [chr(ord("A") + i) for i in range(len(letters))]
    assert letters == expected, f"Appendix letters aren't sequential from A: {letters}"


def test_appendix_pages_dont_consume_a_chapter_number(headings, nav_pages, macros, docs_dir):
    """The numeric chapter sequence should have exactly one entry per
    non-appendix nav page with a heading - i.e. appendix pages (see
    _page_is_appendix()) are skipped, not just lettered on top of an
    otherwise-continuing numeric count."""
    numeric_count = sum(1 for level, text in headings if level == 1 and H1_NUMERIC.match(text))
    non_appendix_pages_with_headings = sum(
        1
        for rel_path in nav_pages
        if not macros._page_is_appendix(docs_dir / rel_path)
        and macros._count_top_level_headings(docs_dir / rel_path) > 0
    )
    assert numeric_count == non_appendix_pages_with_headings


def test_subheadings_match_their_chapter_or_appendix(headings):
    """Walks headings in order, tracking the current chapter number/appendix
    letter, and checks every H2/H3 prefix matches it."""
    current_chapter = None
    current_appendix = None
    mismatches = []

    for level, text in headings:
        if level == 1:
            if (m := H1_NUMERIC.match(text)):
                current_chapter, current_appendix = m.group(1), None
            elif (m := H1_APPENDIX.match(text)):
                current_chapter, current_appendix = None, m.group(1)
            continue

        if level != 2:
            continue

        if current_appendix is not None:
            m = H2_APPENDIX.match(text)
            if not m or m.group(1) != current_appendix:
                mismatches.append((text, f"expected prefix '{current_appendix}.'"))
        elif current_chapter is not None:
            m = H2_NUMERIC.match(text)
            if not m or m.group(1) != current_chapter:
                mismatches.append((text, f"expected prefix '{current_chapter}.'"))

    assert not mismatches, f"Sub-heading numbers not matching their chapter/appendix: {mismatches}"
