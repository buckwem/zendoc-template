---
icon: lucide/book-open
---

<!-- 
# Copyright (c) 2025-2026 Mark Buckwell and contributors
# SPDX-License-Identifier: MIT
# All contributions are certified under the DCO
-->

<style>
  /* Reset the page and sidebar to start at 3 */
  .md-typeset { counter-reset: h1-count 2 !important; }
  .md-nav--primary { counter-reset: toc1 3 !important; }
  /* Also change the numbering of the overall title number in the sidebar by editing zensical.toml */
</style>

# Install extensions


## Install vale

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
    
