# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""customisation batch: checks the template-specific customisation points
documented in docs/starthere/customise.md - the ones not already covered by
a more specific batch (numbering: heading/appendix numbering; word_count:
exclude_from_word_count; captions: figure/table-caption; content/links:
leaked syntax and broken links; pdf_structure: cover page has *some* word
count/repo URL) - actually reflect what's configured in zensical.toml, not
just present-and-plausible.

Where a value is duplicated across independent files by necessity (website
CSS in extra.css vs PDF CSS generated in build_pdf.py, since Pandoc's HTML
has no .md-typeset wrapper for the website's own rules to match against -
see "How the PDF handles this" throughout customise.md), tests check both
copies stay in sync with each other, not just that either one individually
looks right - the two are free to drift silently otherwise, which is
exactly the kind of thing a human reviewer skims past.

Not covered here: "Changing heading numbering"'s heading_numbering = false
toggle, and reference_style = "global" - both need a second build under a
different config to observe, which this batch (like the rest of the suite)
deliberately doesn't trigger itself (see run_tests.py); "Directory
structure" and "Finalising your document" are instructional, not
behaviour; "Social links" and a custom "Favicon" are unset in this
template's own zensical.toml, so there's nothing configured to check
against."""

import hashlib
import inspect
import re

from zendoc.pdf.build import build_pdf
from zendoc.pdf.css import build_css
from zendoc.pdf.icons import build_icon_registry, discover_icon_dirs
from zendoc.settings import reference_style_values
from zendoc.zensical_macros import _get_repo_url

from conftest import PDF_PATH, REPO_ROOT, soup_for

EXTRA_CSS_PATH = REPO_ROOT / "docs" / "stylesheets" / "extra.css"


def _read(path):
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Site logo
# ---------------------------------------------------------------------------

def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_correct_logo_pair_is_copied_for_this_remote(docs_dir, macros):
    """Institution branding (see customise.md) swaps logo_black.png/
    logo_white.png for either the Surrey or default pair, depending on
    where *this* checkout's remote actually points - this repo builds on
    both a GitHub Actions pipeline (non-Surrey) and a Surrey GitLab mirror
    pipeline (see project docs on syncing the mirror), so the expected pair
    depends on which one is currently running this test, not a hardcoded
    assumption - reuses macros._detect_is_surrey() (the exact same check
    define_env() itself uses) rather than guessing.

    Compared by sha256 digest, not raw bytes: both files are real binary
    PNGs, and pytest's assertion introspection tries to diff the full raw
    bytes on a failing `assert a == b`, which for two ~100KB+ PNGs can
    balloon into a multi-megabyte failure message - enough to exceed
    GitLab CI's job log size limit outright on a real failure. A short hex
    digest gives a clean, readable failure either way."""
    is_surrey = macros._detect_is_surrey()
    expected_name = "logo_surrey" if is_surrey else "logo_default"
    other_name = "logo_default" if is_surrey else "logo_surrey"
    assets = docs_dir / "assets"
    for variant in ("black", "white"):
        active = _sha256(assets / f"logo_{variant}.png")
        expected = _sha256(assets / f"{expected_name}_{variant}.png")
        other = _sha256(assets / f"{other_name}_{variant}.png")
        assert active == expected, f"logo_{variant}.png doesn't match {expected_name}_{variant}.png"
        assert active != other, f"logo_{variant}.png matches {other_name}_{variant}.png unexpectedly"


def test_built_website_includes_the_active_logo_files(public_dir):
    assert (public_dir / "assets" / "logo_black.png").exists()
    assert (public_dir / "assets" / "logo_white.png").exists()


def test_pdf_cover_page_has_an_embedded_logo_image(pdf_doc):
    """The website check above only confirms the right logo *files* exist -
    this confirms the PDF cover page actually embeds one, using
    get_image_info() (bounding boxes of images actually drawn on this
    specific page) rather than get_images() (every image in the PDF's
    shared resource pool, most of which - e.g. Figure 11.3/11.4's header/
    footer diagrams - live nowhere near the cover page)."""
    cover_images = pdf_doc[0].get_image_info()
    assert cover_images, "No image found on the PDF cover page"


# ---------------------------------------------------------------------------
# Site metadata
# ---------------------------------------------------------------------------

def test_website_title_and_description_match_config(public_dir, zensical_config):
    project = zensical_config["project"]
    soup = soup_for(public_dir / "index.html")
    assert project["site_name"] in soup.find("title").get_text()
    description = soup.find("meta", attrs={"name": "description"})
    assert description["content"] == project["site_description"]


# ---------------------------------------------------------------------------
# Copyright
# ---------------------------------------------------------------------------

def test_copyright_text_appears_on_website_and_pdf(public_dir, pdf_full_text, zensical_config):
    configured = zensical_config["project"]["copyright"].strip()
    soup = soup_for(public_dir / "index.html")
    footer_text = soup.get_text()
    assert configured in footer_text
    assert any(configured in page for page in pdf_full_text)


# ---------------------------------------------------------------------------
# Repository link
# ---------------------------------------------------------------------------

def test_repository_link_matches_config(public_dir, zensical_config):
    project = zensical_config["project"]
    soup = soup_for(public_dir / "index.html")
    repo_link = soup.find("a", attrs={"title": "Go to repository"}) or soup.find(
        "a", href=project["repo_url"]
    )
    assert repo_link is not None, "No repository link found on the built cover page"
    assert repo_link["href"] == project["repo_url"]


def test_repository_link_is_independent_of_cover_page_repourl_marker(zensical_config):
    """customise.md's note in "Repository link": the sidebar link above
    reads zensical.toml's own repo_url directly; the cover page's
    {{ repo_url }}/{REPOURL} marker is computed independently from the
    local git remote (see zendoc.zensical_macros._get_repo_url()) - in
    practice they usually match, but they're not the same mechanism.
    Confirms that here."""
    configured = zensical_config["project"]["repo_url"]
    computed = _get_repo_url()
    assert computed, "zendoc.zensical_macros._get_repo_url() returned nothing - no git remote configured?"
    assert computed.rstrip("/") == configured.rstrip("/")


# ---------------------------------------------------------------------------
# Release number (issue #60)
# ---------------------------------------------------------------------------

def test_release_number_looks_like_a_real_tag_when_present(pdf_full_text):
    """Explicitly PDF-only (see "Word count and repository link" - "there's
    no website equivalent"), and explicitly allowed to be absent (most
    forks of this template never publish a release, so the whole line is
    dropped rather than showing an empty "Release:" - see #60), so this
    can't assert the line is always present. If it *is* present, it should
    look like a real tag, not a leaked, un-substituted {RELEASE} marker."""
    match = re.search(r"Release:\s*(\S*)", pdf_full_text[0])
    if match is None:
        return  # no release published for this repo right now - allowed
    tag = match.group(1)
    assert tag and tag != "{RELEASE}", f"Release line present but looks unsubstituted: {tag!r}"
    assert re.match(r"^v?\d+(\.\d+)*", tag), f"Release tag doesn't look like a version: {tag!r}"


def test_release_number_never_appears_on_the_website(public_dir):
    """"Never appears" means "is CSS-hidden", not "absent from the HTML" -
    .pdf-only content still exists in the markup (see
    test_pdf_only_class_is_hidden_on_the_website's CSS check for how it's
    actually hidden), so this confirms any real "Release:"-starting
    paragraph carries the .pdf-only class, rather than searching the
    page's whole get_text(). Deliberately checks real <p> tags, not a
    plain text search - the actual Release <p> sits right after an HTML
    comment that itself contains the word "Release:" while explaining the
    marker, which a naive string search would match first instead of the
    real element."""
    soup = soup_for(public_dir / "index.html")
    release_paragraphs = [
        p for p in soup.find_all("p")
        if p.get_text(strip=True).startswith("Release:")
    ]
    if not release_paragraphs:
        return  # marker line deleted entirely - also fine, nothing to check
    for p in release_paragraphs:
        assert "pdf-only" in (p.get("class") or []), f"'Release:' paragraph found outside .pdf-only: {p}"


# ---------------------------------------------------------------------------
# Colour scheme
# ---------------------------------------------------------------------------

def test_light_and_dark_palettes_are_both_configured(zensical_config):
    palettes = zensical_config["project"]["theme"]["palette"]
    schemes = {p["scheme"] for p in palettes}
    assert schemes == {"default", "slate"}, f"Expected light+dark palettes, got: {schemes}"


def test_website_has_a_theme_toggle_for_both_schemes(public_dir):
    soup = soup_for(public_dir / "index.html")
    labels = {el.get("title") or el.get_text(strip=True) for el in soup.find_all(["label", "input"])}
    assert any("dark" in str(label).lower() for label in labels)
    assert any("light" in str(label).lower() for label in labels)


# ---------------------------------------------------------------------------
# Page heading (header background image)
# ---------------------------------------------------------------------------

def test_header_background_images_exist_and_are_referenced(docs_dir):
    css = _read(EXTRA_CSS_PATH)
    assert "header-background.jpg" in css
    assert "header-background-dark.jpg" in css
    assert (docs_dir / "assets" / "header-background.jpg").exists()
    assert (docs_dir / "assets" / "header-background-dark.jpg").exists()


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

def test_pdf_uses_the_documented_default_fonts_when_unset(zensical_config):
    """[project.theme.font] is commented out in this template's own
    zensical.toml, so both outputs should fall back to the documented
    defaults (customise.md's "Fonts" section: Inter / JetBrains Mono) -
    zendoc.pdf.build_pdf()'s own default, read directly via its signature
    rather than reimplemented here (build_pdf.py no longer hardcodes these -
    see zendoc-extension#96 - it only passes them through when configured)."""
    assert "font" not in zensical_config["project"]["theme"]
    defaults = inspect.signature(build_pdf).parameters
    assert defaults["main_font"].default == "Inter"
    assert defaults["mono_font"].default == "JetBrains Mono"


def test_pdf_compiled_css_actually_uses_the_default_fonts(pdf_doc):
    """Confirms the default from the test above actually reaches the
    compiled PDF stylesheet, not just that the Python default exists."""
    # WeasyPrint embeds requested font family names in the PDF's font
    # resources; a loose substring search across every font descriptor is
    # enough to confirm "Inter"/"JetBrains Mono" were requested somewhere.
    found_main, found_mono = False, False
    for page in pdf_doc:
        for font in page.get_fonts():
            name = (font[3] or "").lower()
            if "inter" in name:
                found_main = True
            if "jetbrains" in name:
                found_mono = True
    assert found_main, "No 'Inter' font found anywhere in the compiled PDF"
    assert found_mono, "No 'JetBrains Mono' font found anywhere in the compiled PDF"


def test_website_also_uses_the_default_fonts(public_dir):
    """customise.md's "Fonts" section: "the PDF build reuses this same
    setting" - the website's own font is the actually-configured value the
    PDF then reuses, so this is the more fundamental of the two checks, not
    a redundant one. Zensical sets --md-text-font as an inline CSS custom
    property and loads --md-code-font from Google Fonts."""
    html = (public_dir / "index.html").read_text(encoding="utf-8")
    assert '--md-text-font:"Inter"' in html
    assert "JetBrains" in html


# ---------------------------------------------------------------------------
# Icons
# ---------------------------------------------------------------------------

def test_configured_icon_names_resolve_to_real_files(zensical_config):
    """theme.icon.* and theme.icon.admonition.* (see "Icons") name icons as
    "set/path" (e.g. "fontawesome/brands/github") - build_icon_registry()
    is the same lookup build_pdf.py itself uses (via zendoc.pdf.icons - see
    zendoc-extension#96) to resolve an icon shortcode to a real .svg file;
    a typo here would silently 404/break on the website and leak as
    missing content in the PDF."""
    docs_dir_name = zensical_config["project"].get("docs_dir", "docs")
    icon_dirs = discover_icon_dirs(docs_dir_name)
    registry = build_icon_registry(icon_dirs)

    theme_icon = zensical_config["project"]["theme"]["icon"]
    names = [v for k, v in theme_icon.items() if k != "admonition" and isinstance(v, str)]
    names += list(theme_icon.get("admonition", {}).values())
    assert names, "No icon names found in [project.theme.icon] to check"

    missing = [name for name in names if name.replace("/", "-").lower() not in registry]
    assert not missing, f"Configured icon(s) not found in the icon registry: {missing}"


# ---------------------------------------------------------------------------
# Navigation and feature toggles
# ---------------------------------------------------------------------------

def test_enabled_features_have_no_duplicates(zensical_config):
    features = zensical_config["project"]["theme"]["features"]
    assert len(features) == len(set(features)), "Duplicate entries in [project.theme].features"


def test_a_sample_of_enabled_features_visibly_took_effect(public_dir, zensical_config):
    features = set(zensical_config["project"]["theme"]["features"])
    soup = soup_for(public_dir / "index.html")

    if "navigation.tabs" in features:
        assert soup.find(attrs={"data-md-component": "tabs"}) is not None


def test_enabled_features_reach_the_built_sites_own_config(public_dir, zensical_config):
    """Most theme features (content.code.copy among them) are applied by
    client-side JS reading an embedded page config, not baked into the
    static HTML at build time - e.g. the copy button itself only exists
    once bundle.js runs in a real browser, which this fast/synthetic test
    suite deliberately doesn't drive (see docs/starthere/testing.md).
    What's checkable without a browser, and actually the thing customise.md
    describes configuring ("comment a line out to disable that feature"),
    is that the configured features list reaches this embedded config at
    all - each built page embeds its own copy inline, so this checks a
    representative one, not all of them."""
    configured = zensical_config["project"]["theme"]["features"]
    soup = soup_for(public_dir / "index.html")
    config_script = soup.find("script", string=re.compile(r'"features"\s*:'))
    assert config_script is not None, "No inline page-config <script> found on the built cover page"
    match = re.search(r'"features"\s*:\s*(\[[^\]]*\])', config_script.string)
    assert match is not None
    embedded_features = re.findall(r'"([\w.]+)"', match.group(1))
    missing = set(configured) - set(embedded_features)
    assert not missing, f"Configured feature(s) missing from the built site's own config: {missing}"


# ---------------------------------------------------------------------------
# Extra CSS and JavaScript
# ---------------------------------------------------------------------------

def test_extra_css_and_js_are_built_and_referenced(public_dir, zensical_config):
    project = zensical_config["project"]
    soup = soup_for(public_dir / "index.html")

    for css_path in project.get("extra_css", []):
        assert (public_dir / css_path).exists(), f"{css_path} missing from built site"
        assert any(css_path in (link.get("href") or "") for link in soup.find_all("link")), (
            f"{css_path} not referenced by a <link> tag"
        )

    for js_path in project.get("extra_javascript", []):
        if js_path.startswith("http"):
            continue
        assert (public_dir / js_path).exists(), f"{js_path} missing from built site"
        assert any(js_path in (script.get("src") or "") for script in soup.find_all("script")), (
            f"{js_path} not referenced by a <script> tag"
        )


# ---------------------------------------------------------------------------
# Navigation structure
# ---------------------------------------------------------------------------

def test_nav_snippet_macro_matches_the_real_nav_config(macros, zensical_config):
    """customise.md's "Navigation structure" section shows this template's
    own nav "pulled directly from zensical.toml" via the nav_snippet()
    macro, described as updating automatically as nav changes - confirms
    that's actually true, not just true when it was last written."""
    snippet = macros._get_nav_snippet()
    project = zensical_config["project"]
    # Every top-level group name in the real nav should appear in the
    # rendered snippet text.
    for group in project["nav"]:
        for group_name in group:
            assert group_name in snippet, f"Top-level nav group '{group_name}' missing from nav_snippet()"


# ---------------------------------------------------------------------------
# References and bibliography / Acronyms / Glossary - shared spacing rule
# ---------------------------------------------------------------------------

def _css_rule_value(css_text, selector, property_name, occurrence=0):
    """Returns the Nth (0-indexed) occurrence of selector { ... property: X }
    in css_text - reference_style_css in build_pdf.py has two branches
    (if reference_style_global / else) that both define "p.reference +
    p.reference", in that source order, so occurrence=1 picks out the
    "else" (european/default) branch's value specifically."""
    pattern = re.compile(re.escape(selector) + r"\s*\{[^}]*?" + re.escape(property_name) + r"\s*:\s*([^;!]+)", re.DOTALL)
    matches = pattern.findall(css_text)
    return matches[occurrence].strip() if len(matches) > occurrence else None


def test_reference_acronym_glossary_spacing_matches_between_website_and_pdf():
    """.reference/.acronym/.glossary entries get tight paragraph spacing on
    both outputs (see "References and bibliography"), driven by
    project.extra.reference_spacing_european/reference_indent_global/
    reference_spacing_global in zensical.toml (issue #66). Both the website
    (via zendoc.zensical_macros) and the PDF (via zendoc.pdf.css.build_css())
    now derive these from the same zendoc.settings.reference_style_values() -
    see zendoc-extension#96 - so this checks that shared function's own
    defaults, plus confirms build_css()'s generated CSS actually plugs each
    value into the right selector (not, say, the wrong variable
    copy-pasted into the acronym/glossary block)."""
    _, spacing_european, indent_global, spacing_global = reference_style_values({})
    pdf_defaults = inspect.signature(build_css).parameters

    for key, expected_default, shared_default in (
        ("reference_spacing_european", "-0.8em", spacing_european),
        ("reference_indent_global", "1.27cm", indent_global),
        ("reference_spacing_global", "2em", spacing_global),
    ):
        pdf_default = pdf_defaults[key].default
        assert shared_default == expected_default, f"zendoc.settings' {key!r} default is {shared_default!r}, expected {expected_default!r}"
        assert pdf_default == expected_default, f"zendoc.pdf.css.build_css()'s {key!r} default is {pdf_default!r}, expected {expected_default!r}"

    # The generated CSS itself: each selector's margin-top/indent should
    # actually reflect the given values, in both the default "european"
    # branch and the "global" branch, not a stray hardcoded literal or the
    # wrong variable copy-pasted into the acronym/glossary block.
    css_kwargs = dict(
        main_font="Inter", mono_font="JetBrains Mono", copyright_text="", site_name="",
        reference_spacing_european="-0.8em", reference_indent_global="1.27cm", reference_spacing_global="2em",
    )
    european_css = build_css(reference_style_global=False, **css_kwargs)
    assert european_css.count("margin-top: -0.8em !important;") == 3, (
        "Expected exactly 3 uses (reference/acronym/glossary, european/default branch) - "
        "one may have drifted onto a stray hardcoded value instead"
    )

    global_css = build_css(reference_style_global=True, **css_kwargs)
    assert "padding-left: 1.27cm !important;" in global_css
    assert "text-indent: -1.27cm !important;" in global_css
    assert "margin-top: 2em !important;" in global_css
    # Acronym/glossary always keep the tight "european" spacing, regardless
    # of reference_style_global - only the reference block itself switches.
    assert global_css.count("margin-top: -0.8em !important;") == 2


# ---------------------------------------------------------------------------
# Institution branding
# ---------------------------------------------------------------------------

def test_correct_branding_shown_for_this_repo(public_dir, pdf_full_text, macros):
    """Institution branding (see customise.md) shows one of two {% if
    is_surrey %} branches on the cover page - which one is correct depends
    on which remote *this* checkout is actually building against (see
    macros._detect_is_surrey(), reused here rather than hardcoding an
    assumption - this repo builds on both a GitHub Actions pipeline
    (non-Surrey) and a Surrey GitLab mirror pipeline)."""
    soup = soup_for(public_dir / "index.html")
    website_text = soup.get_text()
    if macros._detect_is_surrey():
        assert "Faculty of Engineering and Physical Sciences" in website_text
        assert "Crested Eagle Labs" not in website_text
        assert "Faculty of Engineering and Physical Sciences" in pdf_full_text[0]
    else:
        assert "Crested Eagle Labs" in website_text
        assert "University of Surrey" not in website_text
        assert "Crested Eagle Labs" in pdf_full_text[0]


# ---------------------------------------------------------------------------
# PDF-only and web-only content
# ---------------------------------------------------------------------------

def test_pdf_only_class_is_hidden_on_the_website(public_dir):
    css = _read(EXTRA_CSS_PATH)
    assert re.search(r"\.pdf-only\s*\{[^}]*display:\s*none", css)
    soup = soup_for(public_dir / "index.html")
    pdf_only_elements = soup.select(".pdf-only")
    assert pdf_only_elements, "No .pdf-only elements found on the built cover page to check"


def test_web_only_content_is_absent_from_the_pdf(pdf_doc):
    """The cover page's "Download PDF" button is .web-only (see "Download
    PDF button") - showing it inside the PDF itself would be circular, so
    no PDF link should point back at the PDF's own filename. Checked via
    the PDF's real link objects, not a text search - "PDF" alone is much
    too common a word across this template's own PDF-vs-website prose
    (e.g. "How the PDF handles this") to search for reliably."""
    offenders = [
        (page_number, link.get("uri"))
        for page_number, page in enumerate(pdf_doc)
        for link in page.get_links()
        if "site_documentation.pdf" in (link.get("uri") or "")
    ]
    assert not offenders, f"PDF contains a self-referential link to its own file: {offenders}"


# ---------------------------------------------------------------------------
# Site name
# ---------------------------------------------------------------------------

def test_site_name_appears_on_both_cover_pages(public_dir, pdf_full_text, zensical_config):
    site_name = zensical_config["project"]["site_name"]
    soup = soup_for(public_dir / "index.html")
    assert site_name in soup.get_text()
    assert site_name in pdf_full_text[0]


# ---------------------------------------------------------------------------
# Download PDF button
# ---------------------------------------------------------------------------

def test_download_pdf_button_links_to_the_real_pdf(public_dir):
    soup = soup_for(public_dir / "index.html")
    button = soup.find("a", href=re.compile(r"site_documentation\.pdf$"))
    assert button is not None, "No 'Download PDF' button found on the built cover page"
    assert (public_dir / "site_documentation.pdf").exists()


# ---------------------------------------------------------------------------
# Page header / footer content
# ---------------------------------------------------------------------------

def test_a_body_page_header_and_footer_show_the_right_content(pdf_full_text, zensical_config):
    """Picks any page past the cover/Table of Contents (identified by
    having a real "Page N of M" footer) and checks its running header shows
    site_name plus a real "<number>. <title>"/"Appendix <letter>. <title>"
    chapter heading, and its footer shows the configured copyright text -
    not tied to a specific hardcoded page number, so it stays correct as
    nav is reordered or grows (see issue #46)."""
    site_name = zensical_config["project"]["site_name"]
    copyright_text = zensical_config["project"]["copyright"].strip()
    page_counter = re.compile(r"Page (\d+) of (\d+)")
    chapter_pattern = re.compile(r"(?:\d+\.|Appendix [A-Z]\.)\s+\S")

    for text in pdf_full_text[1:]:
        match = page_counter.search(text)
        if not match:
            continue
        assert site_name in text, f"site_name missing from a body page's header/footer:\n{text[-200:]}"
        assert copyright_text in text, f"copyright missing from a body page's footer:\n{text[-200:]}"
        assert chapter_pattern.search(text), f"No chapter heading pattern found on body page:\n{text[:200]}"
        return
    raise AssertionError("No body page with a 'Page N of M' footer found to check")


# ---------------------------------------------------------------------------
# Page size and margins
# ---------------------------------------------------------------------------

def test_pdf_page_size_and_margins_match_configured_defaults(pdf_doc, zensical_config):
    """project.extra.pdf_page_size/pdf_margin_* (added in #51) default to
    A4 / 2cm on every side when unset, as they are in this template's own
    zensical.toml - confirms the configured defaults actually reach the
    built PDF's real page geometry, not just that build_pdf.py has a
    default value defined somewhere."""
    extra = zensical_config["project"].get("extra", {})
    assert extra.get("pdf_page_size", "A4") == "A4"
    for side in ("top", "right", "bottom", "left"):
        assert extra.get(f"pdf_margin_{side}", "2cm") == "2cm"

    page = pdf_doc[1]  # skip the cover, which has its own layout
    pt_per_cm = 28.3465
    a4_width_pt, a4_height_pt = 595.28, 841.89
    assert abs(page.rect.width - a4_width_pt) < 1
    assert abs(page.rect.height - a4_height_pt) < 1

    # Left margin: leftmost text span's x0 should sit ~2cm from the edge.
    text_dict = page.get_text("dict")
    x0_values = [
        span["bbox"][0]
        for block in text_dict["blocks"] if "lines" in block
        for line in block["lines"]
        for span in line["spans"]
    ]
    assert x0_values, "No text found on the sampled body page"
    assert abs(min(x0_values) - 2 * pt_per_cm) < 10


# ---------------------------------------------------------------------------
# Screenshots
# ---------------------------------------------------------------------------

def test_screenshot_class_styling_matches_between_website_and_pdf():
    """.screenshot's border/border-radius/box-shadow (see "Screenshots") are
    duplicated - extra.css for the website, a plain selector in
    zendoc.pdf.css.build_css() for the PDF (see zendoc-extension#96; same
    "no .md-typeset wrapper in Pandoc's HTML" reason as the reference/
    acronym/glossary spacing above) - checks the two stay in sync."""
    extra_css = _read(EXTRA_CSS_PATH)
    pdf_css = build_css(main_font="Inter", mono_font="JetBrains Mono", copyright_text="", site_name="")
    for prop in ("border", "border-radius", "box-shadow"):
        website_value = _css_rule_value(extra_css, ".md-typeset img.screenshot", prop)
        pdf_value = _css_rule_value(pdf_css, "img.screenshot", prop)
        assert website_value is not None, f"No website .screenshot rule found for {prop}"
        assert pdf_value is not None, f"No PDF .screenshot rule found for {prop}"
        assert website_value == pdf_value, (
            f".screenshot {prop} differs: website={website_value!r} vs PDF={pdf_value!r}"
        )
