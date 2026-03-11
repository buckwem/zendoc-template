---
icon: lucide/rocket
---

# START HERE

Documentation is easy to write on a static website when using [markdown](https://www.markdownguide.org/) and it's much easier to use than [LateX](https://www.latex-project.org/), which is designed for academic documentation.

## Some history

There are various open source static website generators available including [Read the Docs](https://docs.readthedocs.com/platform/stable/index.html#) and [MkDocs](https://www.mkdocs.org/). A popular combination has been [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) that produces professional documentation using a Material design theme. It's had a very active community of developers creating plugins but development has stopped for the past 18 months. From there the Material for MkDocs primary authors developed a new static website generator, [Zensical](https://zensical.org/), written for speed using the [Rust programming langiuage](https://rust-lang.org/). This website is written using Zensical.

## How it works

Zensical provides the theme and tooling to enable you to write documentation using Markdown and immediately view the website locally. To create am online website to share with others, the files are loaded into the university GitLab and automation then builds it into an online website.

To make it easy for you, a documentation template has been created that you will clone (fork) into a project you can use to develop your own document or report. Follow the instructions below to get started creating an environment to write the content to publish on your static website.

## Install the pre-requisites

We suggest you use Visual Studio Code with appropriate plugins to edit your static website. Complete the following steps.

1. Start with installing [Visual Studio Code](https://code.visualstudio.com/)
2. Install [GitLab plugin](https://marketplace.visualstudio.com/items?itemName=GitLab.gitlab-workflow) in Visual Studio Code. This will enable you manage your documentation in GitLab.
3. Install [markdownlint](https://marketplace.visualstudio.com/items?itemName=DavidAnson.vscode-markdownlint) plugin for Visual Studio Code. This is designed to check your markdown files against a library of rules to encourage standards and consistency.
3. Install [Even Better TOML](https://marketplace.visualstudio.com/items?itemName=tamasfe.even-better-toml) plugin for Visual Studio Code. This extension help manage a TOML file.
4. Connect Visual Studio Code with GitHub using HTTPS.  TODO

## Initialise your repository

1. Create a directory for all your GitLab projects on your local desktop. For example, create a directory called 'gitlab' on your OneDrive. Using OneDrive will give you another backup of your gitlab repository.
2. [Fork a copy of the documentation template](https://gitlab.surrey.ac.uk/mb0105/doc-template/-/forks/new) to create a copy of the template for your use.
3. Enter the *Project name* using to the format the coursework specifies. For example, for Coursework 1 for the module COMM058 in the year 2026, enter 'comm058-coursework1-2026'. Use all lowercase and a dash between words with no spaces. This will be used to create the project URL.
4. Select your personal namespace for the project URL.
5. Change the *Visibility Level* to *Private*.
6. Press the button [Fork Project] to create your own copy of the project.

    !!! Warning
        Don't forget to set the visibility to private, otherwise other students can see your coursework. Ask another student to check whether they can see your site. We will discuss how to view it later in the instructions.

## Download repository locally

1. Next we need to download and copy the project into Visual Studio Code so you can work with it locally. Select the [Code v] button and a menu will come up. Select the HTTPS button to the right of Visual Studio Code.
2. A browser popup will appear saying 'Open Visual Studio Code?' and you push the [Open Visual Stdio Code] button.
3. This will open a directory selection box. Go to the 'gitlab' directory you selected earlier and press the [Select as Repository Destination]. This will then download the code to a subdirectory with the name of the project you created earlier.

    <figure markdown="span">
      <img src="../images/directory-selection.png" style="width: 70%;">
      <figcaption>Directory selection</figcaption>
    </figure>

4. Then you will be prompted to open your repository that is stored in your 'gitlab' directory. If you already have Visual Studio Code, you may wish to select [Open in a new window] so it creates a seprate window to your current workspace.

    <figure markdown="span">
      <img src="../images/open-repository.png" style="width: 40%;">
      <figcaption>Open repository</figcaption>
    </figure>

## Viewing local website

The great feature of Zensical is that you view the changes to the website locally using a locally hosted website without sending the source to gitlab,

1. Start with installing python and any other software extensions that are required. Use the instructions for pip [here](https://zensical.org/docs/get-started/#install-with-pip) or if you are used to using uv then [here](https://zensical.org/docs/get-started/#install-with-uv).
2. With cloning (forking) the site, the configuration work to [create](https://zensical.org/docs/create-your-site/) and [publish](https://zensical.org/docs/publish-your-site/) your site is already done for you.
3. You can now go to your top-level working directory in your chosen Python environment (virtual environment or uv) and use the preview function documented [here](https://zensical.org/docs/usage/preview/).

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

1. Enter in the URL of the website using the form 'https://*namespace*.pages.surrey.ac.uk/*repository-name*'. The URL for this template site is [http://mb0105.pages.surrey.ac.uk/doc-template](http://mb0105.pages.surrey.ac.uk/doc-template)
2. A box will pop up for you to authorise access for GitLab Pages to gain access to your project to build it.

    <figure markdown="span">
       <img src="../images/authorise-gitlab-pages.png" style="width: 40%;">
      <figcaption>Authorise GitLab Pagess</figcaption>
    </figure>

3. You will be redirected to a site [https://doc-template-4f75ad.pages.surrey.ac.uk/](https://doc-template-4f75ad.pages.surrey.ac.uk/)

## Release your report

1. Before you release your report, remove the *START HERE* section by commenting it out in the zensical.toml file. Enter a # before the five lines defining the menu structure. You can still get to the information, as it's on the documentation template website [http://mb0105.pages.surrey.ac.uk/doc-template/starthere/starthere](http://mb0105.pages.surrey.ac.uk/doc-template/starthere/starthere)

    ``` title="zensical.tomal"
    .
    .
    .
      {"Assignment" = [
      {"Section 1" = "section1.md"},
      {"Section 2" = "section2.md"},
      {"Section 3" = "section3.md"},
      {"Section 4" = "section4.md"}
    #  ]},
    #    {"START HERE" = [
    #      {"Start Here" = "starthere/starthere.md"},
    #      {"Zensical basics" = "starthere/getstarted.md"},
    #      {"Markdown in 5min" = "starthere/markdown.md"}
      ]}
    ]
    .
    .
    .
    ```
