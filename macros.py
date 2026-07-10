import os
import re
from bs4 import BeautifulSoup
import subprocess
import shutil
from pathlib import Path
import toml

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


def _compute_site_word_count():
    """Sums the prose word count across every nav page except the cover
    (index.md), for the optional {{ word_count }} variable - see the
    "Word count" section in customise.md for how to show or hide it.
    Returns a comma-formatted string (e.g. "9,971") ready to drop straight
    into a page with {{ word_count }}."""
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
        total += _count_words_in_markdown(docs_dir / rel_path)
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
    no git remote configured (e.g. the template hasn't been cloned yet)."""
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
        return re.sub(r'\.git$', '', remote_url)
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


def _heading_start_counts():
    """Maps each nav markdown file (relative to docs_dir) to the cumulative count of
    top-level headings on every page before it in nav order, so that heading numbering
    can continue seamlessly from one page to the next, the same way it does in the PDF."""
    config_path = Path('zensical.toml')
    if not config_path.exists():
        return {}
    config = toml.load(config_path)
    project = config.get('project', {}) if isinstance(config.get('project'), dict) else {}
    nav = project.get('nav') or config.get('nav') or []
    docs_dir = Path(config.get('docs_dir', 'docs'))

    starts = {}
    running_total = 0
    for rel_path in _extract_nav_md_files(nav):
        starts[rel_path] = running_total
        running_total += _count_top_level_headings(docs_dir / rel_path)
    return starts


def define_env(env):
    # ==========================================
    # 1. SURREY ENVIRONMENT DETECTION LOGIC
    # ==========================================
    target_domain = 'surrey.ac.uk'

    # Check 1: GitLab CI/CD Pipeline environment
    is_surrey_ci = os.getenv('CI_SERVER_HOST') == target_domain
    
    # Check 2: Local Git Remote Origin (Perfect for local 'zensical serve' testing)
    is_surrey_local_git = False
    try:
        # Automatically asks your local folder where its remote points
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"], 
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        if target_domain in remote_url:
            is_surrey_local_git = True
    except Exception:
        # Fails silently if git isn't installed or initialized in this directory
        pass

    # Check 3: Brute-force string scan of Zensical's entire config scope
    is_surrey_in_config = False
    if hasattr(env, 'config'):
        is_surrey_in_config = target_domain in str(env.config)
    if not is_surrey_in_config and hasattr(env, 'variables'):
        is_surrey_in_config = target_domain in str(env.variables)

    # Combine all checks: If ANY layer detects the domain, set to True
    final_result = is_surrey_ci or is_surrey_local_git or is_surrey_in_config
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

    # ==========================================
    # 3. CUSTOM MACROS
    # ==========================================
    @env.macro
    def copy_file(source: str, destination: str):
        """Copies a resource to the specified destination path during build time.
        Useful for including images, PDFs, or other assets in your documentation.
        or to override default assets in the template (like logos or favicons)."""
        src_path = Path(source)
        dest_path = Path(destination)
        
        if not src_path.exists():
            return f"**Macro Error:** Source file `{source}` not found."
            
        # Automatically make parent directories if they don't exist yet
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the file (shutil.copy2 preserves metadata)
        shutil.copy2(src_path, dest_path)
        
        # Return a silent HTML comment so it doesn't print text on your page
        return f""

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
        numbering off entirely (content and sidebar) across the whole site."""
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
                '</style>'
            )
        starts = _heading_start_counts()
        n = starts.get(getattr(page, 'path', ''), 0)
        return (
            '<style>\n'
            f'  .md-typeset {{ counter-reset: h1-count {n} !important; }}\n'
            f'  .md-nav--primary {{ counter-reset: toc1 {n + 1} !important; }}\n'
            '</style>'
        )


