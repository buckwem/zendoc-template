# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""links batch: catches the two classes of bug this template has actually
shipped before - a PDF link pointing at the build machine's own local
filesystem instead of something meaningful to a reader (issue #19, and the
LAUNCH-type "View source" link fixed in issue #40), and an internal website
link/anchor that doesn't resolve to anything (issue #16)."""

from urllib.parse import urlsplit

from conftest import REPO_ROOT, soup_for

LINK_LAUNCH = 3


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def test_pdf_has_no_launch_links(pdf_doc):
    """LAUNCH-type links point at a local file path on whatever machine
    built the PDF - meaningless (and potentially revealing) to anyone else
    reading it. See issue #19/#40 - every internal/repo-file link should
    already be rewritten to either an in-document anchor or a real URL."""
    offenders = []
    for page_number, page in enumerate(pdf_doc):
        for link in page.get_links():
            if link.get("kind") == LINK_LAUNCH:
                offenders.append((page_number, link.get("file")))
    assert not offenders, f"LAUNCH-type links found (page, file): {offenders}"


def test_pdf_uri_links_are_not_local_filesystem_paths(pdf_doc):
    repo_root_str = str(REPO_ROOT)
    offenders = []
    for page_number, page in enumerate(pdf_doc):
        for link in page.get_links():
            uri = link.get("uri") or ""
            if uri.startswith("file://") or repo_root_str in uri:
                offenders.append((page_number, uri))
    assert not offenders, f"PDF links pointing at a local filesystem path: {offenders}"


# ---------------------------------------------------------------------------
# Website
# ---------------------------------------------------------------------------

def _is_internal(href):
    """True for a same-page fragment ("#foo") or a relative/site-root path
    ("../glossary/", "/starthere/customise/") - false for anything with a
    URL scheme (http:, mailto:, tel:, javascript:, data:), which urlsplit()
    reports as a non-empty scheme."""
    return bool(href) and urlsplit(href).scheme == ""


def _resolve_internal_href(href, current_file, public_dir):
    """Resolves an internal href (e.g. "../glossary/#css-def", "#appendixes",
    "/starthere/customise/") found in current_file to (target_file, fragment).
    Returns (None, fragment) if the target file doesn't exist on disk."""
    path_part, _, fragment = href.partition("#")
    fragment = fragment or None
    if not path_part:
        return current_file, fragment

    base = public_dir if path_part.startswith("/") else current_file.parent
    target = (base / path_part.lstrip("/")).resolve()
    if path_part.endswith("/") or target.is_dir():
        target = target / "index.html"

    if not target.exists():
        return None, fragment
    return target, fragment


def _ids_in(html_path, cache):
    if html_path not in cache:
        soup = soup_for(html_path)
        ids = {el.get("id") for el in soup.find_all(id=True)}
        ids |= {el.get("name") for el in soup.find_all("a", attrs={"name": True})}
        cache[html_path] = ids
    return cache[html_path]


def test_website_internal_links_resolve(public_dir, public_html_files):
    """Every same-page fragment link and every internal page link (with or
    without its own fragment) in the built site should point at a file - and
    an id, if it names one - that actually exists once the site is built."""
    id_cache = {}
    broken = []

    for html_file in public_html_files:
        soup = soup_for(html_file)
        article = soup.find("article") or soup

        for a in article.find_all("a", href=True):
            href = a["href"].strip()
            if not href or not _is_internal(href):
                continue

            target_file, fragment = _resolve_internal_href(href, html_file, public_dir)
            rel_source = html_file.relative_to(public_dir)

            if target_file is None:
                broken.append(f"{rel_source}: '{href}' -> no such page")
                continue

            if target_file.suffix != ".html":
                # A real file, but not a page - e.g. glightbox wraps images
                # in <a href="foo.png#only-light">, where the fragment is a
                # CSS hook (see extra.css's #only-light/#only-dark rules),
                # not a document anchor to look up inside the image itself.
                continue

            if fragment and fragment not in _ids_in(target_file, id_cache):
                broken.append(
                    f"{rel_source}: '{href}' -> #{fragment} not found in "
                    f"{target_file.relative_to(public_dir)}"
                )

    assert not broken, "Broken internal links:\n" + "\n".join(broken)
