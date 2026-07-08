---
icon: lucide/book-open 
---

<!-- 
Copyright (c) 2025-2026 Mark Buckwell and contributors
SPDX-License-Identifier: MIT
All contributions are certified under the DCO
-->

{{ heading_counter_reset(page) }}

# Install tooling

This section takes you through the core installation steps for the tools needed to edit your static website. The instructions are for macOS, Windows 11, and Linux (Ubuntu/Debian). If you are using a different operating system, please refer to the official documentation for that operating system.

!!! Tip
    The screenshots below may have small text on your screen. You can click on an image to enlarge it.

The install and configuration starts with the setup of Visual Studio Code.

## Install Visual Studio Code

[Visual Studio Code](https://code.visualstudio.com){target="_blank"} (VS Code) is the selected primary editor for developing your documentation website using Zensical. You can use other editors, but the availability of many plugins in Visual Studio Code will help you edit your documentation more efficiently.

The steps below will help you install VS Code and some essential plugins to edit your documentation. If you have already installed VS Code, check through the steps so you have the plugins installed.

### Install Visual Studio Code

1. Start with installing [Visual Studio Code](https://code.visualstudio.com){target="_blank"}. Instructions for macOS, 

    <div class="grid cards one-column" markdown>
    
    -   :material-clock-fast:{ .lg .middle } __Install Visual Studio Code__

        === "macOS using Homebrew"

            1. If you use the Homebrew package manager, run this command in your Terminal:
                ``` bash
                brew install --cask visual-studio-code
                ```

        === "Windows 11 using PowerShell"

            1. Download the VS Code User setup for Windows.
            2. Run the installer, `VSCodeUserSetup-{version}.exe`. By default the User setup installs Visual Studio Code to your user profile directory. You can change the install location if you want to install it for all users.
         
        === "Linux (Ubuntu/Debian) using bash"

            1. Download the `.deb` package from the [official website](https://code.visualstudio.com/).
            2. Open a terminal and navigate to the directory where you downloaded the `.deb` package.
            3. Run the following command to install Visual Studio Code:
                ``` bash
                sudo apt install ./<file>.deb
                ```
            Replace `<file>` with the name of the downloaded `.deb` file.
            
        Further installation instructions are available on the [Visual Studio Code website](https://code.visualstudio.com/docs/setup/linux){target="_blank"}.

    </div>

### Install Visual Studio Code plugins

VS Code has a rich ecosystem of plugins that can enhance your editing experience. The following plugins are recommended for working with Markdown and Zensical:

1. Install [markdownlint](https://marketplace.visualstudio.com/items?itemName=DavidAnson.vscode-markdownlint){target="_blank"} plugin for Visual Studio Code from the marketplace. This mardownlint extension checks your markdown files using a library of rules to encourage consistent formatting.
1. Install [Even Better TOML](https://marketplace.visualstudio.com/items?itemName=tamasfe.even-better-toml){target="_blank"} plugin for Visual Studio Code from the marketplace. This extension helps manage a [TOML](https://toml.io/en/){target="_blank"} file.
1. Install [LTeX+–LanguageTool grammar/spell checking](https://marketplace.visualstudio.com/items?itemName=ltex-plus.vscode-ltex-plus){target="_blank"} plugin for Visual Studio Code from the marketplace to enable spelling and grammar checking for Markdown. Configure the plugin in the settings to use the *language* `en-GB`.

## Install Git with Visual Studio Code

[Git](https://git-scm.com/){target="_blank"} is a version control system that enables you to track changes to your code and collaborate with others. You will be using Git to manage your documentation website and push your changes to your **GitLab** or **GitHub** cloud repository.

Next, install the `git` command and configure it for Visual Studio Code. The instructions below are for using with both *GitLab* and *GitHub*.

### Install and configure Git

1. As a start, you need to install the `git` command. Follow the instructions below to install or update `git` to the latest stable version.

    <div class="grid cards one-column" markdown>
    
    -   :material-clock-fast:{ .lg .middle } __Install Git__

        === "macOS using Homebrew"

            If you use the Homebrew package manager, run this command in your Terminal to either install or update `git` to the latest stable version:
                
            ``` bash
            brew update
            brew install git
            ```

        === "Windows 11 using PowerShell"

            Open up a **PowerShell** window and install `git` using the command, or you can download and installthe official git installer from [git-scm.com](https://git-scm.com/download/win){target="_blank"}.
                
            ``` PowerShell
            winget install Git.Git
            ```
        
            If you just require an updated version of `git`, you can run the following command in **PowerShell**:
                
            ``` PowerShell
            winget upgrade Git.Git
            ```

        === "Linux (Ubuntu/Debian) using bash"

            Open a terminal and run the following command to install or update `git` to the latest stable version:
            
            ``` bash
            sudo apt update
            sudo apt install git
            ```
    </div>

    Before connecting to any cloud provider, open your terminal (Terminal on macOS/Debian, Git Bash or PowerShell on Windows 11) and set your global username and email. This is the identity stamped onto your commits. Make sure you use the same email address that you used to register for your GitLab or GitHub account.

    ``` bash
    git config --global user.name "Your Name"
    git config --global user.email "your.email@example.com"
    ```

1. Register for an account on the **GitLab** or **GitHub** cloud instance you will use. If you have already registered, you can skip this step.

{% if is_surrey %}
    !!! Info "University of Surrey GitLab"
        For the University of Surrey, you will be using the GitLab instance provided by the university at [https://gitlab.surrey.ac.uk](https://gitlab.surrey.ac.uk). When you get to the login page, select the button **Surrey Login**{: .bg-grey} and use your university credentials.
{% endif %}

1. Now we need to generate ssh keys to use for authentication with your GitLab or GitHub account. Follow the instructions below to generate a new SSH key pair and add it to your GitLab or GitHub account. It's best practice to use modern, secure `ed25519` keys and create separate ones for GitHub and GitLab.

    <div class="grid cards one-column" markdown>
    
    -   :material-clock-fast:{ .lg .middle } __Generate ssh keys__

        === "macOS using Homebrew"

            1. Open the **Terminal** application.
            2. Run the following command to generate a new SSH key pair for GitHub and GitLab. Make sure to replace `your.gitxxx.email@example.com` with your actual email address:
            
                ``` bash
                ssh-keygen -t ed25519 -C "your.github.email@example.com" -f ~/.ssh/id_ed25519_github
                ssh-keygen -t ed25519 -C "your.gitlab.email@example.com" -f ~/.ssh/id_ed25519_gitlab
                ```
            3. When prompted, type a strong passphrase.

        === "Windows 11 using PowerShell"

            1. Open the **PowerShell** application.
            2. Run the following command to generate a new SSH key pair for GitHub and GitLab. Make sure to replace `your.gitxxx.email@example.com` with your actual email address:
            
                ``` powershell
                ssh-keygen -t ed25519 -C "your.github.email@example.com" -f $env:USERPROFILE\.ssh\id_ed25519_github
                ssh-keygen -t ed25519 -C "your.gitlab.email@example.com" -f $env:USERPROFILE\.ssh\id_ed25519_gitlab
                ```
            3. When prompted, type a strong passphrase.
            
        === "Linux (Ubuntu/Debian) using bash"
            1. Open the **Terminal** application.
            2. Run the following command to generate a new SSH key pair for GitHub and GitLab. Make sure to replace `your.gitxxx.email@example.com` with your actual email address:
            
                ``` bash
                ssh-keygen -t ed25519 -C "your.github.email@example.com" -f ~/.ssh/id_ed25519_github
                ssh-keygen -t ed25519 -C "your.gitlab.email@example.com" -f ~/.ssh/id_ed25519_gitlab
                ```
            3. When prompted, type a strong passphrase.
    
    </div>

1. Then configure the SSH Config file to use the correct SSH key for each service. Open the SSH config file in your preferred text editor (create it if it doesn't exist) and add the following lines:

    For example using `nano` on macOS or Linux:

    ```bash
    nano ~/.ssh/config
    ```
    
    paste the following configuration into the file:

    ```text
    # GitLab
    Host gitlab.com
        HostName gitlab.com
        User git
        IdentityFile ~/.ssh/id_ed25519_gitlab


    # GitHub
    Host github.com
        HostName github.com
        User git
        IdentityFile ~/.ssh/id_ed25519_github
    ```

    then save and close the file (`Ctrl+O` to save and `Ctrl+X` to exit in nano). On Windows, you can use `Notepad` or any text editor to create the `config` file in the `.ssh` directory.

    Make sure to replace the paths with the correct paths to your SSH keys if you used different names or locations.

1. Set the correct permissions for the SSH config file and the private keys to ensure they are secure. If you are using macOS or Linux, run the following commands in your terminal:

    ```bash
    chmod 600 ~/.ssh/config
    chmod 600 ~/.ssh/id_ed25519_github
    chmod 600 ~/.ssh/id_ed25519_gitlab
    ```

    Windows handles permissions differently and are normally set to only allow access to the user, but ensure that the private keys aren't accessible to other users.

1. Test the SSH connection to GitHub and GitLab to ensure that the keys are working correctly. Run the following commands in your terminal:

    ```bash
    ssh -T git@github.com
    ssh -T git@gitlab.com
    ```
    If successful, you will see greetings like:

    ```text
    Hi username! You've successfully authenticated, but GitHub does not provide shell access.
    Welcome to GitLab, @username!
    ```

1. You have set a password for the ssh keys and you will be prompted for the password each time you use the key. To avoid this, you can use an SSH agent to cache your passphrase. Follow the instructions below to start the SSH agent and add your keys.

    <div class="grid cards one-column" markdown>
    
    -   :material-clock-fast:{ .lg .middle } __Adding ssh keys__

        === "macOS using Homebrew"

            1. Add your SSH private keys to the already running ssh agent:
        
                ``` bash
                ssh-add ~/.ssh/id_ed25519_github
                ssh-add ~/.ssh/id_ed25519_gitlab
                ```

        === "Windows 11 using PowerShell"

            1. Start the SSH agent in the background and set it to start automatically with Windows:
        
                ``` powershell
                Start-Service ssh-agent
                Set-Service -Name ssh-agent -StartupType Automatic
                ```
            2. Add your SSH private keys to the agent:
        
                ``` powershell
                ssh-add $env:USERPROFILE\.ssh\id_ed25519_github
                ```

        === "Linux (Ubuntu/Debian) using bash"

            1. Add your SSH private keys tto the already running ssh agent:
        
                ``` bash
                ssh-add ~/.ssh/id_ed25519_github
                ssh-add ~/.ssh/id_ed25519_gitlab
                ```
    </div>

!!! Note "Essential Practice Moving Forward"
    When cloning repositories from now on, always use the SSH address, never the HTTPS address.

    * **Use:** `git clone git@github.com:username/repo.git`
    * **Avoid:** `https://github.com/username/repo.git`

### Integrate Visual Studio Code with Git

1. Once the keys are generated and the configuration is complete, now add the SSH keys to the GitHub and GitLab accounts. Follow the instructions below to add your SSH keys to your GitHub and GitLab accounts.

    <div class="grid cards one-column" markdown>
    
    -   :material-clock-fast:{ .lg .middle } __Integrate Visual Studio Code with Git__

        === "GitLab"

            1. Log in to your **GitLab** account in a web browser.
            2. In the top-right corner, click on your **profile avatar** and select **Edit profile**.
            3. On the left-hand sidebar, select **Access > SSH Keys**.
            4. Click **Add new key**{: .bg-blue} and fill out the following details:
                * **Title:** Give it a clear name (e.g., VS Code Extension).
                * **Key:** Paste the contents of your public SSH key file (e.g., `~/.ssh/id_ed25519_gitlab.pub`).
            5. Click **Add key**{: .bg-blue} to save the key.

        === "GitHub"

            1. Log in to your **GitHub** account in a web browser.
            2. In the top-right corner, click on your **profile avatar** and select **Settings**.
            3. On the left-hand sidebar, select **SSH and GPG keys**.
            4. Click **New SSH key**{: .bg-green} and fill out the following details:
                * **Title:** Give it a clear name (e.g., VS Code Extension).
                * **Key:** Paste the contents of your public SSH key file (e.g., `~/.ssh/id_ed25519_github.pub`).
            5. Click **Add SSH key**{: .bg-green} to save the key.

    </div>

## Fork and cloning the doc-template

Forking the documentation template creates a copy of the template into your own GitLab or GitHub cloud account. You will then be able to edit the template locally in Visual Studio Code and publish your own documentation website.

Cloning the documentation template creates a local copy of the template on your computer. You will then be able to edit the template locally in Visual Studio Code and publish your own documentation website.

<br>
<p class="text-center-italic">
Table 7.3-1: Fork and Clone Comparison at a Glance
</p>
| Feature | Fork | Clone |
|----|----|---|
| Where's the copy made? | On the remote host (GitHub / GitLab) | On your local computer |
| Is it a Git command? | No (It's a web platform feature) | Yes (git clone `<url>`) |
| Who owns the target? | You (it's copied to your account) | You (it's on your machine) |
| Can you push to it? | Yes | Yes (if you have write access to the remote source) |
| Primary purpose | To propose changes to a project you don't own | To actually do development work, write code, and make commits |

The features of forking and cloning are complementary. You can fork a repository to create your own copy on the remote host, and then clone that fork to your local machine to work on it. The standard workflow is:

1. **Fork:** You find a project on GitHub. You click the Fork button on the website. Now, you have a copy at `github.com/your-username/project`.
2. **Clone:** You run `git clone https://github.com/your-username/project.git` in your terminal. Now, the code is on your laptop.
3. **Work:** You write code, make local commits, and test your changes.
4. **Push:** You run `git push origin main` to send your local changes back up to your cloud fork.
5. **Pull Request:** You go back to the GitHub website and open a Pull Request, asking the original project owner to pull the changes from your fork into their original repository.

!!! Note
    In this case, you will be creating your own documentation website, so you won't be submitting a pull request to the original repository. You will be working on your own forked copy of the documentation template.

### Fork the doc-template

You may already have a GitLab or GitHub repository containing a Zensical template provided for you. If you do, you can skip this section and go to the next section to clone the repository locally.

<!-- Point the user to the correct repository based on whether they are using Surrey GitLab or GitHub. -->
{% if is_surrey %}
1. Start with opening up a browser and go to the [doc-template repository](https://gitlab.surrey.ac.uk/mb0105/doc-template){target="_blank"} on the University of Surrey GitLab.
{% else %}
1. Start with opening up a browser and go to the [doc-template repository](https://github.com/buckwem/doc-template){target="_blank"} on GitHub.
{% endif %}

2. Next, fork the documentation template to create a copy of the template in your own Git cloud account. Follow the instructions below to fork the repository.

    <div class="grid cards one-column" markdown>
    
    -   :material-clock-fast:{ .lg .middle } __Fork the documentation template__

        {% if is_surrey %}
        === "GitLab"

            1. Click on the link to [fork a copy of the documentation template](https://gitlab.surrey.ac.uk/mb0105/doc-template/-/forks/new){target="_blank"} to create a copy of the template for your use.
            
                ![Image title](images/gitlab-fork-project.png){ width=70% }
                /// caption
                Figure 7.3.1-1: GitLab fork project
                ///
           
            3. Enter your *Project name* using to the format the coursework specifies. For example, for coursework 1 for the module COMM058 in the year 2026 for your GitLab ID az1234, enter 'cw1-az1234' in the project name field. Edit the *Project slug* to match the project name. Use all lowercase and a dash between words with no spaces.
            4. Then select the project namespace for the module as directed by your course tutor.
            5. Change the *Visibility Level* to *Private*.
            6. Press the button **Fork Project**{: .bg-blue} to create your own copy of the project in the group namespace.
        
        {% endif %}

        === "GitHub"

            xxx

    </div>

!!! Warning
    Don't forget to set the visibility to private, otherwise others can see your repository. Ask someone else to check whether they can see your repository.

### Clone the doc-template

This section takes you through the steps to clone the documentation template into your own local device. You will then be able to edit the template locally in Visual Studio Code and eventually publish your own documentation website.

1. Start with creating a directory for all your *GitLab* or *GitHub* projects on your local desktop. For example, create a directory called 'GitLab' in your OneDrive directory..
    
    !!! Tip
        Using OneDrive will give you an additional backup of your GitLab repository.

1. Open a terminal (Terminal on macOS/Debian, Git Bash or PowerShell on Windows 11) and navigate to the directory you created in the previous step.

1. Then run the following command to clone the documentation template into your local directory. Replace the `git_website` with the actual GitLab or GitHub website address. For example, `gitlab.com` or `github.organisation.com`. Make sure to replace the `username` with your actual GitLab or GitHub username.

    ``` bash
    git clone git@git_website:username/doc-template.git
    ```

    !!! Tip
        You can find your `username` by logging into your GitLab or GitHub account and clicking on your profile picture at the top right corner of the page. On **GitLab** your username will is **below** your name in the dropdown menu. On **GitHub** your username will is **above** your name in the dropdown menu.

## Install Python and Zensical

First we need to install Python. I've written brief instructions below for macOS, Windows 11, and Linux (Ubuntu/Debian). You are also recommended to refer to the [official Python installation documentation](https://docs.python.org/3/using/) for your operating system. 

If you already have Python installed, you can check the version by running the following command in your terminal or command prompt:
```bash
python --version
```

The instructions below are for installing Python 3.8 or later. If you have an older version, please update to Python 3.8 or later.


<div class="grid cards one-column" markdown>
    
-   :material-clock-fast:{ .lg .middle } __Install Python and Zensical__

    === "macOS - Terminal"

        1. Install python using the Homebrew package manager. If you don't have Homebrew installed, you can install it by following the instructions on the [Homebrew website](https://brew.sh/).
        
            ``` bash
            brew install python
            ```
        
        2. Open *Terminal* and run the following commands to create a virtual environment and install Zensical:

            ```bash
            # 1. Create the virtual environment
            python3 -m venv .venv

            # 2. Activate it
            source .venv/bin/activate

            # 3. Install Zensical
            pip install zensical
            ```

    === "Windows 11 - PowerShell"

        1. Download and run the official python installer from the [python.org](https://www.python.org/downloads/).
        1. Open *PowerShell* as an Administrator in your project folder and run:

            !!! Critical
                Make sure to check the box that says "Add Python to PATH" during the installation process. This will allow you to run Python from the command line. 

            ```PowerShell
            # 1. Create the virtual environment
            python -m venv .venv

            # 2. Activate it (Choose the line matching your terminal)
            .\.venv\Scripts\Activate.ps1     # <-- Use this if you are in PowerShell
            .\.venv\Scripts\activate.bat     # <-- Use this if you are in classic CMD

            # 3. Install Zensical inside the environment
            pip install zensical
            ```

    === "Linux - Ubuntu/Debian"

        1. Download the `.deb` package from the [official website](https://code.visualstudio.com/).
        2. Open a terminal and navigate to the directory where you downloaded the `.deb` package.
        3. Run the following command to install Visual Studio Code:

            ``` bash
            # 1. Create the virtual environment
            python -m venv .venv

            # 2. Activate it (Choose the line matching your terminal)
            .\.venv\Scripts\Activate.ps1     # <-- Use this if you are in PowerShell
            .\.venv\Scripts\activate.bat     # <-- Use this if you are in classic CMD

            # 3. Install Zensical inside the environment
            pip install zensical
            ```

            Replace `<file>` with the name of the downloaded `.deb` file.

    </div>
Further installation instructions are available on the [Visual Studio Code website](https://code.visualstudio.com/docs/setup/linux){target="_blank"}.

### Install Zensical Studio plugin

1. Install [Zensical Studio Code Extension](https://marketplace.visualstudio.com/items?itemName=zensical.zensical-studio){target="_blank"} plugin for Visual Studio Code from the marketplace. This extension provides a set of tools to help you work with Zensical projects, including commands to build and preview your site.

    Follow the instructions on the Zensical Studio plugin page to configure the extension. Add to the `.vscode/settings.json` file in your project directory the following lines:

    ```json
    {
      "files.associations": {
        "*.md": "python-markdown"
      }
    }
    ```


There are many other extensions available for Visual Studio Code that can help you with your documentation. You can explore the [Visual Studio Code Marketplace](https://marketplace.visualstudio.com/vscode){target="_blank"} to find more extensions that suit your needs.

<!--
Some useful extensions for documentation are documented in the section [Install extensions][install-extensions] in the Zensical documentation.
-->