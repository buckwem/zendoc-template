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

This page covers the day-to-day cycle of working on your document: previewing your changes locally, syncing them to GitLab or GitHub, viewing the published website, building the PDF, working with branches and issues, troubleshooting common problems, and finally releasing your report. It assumes no prior experience with the command line, Git, or software development - every step is spelled out, with the exact commands to type. For one-time setup (installing Python, Git, and Zensical itself), see [Install tooling](installtooling.md) first if you haven't already.

## Viewing documentation locally

Zensical renders your Markdown into a live, locally hosted website as you write, without you needing to push anything - so you can check headings, links, images, diagrams, and PDF-only/web-only content render correctly before anyone else sees them.

### Open a terminal

A terminal (also called a command line, console, or shell) is a text-based way to give your computer instructions by typing commands, instead of clicking buttons. It can look intimidating at first, but this whole workflow only needs a handful of commands, and they're all given below.

The easiest way to open one is Visual Studio Code's own integrated terminal:

1. Open your project folder in Visual Studio Code, if it isn't already open (**File** > **Open Folder...**).
2. Open the integrated terminal, whichever way is quickest for you:
    * Menu: **View** > **Terminal**.
    * Keyboard shortcut: `` Ctrl+` `` on Windows/Linux, `` Cmd+` `` on macOS.
    * Command Palette (`Ctrl+Shift+P`/`Cmd+Shift+P`) > **View: Toggle Terminal**.
3. A panel opens at the bottom of the window, already sitting in your project folder - defaulting to PowerShell on Windows, or your shell of choice (bash/zsh) on macOS and Linux.

