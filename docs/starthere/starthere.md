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

Let's start with installing the basic tools for using 

## Setup the prerequisites

We suggest you use Visual Studio Code with appropriate plugins to edit your static website. Complete the following steps.

1. Register for the Surrey GitLab instance at [https://gitlab.surrey.ac.uk](https://gitlab.surrey.ac.uk)
1. Start with installing [Visual Studio Code](https://code.visualstudio.com){target="_blank"}. Instructions for macOS and Windows 11 are below:

    === "macOS - Standard"

        1. Download the macOS universal zip file from the [official website](https://code.visualstudio.com/).
        2. Open the downloaded `.zip` file to extract the application.
        3. Drag the **Visual Studio Code.app** into your **Applications** folder.

    === "macOS - Homebrew"

        If you use the Homebrew package manager, run this command in your Terminal:
        ``` bash
        brew install --cask visual-studio-code
        ```

    === "Windows 11 - PowerShell"

        Open up a **PowerShell** window and install **Visual Studio Code** using the command:
        ```PowerShell
        winget install Microsoft.VisualStudioCode
        ```

2. You will be using the university **GitLab** service at [https://gitlab.surrey.ac.uk] to store your code. The `git` command is used to communicate with **GitLab**.  macOS usually comes with the `git` command installed, but it might be an outdated version. For Windows 11, you will need to install`git`. Follow the instructions below to update or install it.

    === "macOS - Standard"

        Open the **Terminal** application and run the command `xcode-select --install`

    === "macOS - Homebrew"

        If you use the Homebrew package manager, run this command in your Terminal:
        ``` bash
        brew install git
        ```

    === "Windows 11 - PowerShell"

        Open up a **PowerShell** window and install `git` using the command:
        ```PowerShell
        winget install Git.Git
        ```

3. Install [markdownlint](https://marketplace.visualstudio.com/items?itemName=DavidAnson.vscode-markdownlint){target="_blank"} plugin for Visual Studio Code. This is designed to check your markdown files against a library of rules to encourage standards and consistency.
4. Install [Even Better TOML](https://marketplace.visualstudio.com/items?itemName=tamasfe.even-better-toml){target="_blank"} plugin for Visual Studio Code. This extension help manage a TOML file.
5. Install [LTeX+ – LanguageTool grammar/spell checking](https://marketplace.visualstudio.com/items?itemName=ltex-plus.vscode-ltex-plus){target="_blank"} to enable spelling and grammar checking for Markdown. Configure the plugin in the setting to use the *language* `en-GB`.
6. Install [GitLab](https://marketplace.visualstudio.com/items?itemName=GitLab.gitlab-workflow){target="_blank"} plugin in Visual Studio Code. This will enable you manage your documentation in GitLab.
7. Now let's configure the *GitLab* plugin to use an OAuth login.

    1. Open the Command Palette:
        1. For macOS, press Command+Shift+P.
        1. For Windows or Linux, press Control+Shift+P.
    1. Type `Preferences: Open User Settings` and press `Enter`.
    1. Select **Settings > Extensions > GitLab > Authentication**.
    1. Under **OAuth Client IDs**, select **Add Item**.
    1. Select **Key** and enter the GitLab instance URL [https://gitlab.surrey.ac.uk](https://gitlab.surrey.ac.uk).
    1. Select **Value** and enter your university ID for the OAuth application. e.g. `aa0101`.

## Initialise your repository

1. Create a directory for all your GitLab projects on your local desktop. For example, create a directory called 'GitLab' on your OneDrive. Using OneDrive will give you another backup of your GitLab repository.
2. [Fork a copy of the documentation template](https://gitlab.surrey.ac.uk/mb0105/doc-template/-/forks/new){target="_blank"} to create a copy of the template for your use.
3. Enter the *Project name* using to the format the coursework specifies. For example, for Coursework 1 for the module COMM058 in the year 2026, enter 'comm058-coursework1-2026'. Use all lowercase and a dash between words with no spaces. This will be used to create the project URL.
4. Select your personal namespace for the project URL.
5. Change the *Visibility Level* to *Private*.
6. Press the button [Fork Project] to create your own copy of the project.

    !!! Warning
        Don't forget to set the visibility to private, otherwise other students can see your coursework. Ask another student to check whether they can see your site. We will discuss how to view it later in the instructions.

## Download repository locally

1. Next we need to download and copy the project into Visual Studio Code so you can work with it locally. Select the [Code v] button and a menu will come up. Select the HTTPS button to the right of Visual Studio Code.
2. A browser popup will appear saying 'Open Visual Studio Code?' and you push the [Open Visual Studio Code] button.
3. This will open a directory selection box. Go to the 'GitLab' directory you selected earlier and press the [Select as Repository Destination]. This will then download the code to a subdirectory with the name of the project you created earlier.

    <figure markdown="span">
      <img src="../images/directory-selection.png" style="width: 70%;">
      <figcaption>Directory selection</figcaption>
    </figure>

4. Then you will be prompted to open your repository that is stored in your 'GitLab' directory. If you already have Visual Studio Code, you may wish to select [Open in a new window] so it creates a separate window to your current workspace.

    <figure markdown="span">
      <img src="../images/open-repository.png" style="width: 40%;">
      <figcaption>Open repository</figcaption>
    </figure>

## Viewing local website

The great feature of Zensical is that you view the changes to the website locally using a locally hosted website without sending the source to GitLab,

1. Start with installing python and any other software extensions that are required. Use the instructions for pip [here](https://zensical.org/docs/get-started/#install-with-pip){target="_blank"} or if you are used to using uv then [here](https://zensical.org/docs/get-started/#install-with-uv){target="_blank"}.
2. With cloning (forking) the site, the configuration work to [create](https://zensical.org/docs/create-your-site/){target="_blank"} and [publish](https://zensical.org/docs/publish-your-site/){target="_blank"} your site to GitLab is already done for you.
3. You can now go to your top-level working directory in your chosen Python environment (virtual environment or uv) and use the preview function documented [here](https://zensical.org/docs/usage/preview/){target="_blank"}.

## Perform initial configuration

1. The zensical.toml file contains the configuration for your website.

1. Make sure all your files have been saved. Any that are unsaved have a filled circle against the file name. Go to the file and press Ctrl-S/Cmd-S.

## Synchronise your updates

1. Click on the [Source Control] icon (third one down) on the left in Visual Studio Code and you will see a list of all the files that have been changed and created.

    <figure markdown="span">
      <img src="../images/initial-commit.png" style="width: 40%;">
      <figcaption>Initial commit</figcaption>
    </figure>

2. Fill into the Message box short description of the change. In this case, enter 'Initial Commit' as this is the first commit of the code to GitLab.
3. Then press the [Commit] button and select [Save All and Commit Changes].

    <figure markdown="span">
      <img src="../images/commit-changes.png" style="width: 40%;">
      <figcaption>Initial commit</figcaption>
    </figure>

4. Then sync changes with GitLab

    <figure markdown="span">
      <img src="../images/sync-changes.png" style="width: 40%;">
      <figcaption>Sync changes</figcaption>
    </figure>

## Viewing online website

1. Enter in the URL of the website using the form 'https://*namespace*.pages.surrey.ac.uk/*repository-name*'. The URL for this template site is [http://mb0105.pages.surrey.ac.uk/doc-template](http://mb0105.pages.surrey.ac.uk/doc-template){target="_blank"}.
2. A box will pop up for you to authorise access for GitLab Pages to gain access to your project to build it.

    <figure markdown="span">
       <img src="../images/authorise-gitlab-pages.png" style="width: 40%;">
      <figcaption>Authorise GitLab Pagess</figcaption>
    </figure>

3. You will be redirected to a site [https://doc-template-4f75ad.pages.surrey.ac.uk/](https://doc-template-4f75ad.pages.surrey.ac.uk/){target="_blank"}.

## Release your report

1. Before you release your report, remove the *START HERE* section by commenting it out in the zensical.toml file. Enter a # before the five lines defining the menu structure. You can still get to the information, as it's on the documentation template website [http://mb0105.pages.surrey.ac.uk/doc-template/starthere/starthere](http://mb0105.pages.surrey.ac.uk/doc-template/starthere/starthere){target="_blank"}.

    ``` title="zensical.tomal"
    .
    nav = [
      {"Cover" = [
        "index.md",
      ]},
      {"Originality" = [
        {"Content Originality" = "originality.md"}
      ]},
      {"Assignment" = [
        {"Section 1" = "section1.md"},
        {"Section 2" = "section2.md"},
        {"Section 3" = "section3.md"},
        {"Section 4" = "section4.md"}
    # Comment out the START HERE section (5 lines) before final release
    #  ]},
    #    {"START HERE" = [
    #      {"Start Here" = "starthere/starthere.md"},
    #      {"Zensical basics" = "starthere/getstarted.md"},
    #      {"Markdown in 5min" = "starthere/markdown.md"}
       ]}
    ]
    ```
