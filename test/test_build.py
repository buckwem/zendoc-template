# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""build batch: sanity-checks that both build_pdf.py and `zensical build`
actually produced usable output - not a rebuild, just enough evidence that
the artifacts on disk are complete and openable. See conftest.py for the
pdf_doc/public_dir fixtures, which already fail with a clear message if the
artifacts are missing entirely."""

from conftest import PDF_PATH, soup_for


def test_pdf_opens_and_has_pages(pdf_doc):
    assert pdf_doc.page_count > 0


def test_pdf_has_a_reasonable_page_count(pdf_doc):
    # Loose sanity bound, not a golden value - this template's own PDF has
    # run past 100 pages once References/Acronyms/Glossary/Appendixes were
    # added, and a genuinely broken build (e.g. only the cover page made it
    # through) would produce something far smaller than any real report.
    assert pdf_doc.page_count > 5


def test_pdf_file_is_not_suspiciously_small(pdf_doc):
    assert PDF_PATH.stat().st_size > 50_000


def test_website_cover_page_renders(public_dir):
    soup = soup_for(public_dir / "index.html")
    assert soup.find("html") is not None
    assert len(soup.get_text(strip=True)) > 0


def test_website_has_more_than_the_cover_page(public_html_files):
    # index.html plus at least a handful of nav pages.
    assert len(public_html_files) > 5
