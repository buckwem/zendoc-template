---
icon: lucide/book-open
---

<!-- 
# Copyright (c) 2025-2026 Mark Buckwell and contributors
# SPDX-License-Identifier: MIT
-->

{{ heading_counter_reset(page) }}

# Testing

Every other page in this section explains how to *use* this template to write your report. This page is different: it documents the test suite in `test/`, which checks that this template's own zendoc-specific features (References, Acronyms, Glossary, Appendix numbering, word-count exclusions, and so on) actually work and haven't regressed - a contributor/maintainer tool, not something you need while writing your assignment.

!!! info "Why this exists"
    Every feature and bug fix in this template used to be verified by hand - a one-off script, eyeballed once, then thrown away. Nothing stopped a later change from silently re-breaking something already fixed. The test suite in `test/` replaces that with checks that run automatically, in CI, on every push.

## Running the test suite

The tests check the *built output* - the website in `public/` and the PDF at `docs/site_documentation.pdf` - not the build process itself, so build both first:

```bash
pip install -r requirements.txt -r testrequirements.txt
python build_pdf.py
zensical build
python test/run_tests.py
```

`testrequirements.txt` is separate from `requirements.txt` - it's only needed to run the tests (locally or in CI), not to build your own report from this template.

Tests are organised into **batches**, one per `test/test_*.py` file, each reporting its own pass/fail (see [Test batches](#test-batches) below for what each one covers):

```bash
python test/run_tests.py --list            # list available batches
python test/run_tests.py --batch links     # run just one batch
python test/run_tests.py -- -k caption     # extra args passed through to pytest
```

Running just one batch is the fast path while you're actively working on a specific capability - you don't have to wait on the rest of the suite (including a couple of batches that parse the whole PDF) to check whether your change works.

## Adding a new test

Most new tests belong in an existing batch - add a `test_*` function to the matching `test/test_<batch>.py` file. Start a new batch (a new `test/test_<name>.py` file) only for a genuinely new category of concern; `test/run_tests.py --list` picks up any `test_*.py` file automatically, no registration needed.

Shared fixtures live in `test/conftest.py` and cover both the failure-with-a-clear-message case (missing build artifacts) and the common lookups most tests need:

| Fixture | Gives you |
| -- | -- |
| `pdf_doc` | The built PDF, already opened with PyMuPDF (`fitz`) |
| `pdf_full_text` | The PDF's text, one string per page |
| `public_dir` | Path to the built website (`public/`) |
| `public_html_files` | Every built HTML file, as a sorted list of `Path`s |
| `macros` / `build_pdf_module` | The actual `macros.py`/`build_pdf.py` modules, imported live |
| `nav_pages` / `docs_dir` | The current `nav` list (docs_dir-relative paths) and `docs_dir` itself |
| `zensical_config` | `zensical.toml`, parsed |
/// table-caption | <
Shared fixtures in test/conftest.py
///

Two different styles of test both have a place here, and most batches mix both:

- **Black-box, against the built output** - most of `test_build.py`, `test_links.py`, `test_numbering.py`, `test_word_count.py`, `test_content.py`, and `test_pdf_structure.py` work this way: build the site/PDF, then check something true about the result (no `LAUNCH`-type links, chapter numbers sequential, a flagged page's words don't count, and so on).
- **Direct unit tests against a helper function**, with a hand-written markdown snippet, no build required - `test_fences.py` works this way throughout, calling functions like `macros._count_top_level_headings()` directly. Reach for this style when you're testing a specific function's behaviour on a deliberately constructed edge case (e.g. a heading shown literally inside a fenced code example) rather than something you'd have to go hunting for in the real docs to exercise.

Where a check needs "the real thing this feature is supposed to do" as a source of truth (e.g. which pages are flagged `is_appendix: true`), reuse the actual function from `macros.py`/`build_pdf.py` (via the `macros`/`build_pdf_module` fixtures) rather than re-implementing the same TOML/front-matter parsing a second time in the test - that would just test the test's own parser, not catch a real regression in the production code.

## Test batches

| Batch | Checks |
| -- | -- |
| `build` | Both builds actually produced usable output - the PDF opens with a sane page count, the website has more than just the cover page. |
| `links` | No `LAUNCH`-type or local-filesystem links in the PDF (see [issue #19](https://github.com/buckwem/zendoc-template/issues/19)); every internal website link and same-page fragment resolves to a real page and id; every internal PDF cross-reference resolves to a real, in-range page (see [issue #71](https://github.com/buckwem/zendoc-template/issues/71)). |
| `numbering` | Chapter numbers are sequential with no gaps or duplicates; appendix letters run A, B, C... with no gaps and don't consume a chapter number (see [issue #24](https://github.com/buckwem/zendoc-template/issues/24)); every sub-heading's number matches its actual parent chapter/appendix. |
| `word_count` | Pages flagged `exclude_from_word_count: true` are actually subtracted from both the website's and the PDF's word count, not just present as an unused flag (see [issue #23](https://github.com/buckwem/zendoc-template/issues/23)). |
| `content` | No un-translated template syntax leaks into the PDF as literal, visible text - unsubstituted `{WORDCOUNT}`/`{REPOURL}` markers on the cover page, or leaked attr_list `{: ... }` syntax on the Acronyms/Glossary/References pages. |
| `pdf_structure` | The cover page's computed fields (word count, repo URL) and the auto-generated Table of Contents are present and look like real data. |
| `fences` | The fence-skipping loops in `macros.py`'s heading/word counters hold up under nested combinations of headings, admonitions, and code blocks - not just a single flat fenced block. `build_pdf.py`'s own equivalent primitives were retired in zendoc-template#92: `render_page_html()` renders pages through Zensical's real Markdown parser, so a heading/tab/admonition shown inside a fenced code example is never mistaken for the real thing in the first place. |
| `captions` | The PDF's `figure-caption`/`table-caption` numbering (see [Captions](customise.md#captions)) is correctly prefixed with the page's chapter number/appendix letter, and no `///` block syntax leaks into the PDF as literal text - checked against the real, already-built PDF. Manual number overrides, custom id/class, and prepend/append position are `pymdownx.blocks.caption`'s own behaviour since zendoc-template#92, identical to the website's - no longer a `build_pdf.py`-specific concern to unit-test here. |
| `markdown_foundations` | The core Markdown syntax documented in [Markdown basics](markdown.md) - headings, text formatting, links/images, lists (including the 4-space nesting rule - see [issue #70](https://github.com/buckwem/zendoc-template/issues/70)), code blocks, tables, horizontal rules, task lists, and blockquotes - rendered through this project's real `markdown.Markdown()` extension config, not a hardcoded copy of it, plus a real `pandoc` subprocess check for a genuine website/PDF nesting discrepancy. |
| `zensical_basics` | The Zensical-specific extensions documented in [Zensical basics](zensicalbasics.md) - admonitions (all 12 configured types, custom/empty titles, nesting, collapsible details), code blocks (line highlighting, line numbers, titles, annotations, inline highlighting), content tabs (nested, anchor ids), images (figure/figcaption, alignment, lazy loading, light/dark hash fragments), diagrams (all 5 officially-supported Mermaid types), footnotes, formatting (mark, keys), icons/emojis, maths (arithmatex wrapping), task lists, and tooltips/abbreviations - cross-checked against the upstream `zensical.org/docs/authoring/*` pages this page itself links to, not just its own worked examples, plus end-to-end checks against this page's own "live example" content in the real, already-built PDF (catching, among other things, `==mark==`/`++keys++` leaking as literal text there - see [issue #72](https://github.com/buckwem/zendoc-template/issues/72)). |
| `customisation` | Every remaining template-specific customisation point in [Customisation](customise.md) not already covered by a more specific batch above - site logo/metadata/copyright/repository link, colour scheme, header background, fonts, icons, feature toggles, extra CSS/JS, navigation structure, institution branding, `.pdf-only`/`.web-only` content, the Download PDF button, page header/footer content, page size/margins (see [issue #51](https://github.com/buckwem/zendoc-template/issues/51)), and screenshots - reflects what `zensical.toml` actually configures, not just something plausible-looking. Where a value is duplicated by necessity between the website's CSS and the PDF's (references/acronyms/glossary spacing, `.screenshot` framing), checks both copies stay in sync with each other. |
/// table-caption | <
Test suite batches
///

## Where to go next

This is the last of the "Start Here" reference pages. Continue to [Finalising your document](customise.md#finalising-your-document) once your report itself is ready to submit - removing `starthere/` (this page included) is part of that step.