This integrated terminal also activates your Python virtual environment automatically (a self-contained folder holding just this project's Python packages, kept separate from everything else on your computer), as long as you've selected the `.venv` interpreter once - see [Install Python and Zensical](installtooling.md#install-python-and-zensical). That's the recommended path, since it needs no further steps below.

If you'd rather use your system's own terminal application instead of Visual Studio Code's, you need to navigate to your project folder and activate the virtual environment yourself:

<div class="grid cards one-column" markdown>

-   :material-clock-fast:{ .lg .middle } __Activate the virtual environment manually__

    === "macOS/Linux Terminal"

        1. Open a terminal application:
            * **macOS:** press `Cmd+Space` to open Spotlight, type `Terminal`, and press `Enter`.
            * **Linux:** look for **Terminal** in your applications menu.
        2. Navigate to your project folder using the `cd` (change directory) command - replace the path below with wherever you cloned your project:

            ```bash
            cd path/to/your/project
            ```

        3. Activate the virtual environment:

            ```bash
            source .venv/bin/activate
            ```

            Your prompt now starts with `(.venv)`, confirming it's active.

    === "Windows PowerShell"

        1. Open PowerShell: press the `Windows` key, type `PowerShell`, and press `Enter`.
        2. Navigate to your project folder using the `cd` command:

            ```powershell
            cd path\to\your\project
            ```

        3. Activate the virtual environment:

            ```powershell
            .\.venv\Scripts\Activate.ps1
            ```

            Your prompt now starts with `(.venv)`, confirming it's active.

</div>

### Start the preview server

1. In your terminal (with the virtual environment active), start the local preview server:

    ```bash
    zensical serve
    ```

2. Wait for it to finish starting - you'll see some log messages ending with a local web address.
3. Open that address (typically [http://127.0.0.1:8000](http://127.0.0.1:8000)) in your browser to view your documentation.

Leave `zensical serve` running in its terminal while you write - it watches your files and automatically rebuilds and refreshes the browser whenever you save a change, so you don't need to restart it after every edit. To stop it, click back into its terminal and press `Ctrl+C`.

!!! tip
    `zensical serve` only builds the website - it doesn't touch `docs/site_documentation.pdf`. See [Build the PDF](#build-the-pdf) below to preview the PDF output.

## Synchronise your updates

Whenever you've made a change you want to keep, there are three things to do: **save** the file, **commit** it (record a labelled snapshot of the change in your project's history), and **push** it (upload that snapshot to GitLab or GitHub, where it's backed up and, once it reaches your default branch, published). You can do all three either through Visual Studio Code's Source Control view, or by typing Git commands directly - both do exactly the same thing, so use whichever feels more comfortable.

<div class="grid cards one-column" markdown>

-   :material-clock-fast:{ .lg .middle } __Commit and push your changes__

    === "Visual Studio Code"

        1. Make sure your changed files are saved (a filled circle next to a file name in the Explorer tab means it has unsaved changes - select the file and press `Ctrl+S` / `Cmd+S`).
        2. Click the :gitlab-branch: **Source Control** icon in the left-hand sidebar. You'll see a list of every changed and new file.

            ![Initial commit](images/initial-commit.png){ width="40%" }
            /// caption
            Initial commit
            ///

        3. Type a short, descriptive message in the message box (for example, "Add section 2 draft") - this is the label future-you (or a marker) will see when looking back through the history.
        4. Press the **Commit**{: .bg-blue} button and select **Save All and Commit Changes**{: .bg-blue}. This records the snapshot on your computer only - nothing has been sent anywhere yet.

            ![Commit changes](images/commit-changes.png){ width="40%" }
            /// caption
            Commit changes
            ///

        5. Press **Sync Changes**{: .bg-blue} to push your commit to GitLab or GitHub (and pull down anyone else's changes too).

            ![Sync changes](images/sync-changes.png){ width="40%" }
            /// caption
            Sync changes
            ///

    === "Command line"

        1. Check what's changed - this lists every file you've added, edited, or deleted since your last commit:

            ```bash
            git status
            ```

        2. Stage the files you want to commit - "staging" means marking them to be included in the next commit (use `git add .` to stage everything shown by `git status` in one go):

            ```bash
            git add docs/section1.md
            ```

        3. Commit the staged changes with a short, descriptive message:

            ```bash
            git commit -m "Add section 2 draft"
            ```

            This records the snapshot on your computer only - nothing has been sent anywhere yet.

        4. Push your commit to your GitLab or GitHub remote, uploading it so it's backed up and visible online:

            ```bash
            git push
            ```

</div>

!!! note
    Commit little and often. Small, clearly described commits are easier to review, easier to revert if something goes wrong, and give you a much more useful history to look back on than one huge commit at the deadline.

## Viewing online website

Once your commit reaches the default branch, the [CI/CD pipeline](#automated-builds) rebuilds and republishes the website (and the PDF) automatically - there's nothing extra to trigger.

{% if is_surrey %}
1. Go to your GitLab Pages address, in the form `https://`*namespace*`.pages.surrey.ac.uk/`*repository-name*. This template's own site is at [http://mb0105.pages.surrey.ac.uk/doc-template](http://mb0105.pages.surrey.ac.uk/doc-template){target="_blank"}.
2. The first time you visit, GitLab prompts you to authorise GitLab Pages access to your project:

    ![Authorise GitLab Pages](images/authorise-gitlab-pages.png){ width="40%" }
    /// caption
    Authorise GitLab Pages
    ///

3. Your browser redirects to a URL with an extra, unique key added, such as [https://doc-template-4f75ad.pages.surrey.ac.uk/](https://doc-template-4f75ad.pages.surrey.ac.uk/){target="_blank"}. This confirms you (specifically, someone with access to the underlying GitLab project) are allowed to view the page - University of Surrey GitLab Pages sites aren't public by default.

{% else %}

1. Go to your GitHub Pages address, in the form `https://`*username*`.github.io/`*repository-name*. This template's own site is at [https://buckwem.github.io/doc-template](https://buckwem.github.io/doc-template){target="_blank"}.
2. Unlike GitLab Pages, GitHub Pages sites are publicly accessible by default, even when the source repository is private - so no separate authorisation step is normally needed to view a GitHub Pages site once it's built.
3. If your organisation has restricted Pages visibility (available on GitHub Enterprise), you'll be asked to sign in to GitHub with an account that has access to the repository before the site loads.

{% endif %}

!!! warning
    The very first deployment can take a few minutes to build. If you get a 404, wait a little and refresh before assuming something's broken - check the pipeline/workflow run for errors first.

## Build the PDF

`docs/site_documentation.pdf` isn't built by `zensical serve` or `zensical build` - it has its own build script, `build_pdf.py`.

### Building it manually

1. Make sure the PDF build's dependencies are installed - see [Install Python and Zensical](installtooling.md#install-python-and-zensical) for `requirements.txt`, and [Additional tooling](additionaltooling.md) if your document uses Mermaid diagrams or maths and you need the optional `tools/mermaid`/`tools/mathjax` Node packages too.
2. [Open a terminal](#open-a-terminal) with your virtual environment active, in your project's root directory.
3. Run the build script:

    ```bash
    python build_pdf.py
    ```

    This can take a little while, especially the first time - it's converting every page into a single PDF, rendering any diagrams and maths along the way.

4. Once it finishes, open `docs/site_documentation.pdf` (in the `docs` folder) to check the result.

Run this again after any change you want reflected in the PDF - it always rebuilds the whole document from scratch, so there's no separate "clean" step needed for it, unlike the website build below.

### Automated builds

Both `.gitlab-ci.yml` and `.github/workflows/docs.yml` run this exact sequence automatically on every push to your default branch:

```bash
python build_pdf.py
zensical build --clean
```

`build_pdf.py` runs first so `docs/site_documentation.pdf` exists before the site is built - that's what makes the "Download PDF" button on the cover page work, since the PDF gets published as part of the website itself. `zensical build --clean` then builds the site into the `public/` directory (set by `site_dir` in `zensical.toml`), which GitLab Pages or GitHub Pages then publishes. See [Clean build](#clean-build) in Troubleshooting if you need to force a fresh website build locally.

## Managing branches and issues

Once you're comfortable with the basic commit-and-push cycle, branches and issues give you two extra tools for organising bigger or shared pieces of work: a branch isolates a change until it's ready, and an issue records what needs doing, with the two linked together.

### Working with branches

A branch is a parallel, isolated copy of your files where you can work without affecting the "real", published version until you're ready. For anything more than a small tweak - a new section, a bigger restructure - it's worth developing it on its own branch rather than directly on your default branch (usually `main`). That keeps `main` (and therefore the published website and PDF) stable while you're mid-change, and makes an unfinished idea easy to abandon without cleaning up half-done edits.

<div class="grid cards one-column" markdown>

-   :material-clock-fast:{ .lg .middle } __Create a new branch__

    === "Visual Studio Code"

        1. Click the branch name in the bottom-left of the status bar (it normally reads `main`).
        2. Select **Create new branch...** and give it a short, descriptive name (for example, `add-section-3`).
        3. Visual Studio Code switches you onto the new branch. Edit, save, and commit as usual (see [Synchronise your updates](#synchronise-your-updates)) - your commits go onto this branch, not `main`.
        4. The first time you press **Sync Changes**{: .bg-blue}, Visual Studio Code offers to **Publish Branch**{: .bg-blue} instead - accept this to push the new branch to GitLab or GitHub.

    === "Command line"

        1. Create and switch to a new branch in one step:

            ```bash
            git switch -c add-section-3
            ```

        2. Commit as usual (see [Synchronise your updates](#synchronise-your-updates)) - your commits go onto this branch, not `main`.
        3. Push it, telling Git to track this new branch on the remote the first time:

            ```bash
            git push -u origin add-section-3
            ```

            After that first push, a plain `git push` is enough.

</div>

### Merging your branch back

Once you're happy with the branch, bring it into your default branch so it's published.

<div class="grid cards one-column" markdown>

-   :material-clock-fast:{ .lg .middle } __Merge your branch__

    === "Merge/pull request (recommended)"

        1. Open your project on GitLab or GitHub in a browser.
        2. Open a merge request (GitLab) or pull request (GitHub) from your branch into `main` - both platforms show a prompt for this as soon as you push a new branch, or you can start one from the **Merge requests**/**Pull requests** section of the sidebar.
        3. This gives you, or a collaborator, a chance to review the diff before it goes live.
        4. Once you're happy, click the **Merge**{: .bg-blue} button on the merge/pull request page - GitLab or GitHub does the rest.

    === "Merge locally"

        If you're working alone and don't need a review step first:

        1. Switch to your default branch:

            ```bash
            git switch main
            ```

        2. Pull down the latest version, in case anything's changed since you branched:

            ```bash
            git pull
            ```

        3. Merge your branch into it:

            ```bash
            git merge add-section-3
            ```

        4. Push the result:

            ```bash
            git push
            ```

</div>

Either way, once the merge reaches `main`, the [CI/CD pipeline](#automated-builds) rebuilds and republishes the website and PDF automatically, the same as any other push to `main`.

!!! tip
    Delete the branch once it's merged - neither GitLab nor GitHub need it anymore, and it keeps your branch list tidy. Both offer a **Delete branch** button right after a merge request or pull request is merged.

### Recording issues and linking them to a branch

Issues are GitLab's and GitHub's built-in way to track things to do - a missing section, a diagram to add, a typo to fix - separately from the writing itself. They're especially useful once more than one person is working on the same report, or if you just want a running to-do list attached to the project instead of a separate document.

1. Open the **Issues** section in the left-hand sidebar of your project on the website, and select **New issue**.
2. Give it a short title (for example, "Add diagram to section 2") and, optionally, a longer description of what's needed.

Both platforms let you create a branch directly from an issue, which links the two together from the start:

{% if is_surrey %}
* On GitLab, open the issue and use the **Create merge request**{: .bg-blue} button (or the dropdown next to it, for **Create branch** only). This creates a branch named after the issue (for example `12-add-diagram-to-section-2`) and links it back to the issue automatically.
{% else %}
* On GitHub, open the issue and, in the right-hand sidebar under **Development**, select **Create a branch**. This creates a branch linked to the issue, and offers to check it out for you.
{% endif %}

If you've already created your branch by hand instead (see [Working with branches](#working-with-branches)), you can still link it to an issue by mentioning the issue number in a commit message:

```bash
git commit -m "Add diagram to section 2 (#12)"
```

Using `Closes #12`, `Fixes #12`, or `Resolves #12` instead of just `#12` - in the commit message, or in the merge/pull request description - automatically closes that issue as soon as the commit reaches your default branch.

## Trouble shooting

Common problems you might hit while working on your document, and how to fix them.

### Local preview isn't updating

If you save a change and the browser doesn't refresh, or the page looks stuck:

1. Do a hard refresh in the browser first (`Ctrl+Shift+R` on Windows/Linux, `Cmd+Shift+R` on macOS) - this bypasses the browser's own cache, which is a more common culprit than Zensical itself.
2. If that doesn't help, stop the server (`Ctrl+C` in its terminal) and start it again:

    ```bash
    zensical serve
    ```

3. Still stuck? Check the terminal `zensical serve` is running in - a build error there (for example, invalid TOML in `zensical.toml`, or a broken link) stops it rebuilding, and it'll usually tell you exactly which file and line to look at.

### Clean build

The `--clean` flag on `zensical build --clean` deletes the previous contents of `public/` before rebuilding, so pages you've since renamed or removed don't linger in the published site. Both CI pipelines always build clean.

To do the same locally - useful if the local `public/` folder looks out of date or you suspect a stale file is causing an issue - delete it yourself first:

```bash
rm -rf public
python build_pdf.py
zensical build --clean
```

### Numbered lists reset to "1."

If a numbered list in your Markdown restarts at "1." partway through instead of continuing (for example after a code block, admonition, or tab), it's almost always an indentation problem - Zensical (and Pandoc, for the PDF) only treat content as *continuing* the list item if it's indented to match. See [Lists within lists](zensicalbasics.md#lists-within-lists) for the exact rule to follow.

### PDF build fails

If `python build_pdf.py` errors out or produces a PDF missing content:

1. Check the error message in the terminal - it usually names the file and the problem directly.
2. Make sure the dependencies from `requirements.txt` are installed in your active virtual environment (see [Install Python and Zensical](installtooling.md#install-python-and-zensical)).
3. If your document uses Mermaid diagrams or maths, make sure the optional Node tooling is installed too (see [Additional tooling](additionaltooling.md)) - without it, those elements are silently skipped rather than causing an error.

### Published site shows old content or a 404

1. Check the pipeline (GitLab **CI/CD > Pipelines**) or workflow (GitHub **Actions** tab) actually ran, and succeeded, for your latest commit - if it's still running, or failed, the old version stays published.
2. Confirm your change actually reached the default branch (`main`) - a commit sitting on a feature branch, or a merge/pull request that hasn't been merged yet, never triggers a rebuild. See [Managing branches and issues](#managing-branches-and-issues).
3. Hard refresh the published page (`Ctrl+Shift+R`/`Cmd+Shift+R`) - your browser can cache the old version just as easily as it caches the local preview.

## Release your report

Before you submit your report, remove the "Start Here" section so it isn't part of what you hand in. Full details, including exactly what to comment out in `zensical.toml` and whether to delete the `starthere/` files entirely, are in [Finalising your document](customise.md#finalising-your-document) - do that now if you haven't already.

{% if is_surrey %}
!!! Info "University of Surrey Pages Site"
    Once you've removed "Start Here" from your own report, you can still come back to this guidance on the documentation template's own site at [http://mb0105.pages.surrey.ac.uk/doc-template/starthere/starthere](http://mb0105.pages.surrey.ac.uk/doc-template/starthere/starthere){target="_blank"}.
{% else %}
!!! Info
    Once you've removed "Start Here" from your own report, you can still come back to this guidance on the documentation template's own site at [https://buckwem.github.io/doc-template/starthere/starthere](https://buckwem.github.io/doc-template/starthere/starthere){target="_blank"}.
{% endif %}

## Where to go next

* [Customisation](customise.md) - branding, the cover page, PDF layout, and the document's directory structure.
* [Additional tooling](additionaltooling.md) - signing Git commits, a Markdown word-count command, GitLab/GitHub VS Code extensions, and Vale for spelling/grammar/style checking.
