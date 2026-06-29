---
icon: lucide/book-open
---

<!-- 
# Copyright (c) 2025-2026 Mark Buckwell and contributors
# SPDX-License-Identifier: MIT
# All contributions are certified under the DCO
-->

<style>
  /* Reset the page and sidebar to start at 7 */
  .md-typeset { counter-reset: h1-count 6 !important; }
  .md-nav--primary { counter-reset: toc1 7 !important; }
  /* Also change the numbering of the overall title number in the sidebar by editing zensical.toml */
</style>

# Additional tooling

## Setup for signing git commits

Files submitted to a Git repository can be signed using a DCO (Developer Certificate of Origin) signing. The benefit of signing your commits is that it provides a way to verify the authenticity of the code and ensure that it has not been tampered with. It also helps to establish trust between contributors and maintainers, as it provides a way to verify the identity of the person who made the changes.

Setting up for DCO (Developer Certificate of Origin) signing in Git is straightforward. Unlike GPG key signing (which uses cryptographic keys to verify your identity), DCO signing is a legal statement asserting that you have the right to submit the code.

DCO signing simply appends a text line at the very bottom of your commit message that looks like this:
Signed-off-by: Your Name <your.email@example.com>

You will have already configured your Git environment with your name and email. Here is how to set up the DCO signing globally, automate it, and fix any commits you forgot to sign.

### Signing all Git commits globally

Modern versions of Git allow you to turn on automatic DCO signing globally. This means you can run your usual git commit -m "your message" command, and Git will silently inject the signature for you.

Run this command in your terminal:
```bash
git config --global commit.signoff true
```

### Manually signing a single commit

If you want to sign a single commit, you can use the `-s` or `--signoff` option with the `git commit` command. For example:
```bash
git commit -s -m "Your commit message"
```

### Setting up VS Code to automatically sign commits
If you are using Visual Studio Code, you can configure it to automatically sign your commits in two ways.

Either add the following lines to your `settings.json` file:
```json
"git.enableCommitSigning": true,
"git.signoff": true
```

or you can you can use the VS Code GUI to enable commit signing.
1. Open the **Settings** panel, search for "commit signing".
1. Check the box for **Git: Enable Commit Signing** and **Git: Signoff**.





## Installing GitLab or GitHub extensions

VS Code doesn't require any extensions to work with GitLab or GitHub, but installing the relevant extension can make it easier to manage your documentation in GitLab or GitHub. Some features of these extensions include:
1. Viewing issues and merge requests directly in VS Code.
1. Creating and managing issues and merge requests directly in VS Code. 
1. Viewing and managing your GitLab or GitHub repositories directly in VS Code.
1. Viewing and managing your GitLab or GitHub CI/CD pipelines directly in VS Code.


!!! TODO "TO DO"
    Provide instructions for installing GitLab or GitHub extensions in VS Code.

## Configuring GitLab or GitHub extensions

