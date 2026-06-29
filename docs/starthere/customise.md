---
icon: lucide/book-open
---

<!-- 
# Copyright (c) 2025-2026 Mark Buckwell and contributors
# SPDX-License-Identifier: MIT
# All contributions are certified under the DCO
-->

<style>
  /* Reset the page and sidebar to start at 6  */
  .md-typeset { counter-reset: h1-count 5 !important; }
  .md-nav--primary { counter-reset: toc1 6 !important; }
  /* Also change the numbering of the overall title number in the sidebar by editing zensical.toml */
</style>

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








!!! warning

    Before releasing your document, comment out the 5 lines of the START HERE section in the zensical.toml file.
