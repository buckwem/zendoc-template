---
icon: lucide/book-open
---

<!-- 
# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT
# All contributions are certified under the DCO
-->

<style>
  /* Reset the page and sidebar to start at 1 */
  .md-typeset { counter-reset: h1-count 0 !important; }
  .md-nav--primary { counter-reset: toc1 1 !important; }
  /* Also change the numbering of the overall title number in the sidebar by editing zensical.toml */
</style>

# Start here

Documentation is easy to publish on a static website when using a docs-as-code workflow. [Markdown](https://www.markdownguide.org/){target=_blank} is a markup language used for writing documentation in text files that are then stored in a Git repository. Hosted Git services such as GitLab or GitHub, together with tooling such as Visual Studio Code make it easy to maintain and host documentation.

Adopting a docs-as-code workflow transforms documentation from a chore into an engineering process. By treating your written content with the same rigour as code, you enable a collaborative approach to documentation.

## The docs-as-code philosophy

Docs-as-code means using the same tools and workflows for documentation as you do for software development. This creates a unified environment where writers and developers use the same tools and development workflow.

`Markdown as the Source of Truth`

: [Markdown](https://www.markdownguide.org/){target=_blank} is a lightweight markup language that's simple to read in its raw form and consistently renders on the web. It's used for writing documentation for conversion into HTML for web publishing.

`Version control via Git`

: Storing files in a Git repository (such as GitHub, GitLab, or Bitbucket) enables the tracking of all changes to the documentation. There will be a complete history of "who changed what and why," making it easy to undo errors and audit changes.

`Collaborative Reviews`

: Instead of emailing Word docs back and forth, teams use Pull Requests (PRs) or Merge Requests (MRs). This enables peer reviews, automated linting, and transparent discussions before any content goes live.

## The docs-as-code stack

To move from using a word processor or simple website to a scalable and effective documentation tool set needs a stack of tools:

`Authoring tool`

Effective documentation depends on tools that help with content editing and automate quality checks, including spelling, grammar, style and formatting consistency. While there are numerous text editors available, Visual Studio Code stands out as a favoured option due to its extensive ecosystem of extensions. By using Visual Studio Code, writers can take advantage of a variety of extensions that offer real-time quality assurance. 

`Docs-as-code builder`

Markdown files can serve as a foundation for a static website. However, they often require enhanced formatting options through additional themes and styling. A docs-as-code builder then transforms the Markdown and supplementary instructions into HTML, applying a theme to generate a professional-looking website. Zensical is a fast and reliable docs-as-code builder designed to process Markdown files and create a static documentation website. It enables the website to be viewed locally before publishing, ensuring that the final output meets quality standards.

`Code Repository and Management`

By connecting directly to a Git repository, this integrated environment establishes a secure, centralised vault that tracks the history of project files. Each modification is recorded as a distinct commit, enabling users to audit changes or revert to earlier versions if errors arise. Prior to finalising any work, a pull request prompts a peer-review process that allows collaborators to comment on, test, and approve the updates. This workflow ensures that only vetted, high-quality content is prepared for final publication.

!!! note "Why not LaTeX?"

    [LaTeX](https://www.latex-project.org){target=_blank} is a typesetting system widely used in academia and for specialised industrial documentation that requires precise formatting. Although it is not built specifically for web publishing, external tools can convert LaTeX source files into HTML for use on static websites. We are using Markdown as it's often preferred for general documentation in industry because it integrates more naturally with modern web-based development workflows.

## Docs-as-code in production

As a student, you will be following a simplified workflow, as you aren't working with documentation that spans thousands of pages and is maintained by a large development team. Nevertheless, understanding the approach used at scale can help you appreciate the value of the skills you will develop. GitLab provides a video that outlines the entire process for their documentation and highlights the importance of the skills acquired through a docs-as-code methodology.

<div style="display: flex; justify-content: center;">
  <iframe width="560" height="315" src="https://www.youtube.com/embed/ZlabtdA-gZE?si=_3GQjj5C6EDpMP8Z" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## Zensical for docs-as-code

Zensical provides the themes and tools necessary to draft professionaldocumentation in Markdown with instant local previews. Once finalised, you can publish your site by uploading the files to a Git repository. From there, automated pipelines build and deploy the content into a live website.

[Zensical](https://zensical.org/){target="_blank"}, written for speed and reliability using the [Rust programming language](https://rust-lang.org/){target="_blank"}, publishes documentation in a website.

This documentation template is available for you to fork (clone) into a project that you can use to write your own document or report.

!!! tip

    These instructions are composed in markdown format, which is processed by Zensical. To view the structure of Markdown files, go to the Git repository for the documentation located at the top right of this page. There, you will find markdown files that serve as examples for writing your documentation.

## Documentation structure

The documentation for this document template has been split into a number of sections.

`Install core`

The *Install core* section describes how to install the core prerequisite tools and create a fork of the document tamplate. By the end of this section you will have an environment ready to develop your own coursework or documentation. The instructions are available for masOS, Windows 11 and Ubuntu/Debian Linux.

`Install extensions`

The *Install extensions' section describes additional tools that can be installed to help you create quality docs-as-code documents. They will take additional effort to install and configure.

`Customeise`

The 'Customise' section discusses how to configure this template to give it different style and layout to meet your specific needs.

`Markdown basics`

The *Markdown basics* section describes the principles of Markdown and how to use it to write your documentation.

`Zensical basics`

The *Zensical basics* section describes the principles of Zensical and how to use it to create and manage your documentation.

`Shell commands`

The *Shell commands* section describes the shell commands used in this documentation template. It's intended as a reference for you to use when writing your own documentation. Students in the past found these commands helpful.

<br>Continue to the next section to get started with the installation of the core tools and creating a fork of this document template.