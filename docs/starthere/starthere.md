---
icon: lucide/book-open
---

<!-- 
# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT
-->

{{ heading_counter_reset(page) }}

# Start here

A docs-as-code workflow makes it easy to publish documentation on a static website. [Markdown](https://www.markdownguide.org/){target=_blank} is a markup language you use to write documentation in text files, which you then store in a Git repository. Hosted Git services such as GitLab or GitHub, together with tooling such as Visual Studio Code, make it easy to maintain and host documentation.

Adopting a docs-as-code workflow transforms documentation from a chore into an engineering process. By treating your written content with the same rigour as code, you enable a collaborative approach to documentation.

## The docs-as-code philosophy

Docs-as-code means using the same tools and workflows for documentation as you do for software development. This creates a unified environment where writers and developers use the same tools and development workflow.

`Markdown as the Source of Truth`

: [Markdown](https://www.markdownguide.org/){target=_blank} is a lightweight markup language that's simple to read in its raw form and consistently renders on the web. You write your documentation in it, then convert that documentation into HTML for web publishing.

`Version control via Git`

: Storing files in a Git repository (such as GitHub, GitLab, or Bitbucket) enables the tracking of all changes to the documentation. There will be a complete history of "who changed what and why," making it easy to undo errors and audit changes.

`Collaborative Reviews`

: Instead of emailing Word docs back and forth, teams use Pull Requests (PRs) or Merge Requests (MRs). This enables peer reviews, automated linting, and transparent discussions before any content goes live.

## The docs-as-code stack

To move from using a word processor or simple website to a scalable and effective documentation tool set needs a stack of tools:

`Authoring tool`

: Effective documentation depends on tools that help with content editing and automate quality checks, including spelling, grammar, style and formatting consistency. While there are numerous text editors available, Visual Studio Code stands out as a favoured option due to its extensive ecosystem of extensions. By using Visual Studio Code, writers can take advantage of a variety of extensions that offer real-time quality assurance. 

`Docs-as-code builder`

: Markdown files can serve as a foundation for a static website. However, they often need enhanced formatting options through additional themes and styling. A docs-as-code builder then transforms the Markdown and supplementary instructions into HTML, applying a theme to generate a professional-looking website. Zensical is a fast and reliable docs-as-code builder that processes Markdown files and creates a static documentation website. It lets you view the website locally before publishing, so you can confirm the final output meets your quality standards.

`Code Repository and Management`

: By connecting directly to a Git repository, this integrated environment establishes a secure, centralised vault that tracks the history of project files. It records each modification as a distinct commit, letting users audit changes or revert to earlier versions if errors arise. Before finalising any work, a pull request triggers a peer-review process, where collaborators comment on, test, and approve the updates. This workflow ensures that only vetted, high-quality content reaches final publication.

!!! note "Why not LaTeX?"

    [LaTeX](https://www.latex-project.org){target=_blank} is a typesetting system widely used in academia and for specialised industrial documentation that requires precise formatting. Although it is not built specifically for web publishing, external tools can convert LaTeX source files into HTML for use on static websites. We are using Markdown as it's often preferred for general documentation in industry because it integrates more naturally with modern web-based development workflows.

## Docs-as-code in production

As a student, you'll follow a simplified workflow, since you won't be handling documentation that spans thousands of pages and needs a large development team to maintain it. Nevertheless, understanding the approach used at scale can help you appreciate the value of the skills you'll develop. GitLab provides a video that outlines the entire process for their documentation and highlights the importance of the skills you gain through a docs-as-code methodology.

<div style="display: flex; justify-content: center;">
  <iframe width="560" height="315" src="https://www.youtube.com/embed/ZlabtdA-gZE?si=_3GQjj5C6EDpMP8Z" title="Introduction to using GitLab as a technical writing team Youtube video" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## Zensical for docs-as-code

Zensical provides the themes and tools necessary to draft professional documentation in Markdown with instant local previews. Once finalised, you can publish your site by uploading the files to a Git repository. From there, automated pipelines build and deploy the content into a live website.

[Zensical](https://zensical.org/){target="_blank"}, written for speed and reliability using the [Rust programming language](https://rust-lang.org/){target="_blank"}, publishes documentation in a website.

This documentation template is available for you to fork and clone into a project that you can use to write your own document or report - [Install tooling](./installtooling.md) covers exactly what those two steps mean and how to do them.

!!! tip

    Zensical processes these Markdown-formatted instructions into this site. To view the structure of Markdown files, go to the Git repository for the documentation located at the top right of this page. There, you will find markdown files that serve as examples for writing your documentation.

## Documentation structure

This document template's documentation covers the following sections, in the order you'll work through them.

`Install tooling`

: The [*Install tooling*](./installtooling.md) section describes how to install the core prerequisite tools and create a fork of the document template. By the end of this section you will have an environment ready to develop your own coursework or documentation. The instructions are available for macOS, Windows 11, and Ubuntu/Debian Linux.

`Start editing`

: The [*Start editing*](./startediting.md) section describes how to edit the documentation and view the changes locally before publishing to a Git repository. It also describes how to synchronise your changes with the Git repository.

`Markdown basics`

: The [*Markdown basics*](./markdown.md) section describes the principles of Markdown and how to use it to write your documentation.

`Zensical basics`

: The [*Zensical basics*](./zensicalbasics.md) section describes the principles of Zensical and how to use it to create and manage your documentation.

`Customise`

: The [*Customise*](./customise.md) section discusses how to configure this template to give it different style and layout to meet your specific needs.

`Additional tooling`

: The [*Additional tooling*](./additionaltooling.md) section describes additional tools you can install to help you create quality docs-as-code documents. They will take additional effort to install and configure.

`Shell commands`

: The [*Shell commands*](./shcommands.md) section describes the shell commands used in this documentation template. It's intended as a reference for you to use when writing your own documentation. Students in the past found these commands helpful.

Continue to the next section to get started with the installation of the core tools and creating a fork of this document template.