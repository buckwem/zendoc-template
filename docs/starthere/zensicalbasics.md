---
icon: lucide/book-open
---

<!-- 
# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT
# All contributions are certified under the DCO
-->

{{ heading_counter_reset(page) }}

# Zensical basics

Zensical is the static site generator that powers this template: it turns the Markdown files under `docs/` into the website you're reading now, and (via `build_pdf.py`) into the single-file PDF version of your document. It reads its configuration from `zensical.toml`, extends Markdown with the authoring features shown below (admonitions, tabs, diagrams, maths, and more), and lets you preview your changes locally with `zensical serve` before publishing.

This page is a quick reference for the Markdown extensions you're most likely to use while writing your document, each with a live example. For the underlying, general-purpose Markdown syntax these extensions build on (headings, links, bold/italic text, and so on), see [Markdown basics](markdown.md). For full documentation on Zensical itself, visit [zensical.org](https://zensical.org/docs/).

## Commands

Zensical provides a command line interface (CLI) to create, build, and serve your documentation. The following commands are available:

* [`zensical new`][new] - Create a new project
* [`zensical serve`][serve] - Start local web server
* [`zensical build`][build] - Build your site

  [new]: https://zensical.org/docs/usage/new/
  [serve]: https://zensical.org/docs/usage/preview/
  [build]: https://zensical.org/docs/usage/build/

## Examples

