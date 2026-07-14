# Copyright (c) 2025-2026 Mark Buckwell and contributors
# SPDX-License-Identifier: MIT

import os
import re
import subprocess
import shutil
from pathlib import Path
from urllib.parse import urlparse, urlunparse
import toml
from zendoc.headings import prescan as zendoc_heading_prescan

# This function is called by Zensical to identify whether the documentation is being built
# in a Surrey GitLab CI/CD Pipeline or if the repository URL contains the domain `surrey.gitlab.ac.uk`.
# It sets a boolean variable `is_surrey` in the environment variables, which can be used in Markdown
# files to conditionally display content based on the build environment.


def _extract_nav_md_files(nav_element):
    """Recursively walks the Zensical nav tree to list .md files in nav order."""
    files = []
    if isinstance(nav_element, str):
        if nav_element.endswith('.md'):
            files.append(nav_element)
    elif isinstance(nav_element, list):
        for item in nav_element:
            files.extend(_extract_nav_md_files(item))
    elif isinstance(nav_element, dict):
        for value in nav_element.values():
            files.extend(_extract_nav_md_files(value))
    return files


def _count_top_level_headings(path):
    """Counts top-level (single #) ATX headings in a markdown file, skipping fenced
    code blocks, HTML comments (e.g. the copyright header at the top of each page),
    and headings tagged {.unnumbered} (e.g. the hidden cover-page title)."""
    try:
        text = Path(path).read_text(encoding='utf-8')
    except OSError:
        return 0
    count = 0
    in_fence = False
    in_comment = False
    for line in text.splitlines():
        stripped = line.strip()
        if not in_comment and (stripped.startswith('```') or stripped.startswith('~~~')):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not in_comment and '<!--' in stripped:
            in_comment = True
        if in_comment:
            if '-->' in stripped:
                in_comment = False
            continue
        if re.match(r'^#\s+\S', line) and '.unnumbered' not in line:
            count += 1
    return count


def _count_words_in_markdown(path):
    """Rough prose word count for a single markdown file: strips fenced code,
    inline code, HTML tags/comments, and markdown link/image/emphasis syntax
    before splitting on whitespace. Mirrors compute_pdf_word_count() in
    build_pdf.py, which does the same thing for the PDF build."""
    try:
        text = Path(path).read_text(encoding='utf-8')
    except OSError:
        return 0
    text = re.sub(r'<!--.*?-->', ' ', text, flags=re.DOTALL)
    text = re.sub(r'```.*?```', ' ', text, flags=re.DOTALL)
    text = re.sub(r'~~~.*?~~~', ' ', text, flags=re.DOTALL)
    text = re.sub(r'`[^`]*`', ' ', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', text)
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'[#*_~>|]', ' ', text)
    return len(text.split())


def _front_matter_flag(path, key):
    """True if path's YAML front matter sets key: true. Shared by
    _page_excluded_from_word_count() and _page_is_appendix()."""
    try:
        text = Path(path).read_text(encoding='utf-8')
    except OSError:
        return False
    if not text.startswith('---'):
        return False
    parts = text.split('---', 2)
    if len(parts) < 3:
        return False
    return bool(re.search(rf'^{re.escape(key)}:\s*true\s*$', parts[1], re.MULTILINE | re.IGNORECASE))


def _page_excluded_from_word_count(path):
    """True if path's YAML front matter sets exclude_from_word_count: true -
    see "Word count" in customise.md. Used to skip pages like References,
    Acronyms, Glossary, and Originality & AI Use, which conventionally don't
    count toward a submission's word limit. Mirrors the same check in
    build_pdf.py, used there for the PDF's {WORDCOUNT} marker."""
    return _front_matter_flag(path, 'exclude_from_word_count')


def _page_is_appendix(path):
    """True if path's YAML front matter sets is_appendix: true - see
    "Appendixes" in customise.md. Used to give the page's H1 (and any H2/H3
    beneath it) letter-based numbering ("Appendix A", "A.1", ...) instead of
    continuing the document's normal numeric sequence. Mirrors the same
    check in build_pdf.py, used there for the PDF's Lua numbering filter."""
    return _front_matter_flag(path, 'is_appendix')


