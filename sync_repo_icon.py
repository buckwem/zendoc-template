#!/usr/bin/env python3
# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""
Sync repo-hosting-specific metadata with the actual git remote this checkout
is using, so that forking/mirroring this template to GitHub, GitLab or
Bitbucket doesn't leave stale links, the wrong brand icon, or the wrong
README badges behind:

- [project] repo_url / repo_name and [project.theme.icon] repo in
  zensical.toml.
- The README badge row (Build / Stars / Forks) between the
  "repo-badges:start" / "repo-badges:end" markers - GitHub and GitLab each
  get badges pointing at their own APIs; other hosts are left as-is.

Run manually after changing the "origin" remote, or wire it into CI to run
before "zensical build".
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

TOML_PATH = Path(__file__).parent / "zensical.toml"
README_PATH = Path(__file__).parent / "README.md"
DEFAULT_BRANCH = "main"

# Host substring -> (kind, FontAwesome brand icon, display label)
HOST_ICON_MAP = [
    ("github.com", "github", "fontawesome/brands/github", "GitHub"),
    ("gitlab", "gitlab", "fontawesome/brands/gitlab", "GitLab"),
    ("bitbucket.org", "bitbucket", "fontawesome/brands/bitbucket", "Bitbucket"),
]
DEFAULT_ICON = "fontawesome/brands/git-alt"


