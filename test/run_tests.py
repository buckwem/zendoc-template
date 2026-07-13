#!/usr/bin/env python3
# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT

"""CLI runner for the test suite (see issue #44). Each test_<name>.py file
is a "batch" - build, captions, content, fences, links, markdown_foundations,
numbering, pdf_structure, word_count - run individually or all together,
each reporting its own pass/fail.

Run the builds first - these tests check the *built* output, they don't
build it themselves:

    python sync_repo_icon.py   # only needed after changing the git remote
    python build_pdf.py
    zensical build

Usage:
    python test/run_tests.py                  # run every batch
    python test/run_tests.py --batch links     # run just the "links" batch
    python test/run_tests.py --list            # list available batches
    python test/run_tests.py -- -k caption     # extra args passed to pytest
"""

import argparse
import sys
from pathlib import Path

import pytest

TEST_DIR = Path(__file__).resolve().parent


def available_batches():
    return sorted(p.stem.removeprefix("test_") for p in TEST_DIR.glob("test_*.py"))


def run_batch(batch_name, pytest_args):
    target = str(TEST_DIR / f"test_{batch_name}.py")
    print(f"\n{'=' * 70}\nBatch: {batch_name}\n{'=' * 70}")
    return pytest.main(["-v", target, *pytest_args]) == 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the zendoc-template test suite.")
    parser.add_argument("--batch", help="Run only this batch (see --list for names)")
    parser.add_argument("--list", action="store_true", help="List available batches and exit")
    parser.add_argument("pytest_args", nargs="*", help="Extra arguments passed through to pytest")
    args = parser.parse_args(argv)

    batches = available_batches()
    if args.list:
        print("\n".join(batches))
        return 0

    if args.batch:
        if args.batch not in batches:
            print(f"Unknown batch '{args.batch}'. Available: {', '.join(batches)}", file=sys.stderr)
            return 2
        return 0 if run_batch(args.batch, args.pytest_args) else 1

    results = {batch: run_batch(batch, args.pytest_args) for batch in batches}

    print(f"\n{'=' * 70}\nSummary\n{'=' * 70}")
    for batch, ok in results.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {batch}")

    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