def _compute_site_word_count():
    """Sums the prose word count across every nav page except the cover
    (index.md) and any page opted out via exclude_from_word_count (see
    _page_excluded_from_word_count()), for the optional {{ word_count }}
    variable - see the "Word count" section in customise.md for how to show
    or hide it. Returns a comma-formatted string (e.g. "9,971") ready to drop
    straight into a page with {{ word_count }}."""
    config_path = Path('zensical.toml')
    if not config_path.exists():
        return "0"
    config = toml.load(config_path)
    project = config.get('project', {}) if isinstance(config.get('project'), dict) else {}
    nav = project.get('nav') or config.get('nav') or []
    docs_dir = Path(config.get('docs_dir', 'docs'))

    total = 0
    for rel_path in _extract_nav_md_files(nav):
        if os.path.basename(rel_path).lower() == 'index.md':
            continue
        full_path = docs_dir / rel_path
        if _page_excluded_from_word_count(full_path):
            continue
        total += _count_words_in_markdown(full_path)
    return f"{total:,}"


def _get_site_name():
    """Returns project.site_name from zensical.toml, for the {{ site_name }}
    variable - see "Customising front page" in customise.md. Used on the
    cover page instead of the PDF header (which is hidden on the cover page)
    or a second, PDF-specific marker: build_pdf.py substitutes this
    same literal "{{ site_name }}" text directly, so one line works for both
    outputs."""
    config_path = Path('zensical.toml')
    if not config_path.exists():
        return ""
    config = toml.load(config_path)
    project = config.get('project', {}) if isinstance(config.get('project'), dict) else {}
    return project.get('site_name') or config.get('site_name') or ""


def _get_repo_url():
    """Returns the fully-qualified https:// URL for the repo's origin
    remote (converting from git@host:path.git SSH syntax if necessary), for
    the optional {{ repo_url }} variable - see "Word count and repository
    link" in customise.md for how to show or hide it. Returns "" if there's
    no git remote configured (e.g. the template hasn't been cloned yet).

    A GitLab CI/CD job's own checkout has its origin remote rewritten to
    embed a short-lived "gitlab-ci-token:<token>@" credential for
    authentication (see the Surrey mirror pipeline) - stripped out below so
    it never ends up baked into a published PDF/website's repo link."""
    try:
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
    except Exception:
        return ""
    if not remote_url:
        return ""
    ssh_match = re.match(r'^git@([^:]+):(.+?)(?:\.git)?$', remote_url)
    if ssh_match:
        host, path = ssh_match.group(1), ssh_match.group(2)
        return f"https://{host}/{path}"
    if remote_url.startswith(('http://', 'https://')):
        remote_url = re.sub(r'\.git$', '', remote_url)
        parsed = urlparse(remote_url)
        if parsed.username or parsed.password:
            netloc = parsed.hostname or ''
            if parsed.port:
                netloc += f':{parsed.port}'
            parsed = parsed._replace(netloc=netloc)
            remote_url = urlunparse(parsed)
        return remote_url
    return remote_url


def _heading_numbering_enabled():
    """Reads project.extra.heading_numbering from zensical.toml (defaults to True)."""
    config_path = Path('zensical.toml')
    if not config_path.exists():
        return True
    config = toml.load(config_path)
    project = config.get('project', {}) if isinstance(config.get('project'), dict) else {}
    extra = project.get('extra', {}) if isinstance(project.get('extra'), dict) else {}
    return bool(extra.get('heading_numbering', True))


def _reference_style():
    """Reads project.extra.reference_style from zensical.toml (defaults to "european").
    Returns "global" only when explicitly set to that value; anything else falls
    back to "european", so typos default to the current/default look rather than
    silently doing nothing."""
    return _reference_style_values()[0]


