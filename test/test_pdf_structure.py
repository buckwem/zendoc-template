# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""pdf_structure batch: checks the PDF-only scaffolding around the actual
content - the cover page's computed fields, and the auto-generated Table of
Contents - is present and looks like real data, not a placeholder or an
empty result."""

import re


def test_cover_page_has_a_real_word_count(pdf_full_text):
    match = re.search(r"Word count:\s*([\d,]+)", pdf_full_text[0])
    assert match, "No 'Word count: N' line on the cover page"
    assert int(match.group(1).replace(",", "")) > 0


def test_cover_page_has_a_repo_url(pdf_full_text):
    match = re.search(r"Repo:\s*(\S+)", pdf_full_text[0])
    assert match, "No 'Repo: <url>' line on the cover page"
    assert match.group(1).startswith(("http://", "https://"))


def test_table_of_contents_exists(pdf_full_text):
    assert any("Table of Contents" in text for text in pdf_full_text)
