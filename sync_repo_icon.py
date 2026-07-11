#!/usr/bin/env python3
# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""
Sync the [project] repo_url / repo_name and the [project.theme.icon] repo
icon in zensical.toml with the actual git remote this checkout is using, so
that forking/mirroring this template to GitHub, GitLab or Bitbucket doesn't
leave a stale repo link or the wrong brand icon behind.

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

# Host substring -> (FontAwesome brand icon, display label)
HOST_ICON_MAP = [
    ("github.com", "fontawesome/brands/github", "GitHub"),
    ("gitlab", "fontawesome/brands/gitlab", "GitLab"),
    ("bitbucket.org", "fontawesome/brands/bitbucket", "Bitbucket"),
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


def icon_for_host(host: str) -> tuple[str, str]:
    host_lower = host.lower()
    for needle, icon, label in HOST_ICON_MAP:
        if needle in host_lower:
            return icon, label
    return DEFAULT_ICON, host


def update_toml(text: str, repo_url: str, repo_name: str, icon: str) -> tuple[str, list[str]]:
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
    return text, changes


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

    icon, label = icon_for_host(host)
    repo_url = f"https://{host}/{owner}/{repo_name}"

    original = TOML_PATH.read_text()
    updated, changes = update_toml(original, repo_url, repo_name, icon)

    if not changes:
        print(f"zensical.toml already in sync with {label} remote ({repo_url})")
        return 0

    TOML_PATH.write_text(updated)
    print(f"Detected {label} remote ({repo_url}); updated: {', '.join(changes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