def _reference_style_values():
    """Reads project.extra.reference_style plus the three spacing/indent values
    behind it (see "References and bibliography" in customise.md) - shared by
    reference_style()/acronym_style()/glossary_style() below and their
    build_pdf.py PDF equivalents, so a value only needs to change in one place
    (zensical.toml) rather than three (extra.css, macros.py, build_pdf.py).
    Returns (style, spacing_european, indent_global, spacing_global):
    - style: "global" only when explicitly set to that value, else "european".
    - spacing_european: margin-top between consecutive entries in the default
      "european" look - also used, unconditionally, for the acronym and
      glossary list spacing (see acronym_style()/glossary_style() below).
    - indent_global / spacing_global: the "global" look's hanging indent and
      inter-entry spacing."""
    config_path = Path('zensical.toml')
    if not config_path.exists():
        return 'european', '-0.8em', '1.27cm', '2em'
    config = toml.load(config_path)
    project = config.get('project', {}) if isinstance(config.get('project'), dict) else {}
    extra = project.get('extra', {}) if isinstance(project.get('extra'), dict) else {}
    style = str(extra.get('reference_style', 'european')).strip().lower()
    style = 'global' if style == 'global' else 'european'
    spacing_european = str(extra.get('reference_spacing_european', '-0.8em'))
    indent_global = str(extra.get('reference_indent_global', '1.27cm'))
    spacing_global = str(extra.get('reference_spacing_global', '2em'))
    return style, spacing_european, indent_global, spacing_global


def _get_nav_snippet():
    """Extracts the current `nav = [...]` block from zensical.toml verbatim -
    same indentation, same comments - for the nav_snippet() macro used in
    Customisation's "Navigation structure" section, so that example always
    matches the real config instead of drifting stale as nav changes. Reads
    the raw file text and bracket-matches rather than round-tripping through
    `toml.load()`, since that would lose the formatting and comments that
    make the example worth showing in the first place. Returns "" if
    zensical.toml or a nav block can't be found."""
    config_path = Path('zensical.toml')
    if not config_path.exists():
        return ''
    text = config_path.read_text(encoding='utf-8')
    match = re.search(r'^nav\s*=\s*\[', text, flags=re.MULTILINE)
    if not match:
        return ''
    bracket_start = text.index('[', match.start())
    depth = 0
    for i in range(bracket_start, len(text)):
        if text[i] == '[':
            depth += 1
        elif text[i] == ']':
            depth -= 1
            if depth == 0:
                return text[match.start():i + 1]
    return ''


def _detect_is_surrey(env=None):
    """True if this checkout appears to be building for the University of
    Surrey - checked via the GitLab CI/CD pipeline's own CI_SERVER_HOST env
    var (true for both a direct Surrey GitLab run and this template's own
    GitHub-to-Surrey-GitLab mirror sync), the local git remote (covers
    `zensical serve` on a locally-cloned Surrey checkout), and - when env is
    given - a brute-force string scan of Zensical's config as a fallback.
    Extracted as a standalone function (rather than inlined in define_env()
    below) so the test suite can call the exact same detection logic instead
    of hardcoding an assumption about which remote CI happens to be running
    against - see test_customisation.py's site-logo tests, which run
    unchanged against both this repo's GitHub Actions pipeline (non-Surrey)
    and its Surrey GitLab mirror pipeline (Surrey)."""
    target_domain = 'surrey.ac.uk'

    # Check 1: GitLab CI/CD Pipeline environment
    if os.getenv('CI_SERVER_HOST') == target_domain:
        return True

    # Check 2: Local Git Remote Origin (Perfect for local 'zensical serve' testing)
    try:
        # Automatically asks your local folder where its remote points
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        if target_domain in remote_url:
            return True
    except Exception:
        # Fails silently if git isn't installed or initialized in this directory
        pass

    # Check 3: Brute-force string scan of Zensical's entire config scope
    if env is not None:
        if hasattr(env, 'config') and target_domain in str(env.config):
            return True
        if hasattr(env, 'variables') and target_domain in str(env.variables):
            return True

    return False


