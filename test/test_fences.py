# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""fences batch: exercises the fence-detection primitives build_pdf.py and
macros.py both rely on (_split_fenced_blocks(), apply_outside_fences(),
_walk_outside_fences(), and the fence-skipping loops in
_count_top_level_headings()/_count_words_in_markdown()) against nested
combinations of headings, admonitions, code blocks, content tabs, and grid
cards - not just a single flat fenced block, which is all the rest of the
suite happens to exercise incidentally.

These are unit tests against hand-written markdown snippets, not the built
site/PDF - pdf_doc/public_dir aren't needed here, so (unlike every other
batch) this one runs without building anything first."""

import textwrap


def dedent(text):
    return textwrap.dedent(text).strip("\n") + "\n"


# ---------------------------------------------------------------------------
# _split_fenced_blocks() / apply_outside_fences()
# ---------------------------------------------------------------------------

def test_apply_outside_fences_skips_a_simple_fence(build_pdf_module):
    content = dedent(
        """
        before FOO
        ```
        FOO
        ```
        after FOO
        """
    )
    result = build_pdf_module.apply_outside_fences(content, lambda t: t.replace("FOO", "BAR"))
    assert "before BAR" in result
    assert "after BAR" in result
    assert "```\nFOO\n```" in result  # untouched inside the fence


def test_apply_outside_fences_handles_tilde_fences(build_pdf_module):
    content = dedent(
        """
        before FOO
        ~~~
        FOO
        ~~~
        after FOO
        """
    )
    result = build_pdf_module.apply_outside_fences(content, lambda t: t.replace("FOO", "BAR"))
    assert "before BAR" in result
    assert "after BAR" in result
    assert "~~~\nFOO\n~~~" in result


def test_a_longer_fence_can_safely_contain_a_shorter_one(build_pdf_module):
    """superfences (see markdown.md's own "Code blocks" section) lets a
    4-backtick fence wrap a literal 3-backtick example - the inner ``` must
    not be mistaken for the closing fence."""
    content = dedent(
        """
        before FOO
        ````
        ```python
        FOO = 1
        ```
        ````
        after FOO
        """
    )
    result = build_pdf_module.apply_outside_fences(content, lambda t: t.replace("FOO", "BAR"))
    assert "before BAR" in result
    assert "after BAR" in result
    assert "FOO = 1" in result  # untouched - still inside the outer fence


def test_apply_outside_fences_handles_multiple_separate_fences_in_order(build_pdf_module):
    content = dedent(
        """
        FOO one
        ```
        FOO in fence one
        ```
        FOO two
        ```
        FOO in fence two
        ```
        FOO three
        """
    )
    result = build_pdf_module.apply_outside_fences(content, lambda t: t.replace("FOO", "BAR"))
    assert result.count("BAR") == 3
    assert result.count("FOO in fence") == 2


def test_apply_outside_fences_is_a_no_op_transform_roundtrip(build_pdf_module):
    """Rejoining segments with "\\n" (see apply_outside_fences()'s own
    docstring) must reproduce the original content exactly when the
    transform doesn't change anything."""
    content = dedent(
        """
        # Heading

        Some prose.

        ```python
        x = 1
        ```

        More prose.
        """
    )
    assert build_pdf_module.apply_outside_fences(content, lambda t: t) == content


# ---------------------------------------------------------------------------
# tag_first_heading() - a heading-like line inside a fence isn't a heading
# ---------------------------------------------------------------------------

def test_tag_first_heading_skips_a_heading_shown_inside_a_fence(build_pdf_module):
    content = dedent(
        """
        ```markdown
        # Not a real heading
        ```

        # Real Heading
        """
    )
    result = build_pdf_module.tag_first_heading(content, "my-anchor")
    assert "# Not a real heading\n```" in result  # untouched
    assert "# Real Heading {#my-anchor}" in result


def test_tag_first_heading_inserts_into_an_existing_attribute_block(build_pdf_module):
    content = "# Real Heading {.unnumbered}\n"
    result = build_pdf_module.tag_first_heading(content, "my-anchor")
    assert result == "# Real Heading {.unnumbered #my-anchor}\n"


def test_tag_first_heading_adds_the_appendix_class_alongside_the_anchor(build_pdf_module):
    content = "# Real Heading\n"
    result = build_pdf_module.tag_first_heading(content, "my-anchor", extra_class="appendix")
    assert result == "# Real Heading {#my-anchor .appendix}\n"


# ---------------------------------------------------------------------------
# rewrite_internal_md_links() / rewrite_repo_file_links()
# ---------------------------------------------------------------------------

def test_md_link_inside_a_fence_is_left_as_literal_example_text(build_pdf_module):
    content = dedent(
        """
        ```markdown
        [Install tooling](installtooling.md)
        ```

        [Install tooling](installtooling.md)
        """
    )
    result = build_pdf_module.rewrite_internal_md_links(
        content, "starthere/customise.md", {"starthere/installtooling.md": "page-installtooling"}
    )
    assert "[Install tooling](installtooling.md)\n```" in result  # example untouched
    assert "[Install tooling](#page-installtooling)" in result  # real link rewritten


def test_repo_file_link_inside_a_fence_is_left_as_literal_example_text(build_pdf_module):
    content = dedent(
        """
        ```markdown
        [extra.css](../stylesheets/extra.css)
        ```

        [extra.css](../stylesheets/extra.css)
        """
    )
    result = build_pdf_module.rewrite_repo_file_links(
        content, "starthere/customise.md", "docs", "https://github.com/buckwem/zendoc-template"
    )
    assert "[extra.css](../stylesheets/extra.css)\n```" in result  # example untouched
    assert (
        "[extra.css](https://github.com/buckwem/zendoc-template/blob/main/docs/stylesheets/extra.css)"
        in result
    )


# ---------------------------------------------------------------------------
# macros.py: heading/word counting must also skip fenced (incl. indented,
# i.e. nested-under-an-admonition-or-tab) code
# ---------------------------------------------------------------------------

def test_count_top_level_headings_skips_fenced_and_indented_fenced_examples(macros, tmp_path):
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
    assert macros._count_top_level_headings(md_file) == 2


def test_count_words_in_markdown_excludes_fenced_code(macros, tmp_path):
    prose_only = tmp_path / "prose.md"
    prose_only.write_text("one two three four five\n", encoding="utf-8")

    prose_plus_code = tmp_path / "prose_plus_code.md"
    prose_plus_code.write_text(
        dedent(
            """
            one two three four five

            ```python
            this block has plenty of extra words that must not be counted as prose
            ```
            """
        ),
        encoding="utf-8",
    )

    assert macros._count_words_in_markdown(prose_only) == macros._count_words_in_markdown(
        prose_plus_code
    )


# ---------------------------------------------------------------------------
# End-to-end: grid > tab > admonition > fenced code block, the deepest
# nesting this template's own docs actually use (see e.g. "Fork the
# zendoc-template" in installtooling.md) - run through the real
# preprocess_markdown() pipeline, not just the standalone helpers above.
# ---------------------------------------------------------------------------

def test_preprocess_markdown_handles_grid_tab_admonition_code_nesting(tmp_path, build_pdf_module):
    source = dedent(
        """
        # Page Heading

        <div class="grid cards one-column" markdown>

        -   __A card__

            === "macOS"

                !!! note
                    Some setup is needed first:

                    ```bash
                    echo "=== not a tab marker, !!! not an admonition marker ==="
                    brew install example
                    ```

            === "Windows"

                ```powershell
                Write-Host "example"
                ```

        </div>
        """
    )
    src_file = tmp_path / "source.md"
    src_file.write_text(source, encoding="utf-8")
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
        citation_map={},
    )

    result = out_file.read_text(encoding="utf-8")

    # The literal "=== "/"!!! " text *inside* the fenced code block must
    # survive verbatim - not be mistaken for a real tab/admonition marker by
    # the tab/admonition conversion pass that runs over the rest of the page.
    assert '=== not a tab marker, !!! not an admonition marker ===' in result

    # Both fenced code blocks (nested three levels deep: grid > tab >
    # admonition) must still be present and still fenced.
    assert "brew install example" in result
    assert "Write-Host" in result
    assert result.count("```") >= 4  # two open/close pairs

    # The admonition itself was converted to Pandoc's ::: fence syntax
    # rather than left as literal "!!! note" text.
    assert ".admonition .note" in result
    assert "!!! note" not in result
