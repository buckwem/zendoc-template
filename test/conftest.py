# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""Shared fixtures for the test suite (see issue #44). Tests here check the
*built output* - the website in public/ and the PDF at
docs/site_documentation.pdf - not the build process itself; run
`python build_pdf.py` and `zensical build` (or `python sync_repo_icon.py`
first, if you've just changed the git remote) before running these tests.
See test/run_tests.py for the runner and CONTRIBUTING.md for usage."""

import importlib.util
import re
import sys
from pathlib import Path

import fitz
import pytest
import toml
import zensical.config as zensical_config_module
from bs4 import BeautifulSoup
from zendoc.settings import flatten_nav
from zendoc.zensical_macros import _compute_site_word_count, _front_matter_flag

REPO_ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = REPO_ROOT / "docs" / "site_documentation.pdf"
PUBLIC_DIR = REPO_ROOT / "public"
ZENSICAL_TOML_PATH = REPO_ROOT / "zensical.toml"


def _import_repo_module(name):
    """Imports a top-level module (macros.py) from the repo root by file
    path, rather than relying on sys.path - the test suite reuses its own
    helpers (e.g. is_surrey detection) instead of re-implementing the same
    logic a second time, since re-implementing it independently would just
    be testing the test suite's own copy, not catching a real regression in
    the production code. Most of macros.py's own former logic (word count,
    repo URL, numbering/reference-style macros) now lives in
    zendoc.zensical_macros instead (see zendoc-extension#96) - tests that
    need it import that package directly."""
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(REPO_ROOT))
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def macros():
    return _import_repo_module("macros")


@pytest.fixture(scope="session")
def zensical_config():
    if not ZENSICAL_TOML_PATH.exists():
        pytest.fail("zensical.toml not found at repo root")
    return toml.load(ZENSICAL_TOML_PATH)


@pytest.fixture(scope="session")
def resolved_zensical_config():
    """zensical.toml, parsed and resolved through Zensical's own loader
    (`zensical.config.parse_config()`) rather than a raw `toml.load()` -
    `nav` here is Zensical's own already-resolved nav tree (each item
    carrying `url`/`is_index`/`children`), the same shape
    `zendoc.zensical_macros`/`zendoc.pdf.config` work with. Used where a
    test needs that resolved shape specifically (nav walking, or calling
    into `zendoc.zensical_macros`'s own functions directly) - most other
    tests use the `zensical_config` fixture's raw structure instead."""
    if not ZENSICAL_TOML_PATH.exists():
        pytest.fail("zensical.toml not found at repo root")
    return zensical_config_module.parse_config(str(ZENSICAL_TOML_PATH))


@pytest.fixture(scope="session")
def nav_pages(resolved_zensical_config):
    """List of every nav markdown file, docs_dir-relative, in nav order -
    e.g. "section1.md", "starthere/customise.md" - the same order both
    build_pdf.py and zendoc.zensical_macros walk to compute chapter
    numbers."""
    return [page["url"] for page in flatten_nav(resolved_zensical_config.get("nav") or [])]


@pytest.fixture(scope="session")
def docs_dir(zensical_config):
    project = zensical_config.get("project", {})
    docs_dir_name = project.get("docs_dir") or zensical_config.get("docs_dir") or "docs"
    return REPO_ROOT / docs_dir_name


@pytest.fixture(scope="session")
def website_word_count(resolved_zensical_config):
    """The real `{{ word_count }}` value zendoc.zensical_macros computes
    for this project's own website build - see
    test_word_count.py."""
    return _compute_site_word_count(resolved_zensical_config)


def page_is_appendix(path):
    """True if path's YAML front matter sets is_appendix: true - see
    "Appendixes" in customise.md. Mirrors the same check
    zendoc.zensical_macros/zendoc.pdf use for numbering."""
    return _front_matter_flag(str(path), "is_appendix")


def page_excluded_from_word_count(path):
    """True if path's YAML front matter sets exclude_from_word_count: true
    - see "Word count" in customise.md. Mirrors the same check
    zendoc.zensical_macros uses for the website's own word count."""
    return _front_matter_flag(str(path), "exclude_from_word_count")


def count_top_level_headings(path):
    """Counts top-level (single #) ATX headings in a markdown file, skipping
    fenced code blocks, HTML comments (e.g. the copyright header at the top
    of each page), and headings tagged {.unnumbered} (e.g. the hidden
    cover-page title). Test-only verification helper (see test_numbering.py/
    test_fences.py) - not needed by production code, which gets its
    numbering from zendoc.headings' own prescan() instead."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return 0
    count = 0
    in_fence = False
    in_comment = False
    for line in text.splitlines():
        stripped = line.strip()
        if not in_comment and (stripped.startswith("```") or stripped.startswith("~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not in_comment and "<!--" in stripped:
            in_comment = True
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            continue
        if re.match(r"^#\s+\S", line) and ".unnumbered" not in line:
            count += 1
    return count


@pytest.fixture(scope="session")
def pdf_doc():
    if not PDF_PATH.exists():
        pytest.fail(
            f"{PDF_PATH} not found - run `python build_pdf.py` before running the test suite"
        )
    doc = fitz.open(PDF_PATH)
    if doc.page_count == 0:
        pytest.fail(f"{PDF_PATH} opened but has no pages")
    yield doc
    doc.close()


@pytest.fixture(scope="session")
def pdf_full_text(pdf_doc):
    """The whole PDF's text, one string per page, in page order."""
    return [page.get_text() for page in pdf_doc]


@pytest.fixture(scope="session")
def public_dir():
    if not PUBLIC_DIR.exists() or not (PUBLIC_DIR / "index.html").exists():
        pytest.fail(
            f"{PUBLIC_DIR} not found or missing index.html - run `zensical build` before running the test suite"
        )
    return PUBLIC_DIR


@pytest.fixture(scope="session")
def public_html_files(public_dir):
    """Every built HTML page under public/, as a sorted list of Paths."""
    return sorted(public_dir.rglob("*.html"))


def soup_for(html_path):
    """Parses one built HTML file with BeautifulSoup."""
    return BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")


# Same signal test_numbering.py's _iter_headings() uses to tell a real H1
# apart from a Table of Contents row repeating the same "N. Title" text at
# body-text size: this template's print.css only gives real headings bold,
# large text. A naive plain-text "page.get_text().startswith(...)" search
# (the first approach used here, before issue #46's nav reorder exposed the
# bug) can false-match a Table of Contents row instead of the real heading.
_H1_BOLD_FLAG = 1 << 4
_H1_MIN_SIZE = 20


def chapter_page_range(pdf_doc, heading_prefix):
    """Returns (start, end) page indexes [start, end) for the chapter whose
    real H1 starts with heading_prefix (e.g. "11. Customisation"). start is
    the page the heading itself is on; end is the page the *next* numbered
    H1 starts on (or len(pdf_doc) if it's the last chapter). Used by
    test_captions.py, test_zensical_basics.py, and test_markdown_foundations.py
    to locate a specific chapter's real content in the built PDF without
    hardcoding a page number that would break as nav is reordered or pages
    are added/removed."""
    start = None
    for i, page in enumerate(pdf_doc):
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    if not span["flags"] & _H1_BOLD_FLAG or span["size"] < _H1_MIN_SIZE:
                        continue
                    text = span["text"].strip()
                    if not text:
                        continue
                    if start is None and text.startswith(heading_prefix):
                        start = i
                    elif start is not None and re.match(r"^\d+\.\s", text):
                        return start, i
    assert start is not None, f"Couldn't find a chapter starting with '{heading_prefix}' in the PDF"
    return start, len(pdf_doc)


def _flatten_markdown_extensions(extensions_config, prefix=""):
    """Flattens zensical.toml's nested [project.markdown_extensions.*]
    tables into markdown.Markdown()'s flat "dotted.name" extension list -
    e.g. {"pymdownx": {"betterem": {}}} becomes "pymdownx.betterem". A
    table counts as a nested group (recursed into) only if every one of its
    own values is itself a table - otherwise it's a leaf extension's own
    config dict (e.g. pymdownx.highlight's anchor_linenums/line_spans/
    pygments_lang_class are config values, not nested extensions)."""
    flat = {}
    for key, value in extensions_config.items():
        dotted = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict) and value and all(isinstance(v, dict) for v in value.values()):
            flat.update(_flatten_markdown_extensions(value, dotted))
        else:
            flat[dotted] = value
    return flat