1. Now we need to create a personal access token (PAT) with specific permissions for your GitLab or GitHub account. This will allow VS Code to access your GitLab or GitHub account without needing to enter your username and password every time you push changes to the repository.

    <div class="grid cards one-column" markdown>
        
    -   :material-clock-fast:{ .lg .middle } __Create a Personal Access Token (PAT)__

        ---

        === "GitLab"

            1. Log in to **GitLab** (either [gitlab.com](https://gitlab.com) or your organisation's self-managed instance) in a web browser.
            2. In the top-right corner, click on your **profile avatar** and select **Edit profile**. 
            3. On the left-hand sidebar, select **Access > Personal access tokens**.
            4. Click **Add new token**{: .bg-blue} (or use the token generation form) and fill out the following details:
                * **Token name:** Give it a clear name (e.g., VS Code Extension).
                * **Expiration date:** (Optional) Set an expiration date according to your team's security policy. You can click on the date and select the last date available.
            5. Under **Select scopes**, check the **api** scope and copy the token string.
            6. Click **Create token**{: .bg-blue} and copy the token string.
            
            !!! Warning
                Copy the token string **immediately**. GitLab will only show it to you once; if you refresh or leave the page, it is gone forever.

        === "GitHub"

            Review the insstructions for configuring VS Code for Git rep access as it normally uses a browser OAuth workflow. If you are a GitHub Enterprise Server user, the browser flow may not work out of the box. In that case, you can use a personal access token (PAT) instead.

            1. Log in to **GitHub** (either [github.com](https://github.com) or your organisation's self-managed instance).
            1. In the top-right corner, click on your **profile avatar** and select **Settings**.
            1. On the left-hand sidebar, select **Developer settings > Personal access tokens >Fine-grained tokens**.
            
            !!! Note
                You may be prompted to reauthenticate with GitHub before proceeding to the next step.

            1. Click **Generate new token**{: .bg-green} and fill out the following details:
                * **Token name:** Give it a clear name (e.g., VS Code Extension).
                * **Expiration date:** (Optional) Set an expiration date according to your team's security policy. You can click on the date and select the last date available.
            1. Select the **Repository access** level for the token. Choose **All repositories** if you want the token to have access to all your repositories, or choose **Only select repositories** and specify the repositories you want to grant access to.
            1. Under **Permissions**, select **+ Add permissions** and add the following:
                * **Read and Write** access to **Contents** and **Pull Requests**.
                * **Read-only** access to **Metadata**.
            1. Click **Generate token**{: .bg-green} and copy the token string.
            
            !!! Warning
                Copy the token string **immediately**. GitHub will only show it to you once; if you refresh or leave the page, it is gone forever.

    </div>

4. Next, configure the *GitLab* or *GitHub* plugin to use a personal access token (PAT). The instructions below are for both *GitLab* and *GitHub* plugins.

    <div class="grid cards one-column" markdown>
        
    -   :material-clock-fast:{ .lg .middle } __Configure VS Code for Git repo access__

        ---

        === "GitLab"
            
            GitLab's OAuth flow may not work in some environments, so we will use a personal access token (PAT) instead.

            1. Open VS Code and open the **Command Palette**:
                1. For **macOS**, press **Command+Shift+P**.
                1. For **Windows** or **Linux**, press **Control+Shift+P**.
            1. Type `Gitlab: Authenticate` and press `Enter`.
            1. Choose your GitLab instance
                * Select **GitLab.com** if you use a public cloud instance.
                * Select **Add new instance URL** if you use a self-hosted instance, and type out your full dowmain (e.g., `https://gitlab.yourorganisation.com`).
            1. Select **Enter an existing token**
            1. Paste in your personal access token (PAT) that you created earlier and hit `Enter`.
          
            The extension will instantly validate the token. If successful, you will see your GitLab status update in the bottom status bar, and your GitLab sidebar panel will populate with your issues and merge requests.


        === "GitHub"

            The built-in GitHub Authentication provider in VS Code forces a browser OAuth workflow by default. However, if your browser is failing to redirect back to VS Code (due to a firewall, proxy, or strict security settings), you can easily use a token fallback.

            1. Click the **Accounts** icon (the profile silhouette) in the bottom-left corner of VS Code.

            1. Select **Sign in with GitHub** to use... (or trigger a sign-in via Copilot/Settings Sync).

            1. Click **Allow** when asked to open the external website.

            1. Your browser will open GitHub to authorize the app. Click **Authorize Visual Studio Code**.

            1. **The Fallback:** If the browser gets stuck or fails to automatically reopen VS Code, GitHub will display a web page saying *"If your browser does not redirect you..."* alongside a **blue box containing an authorization token.** Copy that token.

            1. Return to VS Code. Look at the very bottom **Status Bar**; it will say `Signing in to github.com....`

            1. Click that status bar text. An input box will open at the top of your editor.

            1. Paste the token you copied from the browser page and hit `Enter`.

            !!! Note "Note for GitHub Enterprise Server Users"
                If your company hosts its own private GitHub Enterprise Server, the browser flow won't always work out of the box. To use a PAT directly, start the sign-in prompt, click Cancel on the browser authorization popups, and VS Code will automatically change its prompt to a direct text field asking you to paste your Enterprise PAT.

    </div>

## Install vale to check for grammar, spelling, and style issues

[Vale](https://vale.sh/){target="_blank"} is a syntax and style checker for writing. You can use it to check your documentation for grammar, spelling, and style issues. 

1. To install Vale, follow the instructions below for your operating system. 

    <div class="grid cards one-column" markdown>
    
    -   :material-clock-fast:{ .lg .middle } __Install Vale__

        ---

        === "macOS - Homebrew"

            We use Homebrew to install Visual Studio Code on macOS. If you don't have Homebrew installed, you can install it using the following command in your Terminal:
            ``` bash
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            ```
            
            Once Homebrew is installed, run this command in your Terminal:
            ``` bash
            brew install vale
            ```

        === "Windows 11 - Winget"

            Use the Microsoft Windows Package Manager (winget) to install Vale on Windows 11. 
            
            Open up a **PowerShell** session running as an administrator and install `vale` using the following command:

            ``` powershell
            winget install --id errata-ai.Vale
            ```

        === "Linux - Ubuntu/Debian"

            We use snaps to install Vale on Ubunti/Debian Linux. If you don't have snapd installed, you can install it using the following commands:
            ``` bash    
            sudo apt update
            sudo apt install snapd
            ```
            
            Once snapd is installed, you can install Vale using the following command:
            ```shell
            sudo snap install vale
            ```

    </div>

     You can find further information on installing Vale on Linux on the [Vale installation page](https://vale.sh/docs/install/){target="_blank"}.
    
2. Create a .vale.ini file in the top level directory of your project. This file configures Vale and specifies the rules and styles for checking your documentation. You can use the following example `.vale.ini` file as a starting point:

    ```ini
    StylesPath = styles
    MinAlertLevel = suggestion
    Packages = Microsoft, Readability, proselint

    [*.{md,rst,asciidoc,html}]
    BasedOnStyles = Vale, Microsoft, Readability, proselint

    Vale.Terms = YES
    Vale.Avoid = YES
    Vale.Spelling = YES

    Microsoft.OxfordComma = YES
    Microsoft.Passive = YES
    Microsoft.Dashes = YES
    Microsoft.Spacing = YES
    Microsoft.Wordiness = YES
    Microsoft.We = YES
    ```

3. Create a `styles` directory in the top level directory of your project. Then synchronise the styles specified in the `.vale.ini` file running from the top-level directory of your project:

    ```bash
    vale sync
    ```

4. Use Vale to check your documentation in Visual Studio Code by installing the [Vale VSCode extension](https://marketplace.visualstudio.com/items?itemName=ChrisChinchilla.vale-vscode){target="_blank"} and then restarting Visual Studio Code. 

     When you open a Markdown file in Visual Studio Code, the Vale extension will automatically check your Markdown files you open for grammar, spelling, and style issues based on the rules and styles. View the results in the *Problems* panel of Visual Studio Code.

     You will find it gwenerates a large numnber of suggestions, some of which aren't relevant to your documentation. You can ignore these and focus on the suggestions that are relevant to your writing style and the requirements of your documentation.

5. One of the most prominent suggestions is to change from passive voice to active voice. This is a good suggestion and recommended in business writing, but it can take time to change all instances of a passive voice to active voice.

    If you need some help for this, here are a few websites that can help you understand how to change from passive voice to active voice:
 
    1. [BBC Bitesize](https://www.bbc.co.uk/bitesize/articles/zkttng8){target="_blank"}
    1. [Communication for Professionals](https://courses.lumenlearning.com/suny-esc-communicationforprofessionals/chapter/active-voice/){target="_blank"}
    1. [University of York](https://subjectguides.york.ac.uk/academic-language/voice){target="_blank"}

    You can also change the `Microsoft.Passive` rule in the `.vale.ini` file to `NO` if you find it too difficult to change all instances of passive voice to active voice.
    
