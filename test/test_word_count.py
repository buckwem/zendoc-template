# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""word_count batch: checks pages flagged exclude_from_word_count: true
(see issue #23) actually get excluded from both the website's
{{ word_count }} and the PDF's {WORDCOUNT} marker - not just that the flag
exists somewhere, but that it visibly changes the computed total."""

import os
import re


def _naive_and_flagged_totals(macros, nav_pages, docs_dir):
    naive_total = sum(
        macros._count_words_in_markdown(docs_dir / rel_path)
        for rel_path in nav_pages
        if os.path.basename(rel_path).lower() != "index.md"
    )
    flagged_total = sum(
        macros._count_words_in_markdown(docs_dir / rel_path)
        for rel_path in nav_pages
        if macros._page_excluded_from_word_count(docs_dir / rel_path)
    )
    return naive_total, flagged_total


def test_at_least_one_page_is_flagged_excluded(macros, nav_pages, docs_dir):
    flagged = [
        rel_path
        for rel_path in nav_pages
        if macros._page_excluded_from_word_count(docs_dir / rel_path)
    ]
    assert flagged, (
        "No nav page has exclude_from_word_count: true - either this "
        "template's default References/Acronyms/Glossary/Originality pages "
        "lost the flag, or this test needs updating"
    )


def test_website_word_count_excludes_flagged_pages(macros, nav_pages, docs_dir):
    computed_total = int(macros._compute_site_word_count().replace(",", ""))
    naive_total, flagged_total = _naive_and_flagged_totals(macros, nav_pages, docs_dir)
    assert flagged_total > 0
    assert computed_total == naive_total - flagged_total


def test_pdf_word_count_reflects_the_excluded_pages(macros, pdf_full_text, nav_pages, docs_dir):
    """The PDF computes its word count independently (compute_pdf_word_count()
    in build_pdf.py runs on already-preprocessed files, a different pipeline
    to macros.py's website-side count - see the "Word count" note in
    customise.md), so it won't match the website's number exactly. But it
    should land closer to "excluding the flagged pages" than to "including
    them" - if exclusion silently broke, the PDF's count would jump back up
    toward (or past) the naive, everything-included total."""
    cover_text = pdf_full_text[0]
    match = re.search(r"Word count:\s*([\d,]+)", cover_text)
    assert match, "No 'Word count: N' line found on the PDF cover page"
    pdf_count = int(match.group(1).replace(",", ""))

    naive_total, flagged_total = _naive_and_flagged_totals(macros, nav_pages, docs_dir)
    assert flagged_total > 0

    distance_to_excluding = abs(pdf_count - (naive_total - flagged_total))
    distance_to_including = abs(pdf_count - naive_total)
    assert distance_to_excluding < distance_to_including, (
        f"PDF word count ({pdf_count}) is closer to the naive, "
        f"everything-included total ({naive_total}) than to the total with "
        f"flagged pages excluded ({naive_total - flagged_total})"
    )
