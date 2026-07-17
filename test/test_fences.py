# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""fences batch: exercises the fence-detection primitives
conftest.count_top_level_headings()/prodockit.wordcount.count_words() rely on
against nested combinations of headings, admonitions, and code blocks - not
just a single flat fenced block.

build_pdf.py's own equivalent fence-awareness concerns (skipping fenced
examples of tab/admonition/caption syntax, code fences nested under grid
cards, and so on) no longer need dedicated primitives of their own - see
zendoc-template#92: render_page_html() renders pages through Zensical's real
Markdown parser (via render()) rather than regex over raw text, so a real
`<pre><code>` element's contents are never mistaken for actual markup in the
first place, the same way python-markdown itself never confuses a heading
shown inside a fenced code example for a real heading.

These are unit tests against hand-written markdown snippets, not the built
site/PDF - pdf_doc/public_dir aren't needed here, so (unlike every other
batch) this one runs without building anything first."""

import textwrap

from prodockit.wordcount import count_words

from conftest import count_top_level_headings


def dedent(text):
    return textwrap.dedent(text).strip("\n") + "\n"


# ---------------------------------------------------------------------------
# heading/word counting must also skip fenced (incl. indented, i.e.
# nested-under-an-admonition-or-tab) code
# ---------------------------------------------------------------------------

def test_count_top_level_headings_skips_fenced_and_indented_fenced_examples(tmp_path):
    content = dedent(
        """
        # Real Heading One

        ```markdown
        # Not a heading
        # Also not a heading
        ```

        !!! note
            An admonition containing an indented, nested fence:

            ```markdown
            # Still not a heading
            ```

        # Real Heading Two
        """
    )
    md_file = tmp_path / "page.md"
    md_file.write_text(content, encoding="utf-8")
    assert count_top_level_headings(md_file) == 2


def test_count_words_excludes_fenced_code():
    prose_only = "one two three four five\n"
    prose_plus_code = dedent(
        """
        one two three four five

        ```python
        this block has plenty of extra words that must not be counted as prose
        ```
        """
    )
    assert count_words(prose_only) == count_words(prose_plus_code)
