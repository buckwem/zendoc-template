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