Some examples of Zensical syntax are below. For full documentation visit [zensical.org](https://zensical.org/docs/).

### Lists within lists

Markdown supports nested lists by indenting the inner list by four spaces. This is an implementation-specific feature of Python Markdown used by Zensical, and isn't part of the original Markdown specification.

!!! warning "The Four Space Rule"

    If you are nesting Tabs, Admonitions, or Code Blocks inside a list, you must indent by exactly 4 spaces. If your ordered list numbering resets to "1", check your indentation! Further background information is on the [Zensical authoring section](https://zensical.org/docs/authoring/markdown/).

### Admonitions

Zensical supports admonitions, that highlight blocks of content to draw attention to important information. Admonitions are available for notes, warnings, tips, and more. For further details, go to the [admonitions documentation](https://zensical.org/docs/authoring/admonitions/).

!!! note

    This is a **note** admonition. Use it to provide helpful information.

!!! warning

    This is a **warning** admonition. Be careful!

### Details

Zensical supports collapsible blocks using the `???` syntax. This is useful for hiding content until the user clicks to expand it. For further details, go to the [admonitions collapsible blocks documentation](https://zensical.org/docs/authoring/admonitions/#collapsible-blocks).

??? info "Click to expand for more info"
    
    This content is hidden until you click to expand it.
    Great for FAQs or long explanations.

## Code blocks

Zensical supports fenced code blocks with syntax highlighting. You can specify the language for syntax highlighting by adding the language name after the opening backticks. For further details, go to the [code blocks documentation](https://zensical.org/docs/authoring/code-blocks/).

``` python hl_lines="2" title="Code blocks"
def greet(name):
    printf("Hello, {name}!") # (1)!

greet("Python")
```

1.  Go to [code annotations documentation](https://zensical.org/docs/authoring/code-blocks/#code-annotations)

    Code annotations enable attaching of notes to lines of code.

You can also highlight code inline: `#!python print("Hello, Python!")`.

## Content tabs

Zensical supports content tabs, which enables you to present different content in the same space. This is useful for showing code examples in multiple programming languages. For further details, go to the [content tabs documentation](https://zensical.org/docs/authoring/content-tabs/).

=== "Python"

    ``` python
    print("Hello from Python!")
    ```

=== "Rust"

    ``` rs
    println!("Hello from Rust!");
    ```

## Images

Zensical supports Markdown image syntax using the `<figure>` tag to add captions. For further details, go to the [images documentation](https://zensical.org/docs/authoring/images/).

<figure markdown="span">
  ![Image title](https://dummyimage.com/600x400/){ width="300" }
  <figcaption>Image caption</figcaption>
</figure>

## Diagrams

Zensical supports [Mermaid](https://mermaid.js.org/){target="_blank"} diagrams. You can create flowcharts, sequence diagrams, and more. For further details, go to the [diagrams documentation](https://zensical.org/docs/authoring/diagrams/).

{% if is_surrey %}
!!! note
    The COMM058 Architectural Thinking for Security module doesn't use any of these documentation types. It's better that you use draw.io to create your diagrams and export them as images to include in your documentation. Use the downloadable version of draw.io, not the web version, as it's much easier to edit. Also, if you use draw.io in your working life, your company may have a policy against using cloud services unless they're a paid, approved service for hosting confidential company data.
{% endif %}

``` mermaid
graph LR
  A[Start] --> B{Error?};
  B -->|Yes| C[Hmm...];
  C --> D[Debug];
  D --> B;
  B ---->|No| E[Yay!];
```

## Footnotes

Zensical supports footnotes, which enables you to add references or additional information without cluttering the main text. You can create a footnote by using the `[^1]` syntax. For further details, go to the [footnotes documentation](https://zensical.org/docs/authoring/footnotes/).
  

Here's a sentence with a footnote.[^1]

Hover it, to see a tooltip.

[^1]: This is the footnote.

## Formatting

Zensical supports various formatting options, including bold, italics, and strikethrough. You can also create headings, blockquotes, and horizontal rules. For further details, go to the [formatting documentation](https://zensical.org/docs/authoring/formatting/).

- ==This was marked (highlight)==
- ^^This was inserted (underline)^^
- ~~This was deleted (strikethrough)~~
- H~2~O
- A^T^A
- ++ctrl+alt+del++

## Icons, emojis

Zensical supports icons and emojis. You can use the `:icon-name:` syntax to add icons from the [Lucide](https://lucide.dev/){target="_blank"} icon set, or use standard emoji codes. For further details, go to the [icons and emojis documentation](https://zensical.org/docs/authoring/icons-emojis/).

* :sparkles: `:sparkles:`
* :rocket: `:rocket:`
* :tada: `:tada:`
* :memo: `:memo:`
* :eyes: `:eyes:`

## Maths

Zensical supports mathematical notation using [MathJax](https://www.mathjax.org/){target="_blank"}. You can write inline math using the `$...$` syntax, and display math using the `$$...$$` syntax. For further details, go to the [math documentation](https://zensical.org/docs/authoring/math/).

$$
\cos x=\sum_{k=0}^{\infty}\frac{(-1)^k}{(2k)!}x^{2k}
$$

!!! warning "Needs configuration"
    This page includes MathJax via a `script` tag, but the generated default
    configuration doesn't enable it everywhere, to avoid loading it on pages
    that don't need it. See the documentation for details on how to configure
    it on all your pages if they're more maths-heavy than these simple
    starter pages.

<script id="MathJax-script" async src="https://unpkg.com/mathjax@3/es5/tex-mml-chtml.js"></script>
<script>
  window.MathJax = {
    tex: {
      inlineMath: [["\\(", "\\)"]],
      displayMath: [["\\[", "\\]"]],
      processEscapes: true,
      processEnvironments: true
    },
    options: {
      ignoreHtmlClass: ".*|",
      processHtmlClass: "arithmatex"
    }
  };
</script>

## Task lists

Zensical supports task lists, which allow you to create checklists with checkboxes. You can create a task list by using the `- [ ]` syntax for an unchecked item and `- [x]` for a checked item. For further details, go to the [task lists documentation](https://zensical.org/docs/authoring/lists/#using-task-lists).

* [x] Install Zensical
* [x] Configure `zensical.toml`
* [x] Write amazing documentation
* [ ] Deploy anywhere

## Tooltips

Zensical supports tooltips, which allow you to add additional information that appears when the user hovers over a specific element. You can create a tooltip by using the `[text][example]` syntax. For further details, go to the [tooltips documentation](https://zensical.org/docs/authoring/tooltips/).

[Hover over this text][example]

  [example]: https://example.com "I'm a tooltip!"

## Where to go next

Continue to [Customisation](customise.md) to change this template's branding, restructure your document's pages, and customise the cover page and PDF layout.