def define_env(env):
    # ==========================================
    # 1. SURREY ENVIRONMENT DETECTION LOGIC
    # ==========================================
    final_result = _detect_is_surrey(env)
    # final_result = False  # This line is for testing purposes; remove it in production to enable the macro.

    # Bind the variable to your markdown files
    env.variables['is_surrey'] = final_result

    # Word count of the whole site (every nav page except the cover), for the
    # optional {{ word_count }} variable - see "Customising front page" in
    # customise.md.
    env.variables['word_count'] = _compute_site_word_count()

    # Fully-qualified repo URL, for the optional {{ repo_url }} variable -
    # see "Customising front page" in customise.md.
    env.variables['repo_url'] = _get_repo_url()

    # Site name, for the {{ site_name }} variable used on the cover page -
    # see "Customising front page" in customise.md.
    env.variables['site_name'] = _get_site_name()

    # ==========================================
    # 2. GLOBAL LOGO SWAP ON STARTUP
    # ==========================================
    # This runs unconditionally when 'zensical serve' or 'zensical build' starts
    # The code is used to swap the logo depending on whether the documentation is being built
    # in a Surrey GitLab CI/CD Pipeline or if the repository URL contains the domain `surrey.gitlab.ac.uk`.
    # This allows for the use of a different logo for the University of Surrey and other environments.
    try:
        # Define paths safely using Path
        dest_white = Path('docs/assets/logo_white.png')
        dest_black = Path('docs/assets/logo_black.png')

        # Ensure the destination folder exists
        dest_white.parent.mkdir(parents=True, exist_ok=True)

        if final_result:
            # If Surrey environment, copy Surrey logos
            shutil.copy2('docs/assets/logo_surrey_white.png', dest_white)
            shutil.copy2('docs/assets/logo_surrey_black.png', dest_black)
            print("[Zensical Startup] Applied Surrey branding logos.")
        else:
            # Otherwise, copy Eagle logos
            shutil.copy2('docs/assets/logo_default_white.png', dest_white)
            shutil.copy2('docs/assets/logo_default_black.png', dest_black)
            print("[Zensical Startup] Applied default branding logos.")
            
    except FileNotFoundError as e:
        print(f"[Zensical Startup Warning] Could not copy logos: {e}")
        print("Please ensure logo_surrey_*.png and logo_default_*.png exist in docs/assets/")

    @env.macro
    def heading_counter_reset(page):
        """Replaces the old hand-maintained <style> counter-reset block. Computes,
        from this page's position in zensical.toml's nav, how many top-level
        headings appear on every page before it, so heading numbering (and the
        matching sidebar numbering) continues seamlessly across pages - the same
        way section numbering continues across chapters in the PDF build.
        Usage: place `{{ heading_counter_reset(page) }}` near the top of each page;
        nothing else needs to change when you reorder pages or add/remove headings.
        Set project.extra.heading_numbering = false in zensical.toml to turn
        numbering off entirely (content and sidebar) across the whole site.

        Pages flagged is_appendix: true (see "Appendixes" in customise.md) get
        letter-based numbering instead - "Appendix A", "A.1", "A.1.1". Since
        the letter is already known here, this bakes it into the override
        CSS as a literal string rather than using CSS's own
        counter(name, upper-alpha) styling - simpler, and it keeps the sidebar
        table of contents (which can't easily mix a letter into a counter()
        expression built for numbers) working the same way.

        The start count/letter themselves come from zendoc.headings'
        prescan() (see zensical.toml's numbering="continuous" config for
        zendoc.headings) rather than being recomputed here - this macro's
        only job is formatting them into this template's own CSS class
        names; zendoc.headings is the single source of truth for what
        number/letter a page actually gets, so this always matches what
        \ref{} shows for a heading on this page (see zendoc-template#89).

        Figure/table captions (see "Captions" in customise.md) follow the
        same pattern: the base rule in extra.css prepends "Figure "/"Table "
        plus counter(h1-count) in front of pymdownx.blocks.caption's own
        per-page auto-number, which already works unmodified on a normal
        numeric page (h1-count is already this page's chapter number by the
        time a caption appears) - only the disabled and appendix cases below
        need an override, exactly like the heading rules above."""
        if not _heading_numbering_enabled():
            return (
                '<style>\n'
                '  .md-typeset h1::before,\n'
                '  .md-typeset h2::before,\n'
                '  .md-typeset h3::before,\n'
                '  .md-nav--secondary > .md-nav__list > .md-nav__item > .md-nav__link .md-ellipsis::before,\n'
                '  .md-nav--secondary > .md-nav__list > .md-nav__item .md-nav__list > .md-nav__item > .md-nav__link .md-ellipsis::before {\n'
                '    content: "" !important;\n'
                '  }\n'
                '  .zendoc-figure-caption .caption-prefix::before { content: "Figure " !important; }\n'
                '  .zendoc-table-caption .caption-prefix::before { content: "Table " !important; }\n'
                '</style>'
            )
        page_path = getattr(page, 'path', '')
        prescan = zendoc_heading_prescan()
        start_counts, appendix_letters = prescan if prescan is not None else ({}, {})
        letter = appendix_letters.get(page_path)
        if letter:
            return (
                '<style>\n'
                f'  .md-typeset h1::before {{ content: "Appendix {letter}. " !important; }}\n'
                f'  .md-typeset h2::before {{ content: "{letter}." counter(h2-count) " " !important; }}\n'
                f'  .md-typeset h3::before {{ content: "{letter}." counter(h2-count) "." counter(h3-count) " " !important; }}\n'
                f'  .md-nav--secondary > .md-nav__list > .md-nav__item > .md-nav__link .md-ellipsis::before {{ content: "{letter}." counter(toc2) " " !important; }}\n'
                f'  .md-nav--secondary > .md-nav__list > .md-nav__item .md-nav__list > .md-nav__item > .md-nav__link .md-ellipsis::before {{ content: "{letter}." counter(toc2) "." counter(toc3) " " !important; }}\n'
                f'  .zendoc-figure-caption .caption-prefix::before {{ content: "Figure {letter}." !important; }}\n'
                f'  .zendoc-table-caption .caption-prefix::before {{ content: "Table {letter}." !important; }}\n'
                '</style>'
            )
        n = start_counts.get(page_path, 0)
        return (
            '<style>\n'
            f'  .md-typeset {{ counter-reset: h1-count {n} !important; }}\n'
            f'  .md-nav--primary {{ counter-reset: toc1 {n + 1} !important; }}\n'
            '</style>'
        )

    @env.macro
    def reference_style():
        """Controls the layout of .reference paragraphs on the References page
        (see docs/references.md). The default look is the "european" style:
        single line spacing throughout, no indent, entries close together -
        spacing set by project.extra.reference_spacing_european. Set
        project.extra.reference_style = "global" in zensical.toml to switch to
        the common APA/MLA/Chicago style instead - single line spacing within
        each entry, but double spacing *between* entries (reference_spacing_global),
        with a hanging indent on wrapped lines (reference_indent_global). Usage:
        place `{{ reference_style() }}` once near the top of the references page."""
        style, spacing_european, indent_global, spacing_global = _reference_style_values()
        if style != 'global':
            return (
                '<style>\n'
                '  .md-typeset p.reference + p.reference {\n'
                f'    margin-top: {spacing_european} !important;\n'
                '  }\n'
                '</style>'
            )
        return (
            '<style>\n'
            '  .md-typeset p.reference {\n'
            f'    padding-left: {indent_global} !important;\n'
            f'    text-indent: -{indent_global} !important;\n'
            '  }\n'
            '  .md-typeset p.reference + p.reference {\n'
            f'    margin-top: {spacing_global} !important;\n'
            '  }\n'
            '</style>'
        )

    @env.macro
    def acronym_style():
        """Controls the layout of .acronym paragraphs on the Acronyms page
        (see docs/acronyms.md) - same tight spacing as the References page's
        default "european" look, and the same project.extra.reference_spacing_european
        setting (see reference_style() above), since neither the acronym nor
        glossary list has a "global"-style alternative to switch to. Usage:
        place `{{ acronym_style() }}` once near the top of the acronyms page."""
        _, spacing_european, _, _ = _reference_style_values()
        return (
            '<style>\n'
            '  .md-typeset p.acronym + p.acronym {\n'
            f'    margin-top: {spacing_european} !important;\n'
            '  }\n'
            '</style>'
        )

    @env.macro
    def glossary_style():
        """Controls the layout of .glossary paragraphs on the Glossary page
        (see docs/glossary.md) - see acronym_style() above, same reasoning.
        Usage: place `{{ glossary_style() }}` once near the top of the
        glossary page."""
        _, spacing_european, _, _ = _reference_style_values()
        return (
            '<style>\n'
            '  .md-typeset p.glossary + p.glossary {\n'
            f'    margin-top: {spacing_european} !important;\n'
            '  }\n'
            '</style>'
        )

    @env.macro
    def nav_snippet():
        """Returns the current `nav = [...]` block from zensical.toml,
        verbatim, so the Navigation structure documentation always matches
        the real config instead of a hand-maintained example that drifts
        stale as nav changes. Usage: place inside a fenced code block:

            ```toml
            {{ nav_snippet() }}
            ```
        """
        return _get_nav_snippet()


