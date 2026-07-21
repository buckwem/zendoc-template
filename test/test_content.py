# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""content batch: catches un-translated template syntax leaking into the
PDF as literal, visible text - attr_list `{: ... }` lines Pandoc doesn't
understand, un-substituted {WORDCOUNT}/{REPOURL} markers, or un-evaluated
{{ jinja }} variables.

This deliberately does NOT scan the whole PDF for these strings: several of
the User Guide's customise.md documentation sections *intentionally* show
this syntax as a literal code-block example (e.g. the Captions and
References sections) - see issue #49, that page now lives in the separate
prodockit-userguide repo - so a blanket scan would flag legitimate examples
as false positives. Checks are scoped to the specific pages where this
syntax should only ever appear already-converted - the cover page for the
PDF markers, and the Acronyms/Glossary/References appendix pages for
attr_list."""

import re

MARKERS = ("{WORDCOUNT}", "{REPOURL}", "{{ site_name }}", "{{ word_count }}", "{{ repo_url }}")

ATTR_LIST_LEAK = re.compile(r"\{:\s*#[\w-]")


def test_cover_page_markers_are_substituted(pdf_full_text):
    cover = pdf_full_text[0]
    leaked = [marker for marker in MARKERS if marker in cover]
    assert not leaked, f"Un-substituted marker(s) on the PDF cover page: {leaked}"


def _page_starting_with(pdf_full_text, heading_prefix):
    for i, text in enumerate(pdf_full_text):
        if text.strip().startswith(heading_prefix):
            return i
    return None


def test_appendix_pages_have_no_leaked_attr_list_syntax(pdf_full_text):
    """References/Acronyms/Glossary entries are written as attr_list
    (paragraph + "{: #id .class }") in their source .md files - resolved by
    the real attr_list Markdown extension when Zensical renders each page
    (the same pipeline `prodockit pdf` uses, before Pandoc ever sees the
    result - see "References and bibliography" in customise.md), identical
    to how the website itself handles it. If that ever broke, the raw
    "{: #id ... }" text would leak straight into the PDF as visible body
    text."""
    headings = {
        "Appendix A. Acronyms": None,
        "Appendix B. Glossary": None,
        "Appendix C. References": None,
    }
    for heading in headings:
        page_index = _page_starting_with(pdf_full_text, heading)
        assert page_index is not None, f"Couldn't find '{heading}' page in the PDF"
        leaked = ATTR_LIST_LEAK.findall(pdf_full_text[page_index])
        assert not leaked, f"Leaked attr_list syntax on the '{heading}' page: {leaked}"
