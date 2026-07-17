---
icon: lucide/book-open
---

<!-- 
# Copyright (c) 2025-2026 Mark Buckwell and contributors
# SPDX-License-Identifier: MIT
-->

{{ heading_counter_reset(page) }}

# Start here

This is **prodockit-template**, a [Zensical](https://zensical.org/){target="_blank"} documentation-as-code template for academic coursework reports and assignments: write your report once in Markdown, and publish it as both a browsable website and a single-file PDF. It comes with automatic heading numbering, University of Surrey or generic branding, a word count and repository link on the cover page, and more.

For the full setup, authoring, customisation, and testing guide - installing tooling, editing and previewing locally, Markdown and Zensical basics, customising this template, and running its test suite - see the independent **[prodockit User Guide](https://buckwem.github.io/prodockit-userguide/){target="_blank"}**. It's hosted separately so it can be improved and kept current without every existing fork of this template being stuck with whatever it looked like the day they forked it.

!!! warning "Delete this page before you submit your report"
    This page is an author-facing pointer, not part of your report, so it needs to come out before you release it:

    1. In `zensical.toml`, comment out (or remove) the `"START HERE"` nav group.
    2. Delete `docs/starthere.md`.

    See [Finalising your document](https://buckwem.github.io/prodockit-userguide/customise/#finalising-your-document) in the User Guide for the full walkthrough, including why the order of those two steps matters.
