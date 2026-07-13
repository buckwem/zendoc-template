# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""Shared fixtures for the test suite (see issue #44). Tests here check the
*built output* - the website in public/ and the PDF at
docs/site_documentation.pdf - not the build process itself; run
`python build_pdf.py` and `zensical build` (or `python sync_repo_icon.py`
first, if you've just changed the git remote) before running these tests.
See test/run_tests.py for the runner and CONTRIBUTING.md for usage."""

import importlib.util
import sys
from pathlib import Path

import fitz
import pytest
import toml
from bs4 import BeautifulSoup

REPO_ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = REPO_ROOT / "docs" / "site_documentation.pdf"
PUBLIC_DIR = REPO_ROOT / "public"
ZENSICAL_TOML_PATH = REPO_ROOT / "zensical.toml"


def _import_repo_module(name):
    """Imports a top-level module (macros.py, build_pdf.py) from the repo
    root by file path, rather than relying on sys.path - the test suite
    reuses these modules' own helpers (e.g. to enumerate nav pages or check
    an is_appendix/exclude_from_word_count flag) instead of re-implementing
    the same TOML/front-matter parsing a second time, since re-parsing it
    independently would just be testing the test suite's own parser, not
    catching a real regression in the production code."""
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(REPO_ROOT))
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def macros():
    return _import_repo_module("macros")


@pytest.fixture(scope="session")
def build_pdf_module():
    return _import_repo_module("build_pdf")


@pytest.fixture(scope="session")
def zensical_config():
    if not ZENSICAL_TOML_PATH.exists():
        pytest.fail("zensical.toml not found at repo root")
    return toml.load(ZENSICAL_TOML_PATH)


@pytest.fixture(scope="session")
def nav_pages(macros, zensical_config):
    """List of every nav markdown file, docs_dir-relative, in nav order -
    e.g. "section1.md", "starthere/customise.md" - the same order both
    build_pdf.py and macros.py walk to compute chapter numbers."""
    project = zensical_config.get("project", {})
    nav = project.get("nav") or zensical_config.get("nav") or []
    return macros._extract_nav_md_files(nav)


@pytest.fixture(scope="session")
def docs_dir(zensical_config):
    project = zensical_config.get("project", {})
    docs_dir_name = project.get("docs_dir") or zensical_config.get("docs_dir") or "docs"
    return REPO_ROOT / docs_dir_name


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
