<!--
# Copyright (c) 2025-2026 Mark Buckwell and contributors
# SPDX-License-Identifier: MIT
-->

# Contributing

Thanks for your interest in improving zendoc-template. This guide covers contributing to the template itself - fixing bugs, adding features, or improving the documentation-as-code tooling. If you're a student using the template to write your own assignment, you don't need any of this: just fork the repo and follow the [Start Here](docs/starthere/starthere.md) section.

## Before you start

For anything beyond a small fix (typos, broken links), please open an issue first to discuss the change. This avoids duplicated effort and lets us agree on the approach before you spend time on an implementation.

## Getting set up

1. Fork the repository and clone your fork.
2. Install the Python prerequisites: `pip install -r requirements.txt`.
3. Preview the site locally: `zensical serve`.
4. If your change touches PDF generation, Mermaid diagrams, or MathJax equations, also install the Node tooling (`npm ci` in `tools/mermaid/` and `tools/mathjax/`) and build the PDF with `python build_pdf.py`. See [Install tooling](docs/starthere/installtooling.md) for the full setup.

## Making a change

1. Create a branch off `main` for your change.
2. Make your change and verify it locally:
   - Website changes: `zensical serve` and check the page in a browser.
   - PDF-affecting changes (`build_pdf.py`, `macros.py`, `docs/stylesheets/print.css`): run `python build_pdf.py` and check `docs/site_documentation.pdf`.
   - Prose changes: optionally run `vale docs/` if you have [Vale](https://vale.sh/) installed (see [Additional tooling](docs/starthere/additionaltooling.md#install-vale-to-check-for-grammar-spelling-and-style-issues)); it's not enforced in CI.
   - Run the test suite (see below) - it checks the built website and PDF for regressions in this template's own prodockit-specific features (numbering, word count, links, and so on), and runs in CI on every push.
3. Open a pull request against `main`. `main` is protected, so all changes - including from maintainers - go through a PR.
4. Reference the issue your PR addresses (e.g. `Fixes #123`) where applicable.

## Running the test suite

The test suite in `test/` checks the *built output*, not the build process itself - build the website and PDF first, then run the tests against them:

```bash
pip install -r requirements.txt -r testrequirements.txt
python build_pdf.py
zensical build
python test/run_tests.py
```

Tests are grouped into batches (`build`, `captions`, `content`, `fences`, `links`, `numbering`, `pdf_structure`, `word_count`), each reporting its own pass/fail. Run `python test/run_tests.py --list` to see them, and `python test/run_tests.py --batch <name>` to run just one - useful when you're actively working on a specific capability and don't want to wait on the rest of the suite. Extra arguments after the batch options are passed straight through to `pytest`. See [Testing](docs/starthere/testing.md) for the full guide.

## Reporting bugs and requesting features

Please use the issue templates when opening an issue - they help make sure we get the information needed to act on it.

## License

By contributing, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
