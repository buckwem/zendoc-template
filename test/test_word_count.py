# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""word_count batch: checks pages flagged exclude_from_word_count: true
(see issue #23) actually get excluded from both the website's
{{ word_count }} and the PDF's {WORDCOUNT} marker - not just that the flag
exists somewhere, but that it visibly changes the computed total."""

import os
import re

from prodockit.wordcount import count_words

from conftest import page_excluded_from_word_count


def _naive_and_flagged_totals(nav_pages, docs_dir):
    naive_total = sum(
        count_words((docs_dir / rel_path).read_text(encoding="utf-8"))
        for rel_path in nav_pages
        if os.path.basename(rel_path).lower() != "index.md"
    )
    flagged_total = sum(
        count_words((docs_dir / rel_path).read_text(encoding="utf-8"))
        for rel_path in nav_pages
        if page_excluded_from_word_count(docs_dir / rel_path)
    )
    return naive_total, flagged_total


def test_at_least_one_page_is_flagged_excluded(nav_pages, docs_dir):
    flagged = [
        rel_path
        for rel_path in nav_pages
        if page_excluded_from_word_count(docs_dir / rel_path)
    ]
    assert flagged, (
        "No nav page has exclude_from_word_count: true - either this "
        "template's default References/Acronyms/Glossary/Originality pages "
        "lost the flag, or this test needs updating"
    )


def test_website_word_count_excludes_flagged_pages(website_word_count, nav_pages, docs_dir):
    computed_total = int(website_word_count.replace(",", ""))
    naive_total, flagged_total = _naive_and_flagged_totals(nav_pages, docs_dir)
    assert flagged_total > 0
    assert computed_total == naive_total - flagged_total


def test_pdf_word_count_matches_the_website_exactly(pdf_full_text, website_word_count):
    """The PDF's {WORDCOUNT} cover-page marker (see prodockit.pdf.config's
    own docs) reuses prodockit.zensical_macros._compute_site_word_count() -
    the exact same function the website's own {{ word_count }} macro
    calls - so the two numbers are guaranteed equal, not just close, and a
    submission's PDF and its live website page never disagree."""
    cover_text = pdf_full_text[0]
    match = re.search(r"Word count:\s*([\d,]+)", cover_text)
    assert match, "No 'Word count: N' line found on the PDF cover page"
    pdf_count = match.group(1)

    assert pdf_count == website_word_count