@pytest.fixture(scope="session")
def markdown_extension_config(zensical_config):
    """Returns (extensions, extension_configs) for markdown.Markdown(),
    built from this project's real [project.markdown_extensions.*] config
    in zensical.toml - so a config change is automatically reflected in
    every test that uses this fixture instead of silently drifting out of
    sync with a hardcoded extension list. Used by test_markdown_foundations.py
    and test_zensical_basics.py.

    Skips zensical.extensions.* (glightbox, macros) - these are Zensical's
    own runtime integrations, not standalone pip-installable Markdown
    extensions - and skips pymdownx.emoji, since its emoji_index/
    emoji_generator config values are dotted references to
    zensical.extensions.emoji callables that only Zensical's own loader
    resolves; plain markdown.Markdown() takes the dotted strings literally
    and errors. A caller that needs working emoji/icon rendering (see
    test_zensical_basics.py) adds pymdownx.emoji back with the real
    zensical.extensions.emoji.twemoji/to_svg callables imported directly."""
    raw = zensical_config.get("project", {}).get("markdown_extensions", {})
    flat = _flatten_markdown_extensions(raw)
    extensions = [
        name for name in flat
        if not name.startswith("zensical.extensions") and name != "pymdownx.emoji"
    ]
    extension_configs = {name: flat[name] for name in extensions if flat[name]}
    return extensions, extension_configs
