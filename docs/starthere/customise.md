---
icon: lucide/book-open
---

<!-- 
# Copyright (c) 2025-2026 Mark Buckwell and contributors
# SPDX-License-Identifier: MIT
# All contributions are certified under the DCO
-->

{{ heading_counter_reset(page) }}

# Customising


## Directory structure

As a starting point, the documentation template has the following directory structure:

* :material-folder: **docs/** — Holds the documentation source tree.
    * :material-file-document-outline: `index.md` — The cover page of your documentation.
    * :material-file-document-outline: `originality.md` — Your declaration of originality and AI use for you to complete.
    * :material-file-document-outline: `section1.md` — The first section of your documentation for you to edit.
    * :material-file-document-outline: `section2.md` — The second section of your documentation for you to edit.
    * :material-file-document-outline: `section3.md` — The third section of your documentation for you to edit.
    * :material-file-document-outline: `section4.md` — The fourth section of your documentation for you to edit.
    * :material-folder: **starthere/** — Contains the "Start Here" section that can be deleted once you are familiar with the template.
        * :material-folder: **images/** — Contains images used in the "Start Here" section.
        * :material-file-document-outline: `starthere.md` — Introduction to the "Start Here" section.
        * :material-file-document-outline: `installation.md` — Instructions for installing the required tools.
        * :material-file-document-outline: `customising.md` — Guide for customising the documentation template.
        * :material-file-document-outline: `markdown.md` — Principles of Markdown for writing documentation.
        * :material-file-document-outline: `zensicalbasics.md` — Basics of using Zensical for documentation.
        * :material-file-document-outline: `shcommands.md` — Reference for shell commands used in the documentation.
* :material-folder: **src/** — Contains the core application logic.
* :material-file-cog-outline: `zensical.toml` — The project's configuration file.
* :material-file-document-outline: `.vale.ini` — Configuration file for Vale, a syntax and style checker.
* :material-file-document-outline: `requirements.txt` — Lists the Python dependencies required for the project.
* :material-file-document-outline: `README.md` — The README file for the project, providing an overview and instructions.
* :material-file-document-outline: `LICENSE.md` — The license file for the project in Markdown format, specifying the terms under which the project can be used and distributed. We've used the MIT license for the project used by Zensical. It's a permissive free software license that allows for reuse within proprietary software provided all copies of the licensed software include a copy of the MIT License terms and the copyright notice.
* :material-file-document-outline: `.gitignore` — Specifies files and directories to be ignored by Git version control.
* :material-file-document-outline: `.gitlab-ci.yml` — Configuration file for GitLab CI/CD, defining the pipeline for continuous integration and deployment.
* :material-folder: `.gitlab/` — Directory containing GitLab-specific configuration files.
    * :material-file-document-outline: `README.md` — README file for the GitLab configuration, providing details about the CI/CD setup.






## Changing the site logo

If the documentation website is part of the university's GitLab service or the location of the website is hosted under the University of Surrey domain, the site logo is automatically changed to the University of Surrey logo. Otherwise, the site logo will use the default logos in the `docs/assets/` directory. You can change the default logo by replacing the existing default logo files with your own logo files named `logo_default_black.png` and `logo_default_white.png`.

## Changing heading numbering

By default, heading numbering is enabled in the documentation template. If you want to disable heading numbering, you can do so by adding the following line to the `[project.extra]` section of the `zensical.toml` file:

```toml
heading_numbering = false
```

This will also disable heading numbering in the generated PDF output. If you want to enable heading numbering again, simply set the value to `true`:

```toml
heading_numbering = true
```

The top level heading numbering on the left menu is set through the explicit heading under nav in the zensical.toml file. If you want to change the top level heading numbering, you can do so by changing the heading under nav in the zensical.toml file. For example, if you want to change the top level heading numbering to "Chapter 1", you can do so by changing the heading under nav in the zensical.toml file to:

```toml
[[project.nav]]
heading = "Chapter 1"
```

!!! warning
    Only one heading 1 per markdown file is permitted. If you need to add a heading 1, please create a new markdown file and add the heading 1 there. This is to ensure that the document structure is maintained correctly and that the table of contents is generated accurately.


## Finalising your document

Before you release your document, please ensure that you have completed the following steps:
1. Comment out the 5 lines of the START HERE section in the zensical.toml file. This is to ensure that the START HERE section isn't included in the final output of your document.
1. Remove the Warning box on the Originality page as this isn't part of your document. You can do this by deleting the first Warning admonition box in the `originality.md` file.
