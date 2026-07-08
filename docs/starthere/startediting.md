---
icon: lucide/book-open
---

<!-- 
# Copyright (c) 2025-2026 Mark Buckwell and contributors
# SPDX-License-Identifier: MIT
# All contributions are certified under the DCO
-->

{{ heading_counter_reset(page) }}

# Start editing

## Viewing documentation locally

The great feature of Zensical is that you view the changes to the website locally using a locally hosted website without sending the source to GitLab,

1. Start with installing python and any other software extensions needed. Use the instructions for pip [here](https://zensical.org/docs/get-started/#install-with-pip){target="_blank"} or uv then [here](https://zensical.org/docs/get-started/#install-with-uv){target="_blank"}.
2. With cloning (forking) the site, the configuration work to [create](https://zensical.org/docs/create-your-site/){target="_blank"} and [publish](https://zensical.org/docs/publish-your-site/){target="_blank"} your site to GitLab is already done for you.
3. You can now go to your top-level working directory in your chosen Python environment (virtual environment or uv) and use the preview function documented [here](https://zensical.org/docs/usage/preview/){target="_blank"}.

## Perform initial configuration

1. The zensical.toml file contains the configuration for your website.

2. Make sure you save all your files. A file that needs saving will have a filled circle beside the file name in the explorer tab. Select the file and press Ctrl-S/Cmd-S.

## Synchronise your updates

1. Click on the :gitlab-branch: icon on the left in Visual Studio Code and you will see a list of all the changed and mew files.

    ![Initial commit](images/initial-commit.png){ width="40%" }
    /// caption
    Initial commit
    ///

2. Fill into the Message box short description of the change. In this case, enter 'Initial Commit' as this is the first commit of the code to GitLab.
3. Then press the **Commit**{: .bg-blue} button and select **Save All and Commit Changes**{: .bg-blue}.

    ![Commit changes](images/commit-changes.png){ width="40%" }
    /// caption
    Commit changes
    ///

4. Then sync changes with GitLab

    ![Sync changes](images/sync-changes.png){ width="40%" }
    /// caption
    Sync changes
    ///

## Viewing online website

{% if is_surrey %}
1. Enter in the address of your Gitlab Pages website using the form 'https://*namespace*.pages.surrey.ac.uk/*repository-name*'. The address for this template site is [http://mb0105.pages.surrey.ac.uk/doc-template](http://mb0105.pages.surrey.ac.uk/doc-template)

1. A box will pop up for you to authorise access for GitLab Pages to gain access to your project to build it.

    ![Authorise GitLab Pages](images/authorise-gitlab-pages.png){ width="40%" }
    /// caption
    Authorise GitLab Pages
    ///

1. The browser will redirect you to a site with an additional unique key in the address, such as [https://doc-template-4f75ad.pages.surrey.ac.uk/](https://doc-template-4f75ad.pages.surrey.ac.uk/){target="_blank"}.

{% else %}

1. Enter in the address of the GitHub Pages website using the form 'https://*username*.github.io/*repository-name*'. The address for this template site is [https://buckwem.github.io/doc-template](https://buckwem.github.io/doc-template){target="_blank"}.

TO DO: Add instructions for authorising GitHub Pages to access the repository and any other steps needed to view the website online.

{% endif %}

## Release your report

Before you release your report, remove the *START HERE* section by commenting it out in the zensical.toml file. Search for START HERE and insert a `#` before the lines between the two comments.

{% if is_surrey %}
!!! Info "University of Surrey Pages Site"
    You can still get to the information, as it's on the documentation template website [http://mb0105.pages.surrey.ac.uk/doc-template/starthere/starthere](http://mb0105.pages.surrey.ac.uk/doc-template/starthere/starthere){target="_blank"}.
{% else %}
!!! Info
    You can still get to the information, as it's on the documentation template website [https://buckwem.github.io/doc-template/starthere/starthere](https://buckwem.github.io/doc-template/starthere/starthere){target="_blank"}.
{% endif %}

``` title="zensical.tomal"
.
nav = [
  {"Cover" = [
    "index.md",
  ]},
  {"Originality" = [
    {"0. Originality & AI Use" = "originality.md"}
  ]},
  {"Assignment" = [
    {"1. Section" = "section1.md"},
    {"2. Section" = "section2.md"},
    {"3. Section" = "section3.md"},
    {"4. Section" = "section4.md"}
  # Comment out the START HERE section (5 lines) before releasing your report, as it contains instructions for the author and is not meant for the reader of the report.
  ]},
    {"START HERE" = [
      {"1. Start Here" = "starthere/starthere.md"},
      {"2. Install tooling" = "starthere/installcore.md"},
      {"3. Install extensions" = "starthere/installextensions.md"},
      {"4. Customise" = "starthere/customise.md"},
      {"5. Markdown basics" = "starthere/markdown.md"},
      {"6. Zensical basics" = "starthere/zensicalbasics.md"},
      {"7. Shell commands" = "starthere/shcommands.md"}
  # Comment until here before releasing your report, as it contains instructions for the author and is not meant for the reader of the report.
  ]}
]
```
