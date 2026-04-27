---
icon: lucide/book-open
---

<style>
  /* This page starts at 1 */
  .md-typeset {
    counter-reset: h1-count 0 !important; 
  }

  /* This specific page sidebar starts at 1 */
  .md-nav--primary {
    counter-reset: toc1 1 !important;
  }
</style>

# Start Here

Documentation is easy to publish on a static website when using a docs-as-code workflow. Documents are written using Markdown and stored in a Git repository. Hosted Git services such as GitLab or GitHub, together with tooling such as Visual Studio Code make it easy to maintain and host documentation.

Adopting a docs-as-code workflow transforms documentation from a chore into an engineering process. By treating your written content with the same rigour as code, you enable a collaborative approach to documentation.

## The Docs-as-Code Philosophy

Docs-as-code means using the same tools and workflows for documentation as you do for software development. This creates a unified environment where writers and developers use the same tools and development workflow.

`Markdown as the Source of Truth`

: Documents are authored in [Markdown](https://www.markdownguide.org/){target=_blank}, a lightweight markup language that is easy to read in its raw form and renders consistently on the web.

`Version control via Git`

: By storing files in a Git repository (GitHub, GitLab, or Bitbucket), every change is tracked. There will be a complete history of "who changed what and why," making it easy to revert errors and audit changes.

`Collaborative Reviews`

: Instead of emailing Word docs back and forth, teams use Pull Requests (PRs) or Merge Requests (MRs). This allows for peer reviews, automated linting, and transparent discussions before any content goes live.

## The Docs-as-Code Stack

To move from using a word processor or simple website to a scalable and effective documentation tool set needs a stack of tools:

`Authoring tool`

Effective documentation relies on tooling to edit content and automate quality checks for spelling, grammar, and consistent formatting. By using Visual Studio Code, writers can leverage a collection of extensions to provide real-time quality assurance. 

`Docs-as-code builder`



`Code Repository and Management`

This integrated environment connects directly to a Git repository, ensuring that all content is polished and professionally vetted before it ever goes live.

!!! note "Why not LaTeX?"

    [LaTeX](https://www.latex-project.org){target=_blank} is a typesetting system widely used in academia and for specialised industrial documentation that requires precise formatting. Although it is not built specifically for web publishing, external tools can convert LaTeX source files into HTML for use on static websites. We are using Markdown as it's often preferred for general documentation in industry because it integrates more naturally with modern web-based development workflows.

## Docs-as-Code in Production

As a student, you will be following a simplified workflow, as you are not working with documentation that spans thousands of pages. Nevertheless, understanding the approach used at scale can help you appreciate the skills you will develop. GitLab provides a video that outlines the entire process for their documentation and highlights the importance of the skills acquired through a docs-as-code methodology.

<iframe width="560" height="315" src="https://www.youtube.com/embed/ZlabtdA-gZE?si=_3GQjj5C6EDpMP8Z" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>


!!! warning

    Before releasing your document, comment out the 5 lines of the START HERE section in the zensical.toml file.

## Zensical for Docs-as-code

Zensical provides the themes and tools necessary to draft documentation in Markdown with instant local previews. Once finalised, you can publish your site by uploading the files to the university GitLab; from there, automated pipelines build and deploy your content into a live website.

[Zensical](https://zensical.org/){target="_blank"}, written for speed and reliability using the [Rust programming language](https://rust-lang.org/){target="_blank"}. This website is written using Zensical.

To make it easy for you, a documentation template has been created that you will fork (clone) into a project you can use to develop your own document or report. Follow the instructions below to get started creating an environment to write the content to publish on your own static website.

!!! tip

    These instructions are composed in markdown format, which is processed by Zensical. To view the structure of Markdown files, go to the Git repository for the documentation located at the top right of this page. There, you will find markdown files that serve as examples for writing your documentation.

Let's start with installing the basic tools for writing your documentation using a Docs-as-code approach.