def get_remote_url(remote: str = "origin") -> str:
    result = subprocess.run(
        ["git", "remote", "get-url", remote],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def parse_remote(url: str) -> tuple[str, str, str]:
    """Return (host, owner, repo_name) from an SSH or HTTPS git remote URL."""
    ssh_match = re.match(r"^[\w.-]+@(?P<host>[\w.-]+):(?P<path>.+)$", url)
    if ssh_match:
        host = ssh_match.group("host")
        path = ssh_match.group("path")
    else:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        path = parsed.path.lstrip("/")

    path = path.removesuffix(".git")
    parts = path.split("/")
    if len(parts) < 2:
        raise ValueError(f"Could not parse owner/repo from remote URL: {url!r}")
    owner, repo_name = parts[0], parts[-1]
    return host, owner, repo_name


def icon_for_host(host: str) -> tuple[str, str, str]:
    """Return (kind, icon, label) for a git remote host."""
    host_lower = host.lower()
    for needle, kind, icon, label in HOST_ICON_MAP:
        if needle in host_lower:
            return kind, icon, label
    return "other", DEFAULT_ICON, host


def edit_uri_for_host(kind: str, docs_dir: str) -> str | None:
    """Return the edit_uri to set for a given host kind, or None if the host
    isn't one this template knows how to link into (in which case edit_uri
    is left unset, and Zensical's "edit"/"view source" page buttons simply
    don't appear - the same as Zensical's own built-in behaviour for an
    unrecognised host).

    Zensical falls back to its own built-in default (f"edit/master/{docs_dir}")
    whenever edit_uri isn't set explicitly - hardcoding the "master" branch
    name regardless of the repo's actual default branch, and only for an
    exact "github.com"/"gitlab.com" host match (so a self-hosted GitLab
    instance like Surrey's gets no default at all). This sets edit_uri
    explicitly instead, using DEFAULT_BRANCH and matching by host kind (see
    icon_for_host()) so a self-hosted GitLab instance is covered too - see
    issue #40."""
    if kind in ("github", "gitlab"):
        return f"edit/{DEFAULT_BRANCH}/{docs_dir.strip('/')}/"
    return None


def update_toml(text: str, repo_url: str, repo_name: str, icon: str, edit_uri: str | None) -> tuple[str, list[str]]:
    changes = []

    def replace_once(pattern: str, replacement: str, label: str, src: str) -> str:
        new_src, count = re.subn(pattern, replacement, src, count=1, flags=re.MULTILINE)
        if count == 0:
            raise ValueError(f"Could not find {label} in zensical.toml")
        if new_src != src:
            changes.append(label)
        return new_src

    text = replace_once(
        r'^repo_url = ".*"$',
        f'repo_url = "{repo_url}"',
        "repo_url",
        text,
    )
    text = replace_once(
        r'^repo_name = ".*"$',
        f'repo_name = "{repo_name}"',
        "repo_name",
        text,
    )
    text = replace_once(
        r'^repo = ".*"$',
        f'repo = "{icon}"',
        "theme.icon.repo",
        text,
    )

    if edit_uri is not None:
        edit_uri_line = f'edit_uri = "{edit_uri}"'
        if re.search(r'^edit_uri = ".*"$', text, flags=re.MULTILINE):
            text = replace_once(r'^edit_uri = ".*"$', edit_uri_line, "edit_uri", text)
        else:
            # First run on a checkout that predates this setting - insert it
            # right after repo_name rather than requiring it to already exist.
            new_text, count = re.subn(
                r'^(repo_name = ".*")$',
                r'\1\n' + edit_uri_line,
                text,
                count=1,
                flags=re.MULTILINE,
            )
            if count == 0:
                raise ValueError("Could not find repo_name to insert edit_uri after in zensical.toml")
            if new_text != text:
                changes.append("edit_uri")
            text = new_text

    return text, changes


def badges_for_host(kind: str, owner: str, repo_name: str) -> str | None:
    """Return the README badge-row markup for a given host kind, or None if
    the host has no known badge set (left untouched in that case)."""
    if kind == "github":
        return (
            f'<p align="center">\n'
            f'  <a href="https://github.com/{owner}/{repo_name}/actions"><img\n'
            f'    src="https://github.com/{owner}/{repo_name}/actions/workflows/docs.yml/badge.svg"\n'
            f'    alt="Build"\n'
            f'  /></a>\n'
            f'  <a href="https://github.com/{owner}/{repo_name}/stargazers"><img\n'
            f'    src="https://img.shields.io/github/stars/{owner}/{repo_name}?style=flat&logo=github&label=Stars"\n'
            f'    alt="GitHub Stars"\n'
            f'  /></a>\n'
            f'  <a href="https://github.com/{owner}/{repo_name}/forks"><img\n'
            f'    src="https://img.shields.io/github/forks/{owner}/{repo_name}?style=flat&logo=github&label=Forks"\n'
            f'    alt="GitHub Forks"\n'
            f'  /></a>\n'
            f"</p>"
        )
    if kind == "gitlab":
        path = f"{owner}/{repo_name}"
        encoded = f"{owner}%2F{repo_name}"
        return (
            f'<p align="center">\n'
            f'  <a href="https://gitlab.com/{path}/-/pipelines"><img\n'
            f'    src="https://img.shields.io/gitlab/pipeline-status/{encoded}?branch={DEFAULT_BRANCH}&label=Build"\n'
            f'    alt="Build"\n'
            f'  /></a>\n'
            f'  <a href="https://gitlab.com/{path}"><img\n'
            f'    src="https://img.shields.io/gitlab/stars/{encoded}?style=flat&logo=gitlab&label=Stars"\n'
            f'    alt="GitLab Stars"\n'
            f'  /></a>\n'
            f'  <a href="https://gitlab.com/{path}/-/forks"><img\n'
            f'    src="https://img.shields.io/gitlab/forks/{encoded}?style=flat&logo=gitlab&label=Forks"\n'
            f'    alt="GitLab Forks"\n'
            f'  /></a>\n'
            f"</p>"
        )
    return None


def update_readme(text: str, badges: str) -> tuple[str, bool]:
    pattern = re.compile(
        r"(<!-- repo-badges:start.*?-->\n).*?(\n<!-- repo-badges:end -->)",
        re.DOTALL,
    )
    if not pattern.search(text):
        raise ValueError("Could not find repo-badges markers in README.md")
    new_text, count = pattern.subn(rf"\1{badges}\2", text)
    return new_text, new_text != text


def main() -> int:
    try:
        remote_url = get_remote_url()
    except subprocess.CalledProcessError:
        print("error: no 'origin' git remote configured", file=sys.stderr)
        return 1

    try:
        host, owner, repo_name = parse_remote(remote_url)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    kind, icon, label = icon_for_host(host)
    repo_url = f"https://{host}/{owner}/{repo_name}"

    original_toml = TOML_PATH.read_text()
    docs_dir_match = re.search(r'^docs_dir\s*=\s*"([^"]*)"', original_toml, re.MULTILINE)
    docs_dir = docs_dir_match.group(1) if docs_dir_match else "docs"
    edit_uri = edit_uri_for_host(kind, docs_dir)
    updated_toml, changes = update_toml(original_toml, repo_url, repo_name, icon, edit_uri)
    if changes:
        TOML_PATH.write_text(updated_toml)

    badges = badges_for_host(kind, owner, repo_name)
    readme_changed = False
    if badges is not None:
        original_readme = README_PATH.read_text()
        updated_readme, readme_changed = update_readme(original_readme, badges)
        if readme_changed:
            README_PATH.write_text(updated_readme)
            changes.append("README badges")
    else:
        print(f"note: no known README badge set for {label}; README left unchanged")

    if not changes:
        print(f"zensical.toml and README.md already in sync with {label} remote ({repo_url})")
        return 0

    print(f"Detected {label} remote ({repo_url}); updated: {', '.join(changes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
