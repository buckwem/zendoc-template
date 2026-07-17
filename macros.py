# Copyright (c) 2025-2026 Mark Buckwell and contributors
# SPDX-License-Identifier: MIT

"""This project's own Zensical macros - institution branding (Surrey vs.
default). Everything else a professional/academic report commonly needs
(word count, repo URL, site name, chapter/appendix numbering,
reference/acronym/glossary spacing) comes from prodockit.zensical_macros
instead (see prodockit-extensions#96, formerly zendoc-extensions#96 before
#16's rename) - not duplicated here.

prodockit.zensical_macros.define_env() is called directly below rather than
via zensical.toml's documented `modules = [...]` extension option: that
option makes Zensical also watch the module's file for auto-reload, and if
the module lives outside the project directory (true for any pip-installed
package, e.g. in CI where dependencies install outside the checkout) that
watch triggers an upstream panic in `zensical build`'s file watcher
(zensical/zensical#823). Calling it as a plain import instead
gives identical behaviour without that second watch registration - remove
this workaround and switch back to `modules = [...]` in zensical.toml once
that's fixed upstream."""

import os
import shutil
import subprocess
from pathlib import Path

from prodockit.zensical_macros import define_env as _prodockit_define_env


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
    _prodockit_define_env(env)

    # ==========================================
    # 1. SURREY ENVIRONMENT DETECTION LOGIC
    # ==========================================
    final_result = _detect_is_surrey(env)
    # final_result = False  # This line is for testing purposes; remove it in production to enable the macro.

    # Bind the variable to your markdown files
    env.variables['is_surrey'] = final_result

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
