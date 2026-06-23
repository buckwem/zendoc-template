---
icon: lucide/book-open
---

<style>
  /* Reset the page and sidebar to start at 1 */
  .md-typeset { counter-reset: h1-count 0 !important; }
  .md-nav--primary { counter-reset: toc1 1 !important; }
</style>

# Start here

Documentation is easy to publish on a static website when using a docs-as-code workflow. [Markdown](https://www.markdownguide.org/){target=_blank} is a markup language used for writing documentation, which is then stored in a Git repository.. Hosted Git services such as GitLab or GitHub, together with tooling such as Visual Studio Code make it easy to maintain and host documentation.

Adopting a docs-as-code workflow transforms documentation from a chore into an engineering process. By treating your written content with the same rigour as code, you enable a collaborative approach to documentation.

## The docs-as-code philosophy

Docs-as-code means using the same tools and workflows for documentation as you do for software development. This creates a unified environment where writers and developers use the same tools and development workflow.

`Markdown as the Source of Truth`

: Markdown is a lightweight markup language that's simple to read in its raw form and consistently renders on the web. It's used for writing documentation for conversion into HTML for web publishing.

`Version control via Git`

: Storing files in a Git repository (GitHub, GitLab, or Bitbucket) enables the tracking of all changes. There will be a complete history of "who changed what and why," making it easy to revert errors and audit changes.

`Collaborative Reviews`

: Instead of emailing Word docs back and forth, teams use Pull Requests (PRs) or Merge Requests (MRs). This enables peer reviews, automated linting, and transparent discussions before any content goes live.

## The docs-as-code stack

To move from using a word processor or simple website to a scalable and effective documentation tool set needs a stack of tools:

`Authoring tool`

Effective documentation relies on tooling to edit content and automate quality checks for spelling, grammar, and consistent formatting. By using Visual Studio Code, writers can leverage a collection of extensions to provide real-time quality assurance. 

`Docs-as-code builder`



`Code Repository and Management`

This integrated environment is directly connected to a Git repository enabling the review and editing of content by other team members before publication.

!!! note "Why not LaTeX?"

    [LaTeX](https://www.latex-project.org){target=_blank} is a typesetting system widely used in academia and for specialised industrial documentation that requires precise formatting. Although it is not built specifically for web publishing, external tools can convert LaTeX source files into HTML for use on static websites. We are using Markdown as it's often preferred for general documentation in industry because it integrates more naturally with modern web-based development workflows.

## Docs-as-code in production

As a student, you will be following a simplified workflow, as you aren't working with documentation that spans thousands of pages. Nevertheless, understanding the approach used at scale can help you appreciate the skills you will develop. GitLab provides a video that outlines the entire process for their documentation and highlights the importance of the skills acquired through a docs-as-code methodology.

<iframe width="560" height="315" src="https://www.youtube.com/embed/ZlabtdA-gZE?si=_3GQjj5C6EDpMP8Z" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>


!!! warning

    Before releasing your document, comment out the 5 lines of the START HERE section in the zensical.toml file.

## Zensical for docs-as-code

Zensical provides the themes and tools necessary to draft professionaldocumentation in Markdown with instant local previews. Once finalised, you can publish your site by uploading the files to a Git repository. From there, automated pipelines build and deploy the content into a live website.

[Zensical](https://zensical.org/){target="_blank"}, written for speed and reliability using the [Rust programming language](https://rust-lang.org/){target="_blank"}, publishes this documentation in a website.

You will fork (clone) a documentation template into a project you can use to write your own document or report. To begin creating an environment for writing content to publish on your own static website, follow the instructions below.

!!! tip

    These instructions are composed in markdown format, which is processed by Zensical. To view the structure of Markdown files, go to the Git repository for the documentation located at the top right of this page. There, you will find markdown files that serve as examples for writing your documentation.

Start with installing the basic tools for writing your documentation using a Docs-as-code approach.
