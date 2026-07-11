---
icon: lucide/book-open
---

<!-- 
# Copyright (c) 2025-2026 Mark Buckwell, Zensical and contributors
# SPDX-License-Identifier: MIT
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

## References and bibliography

Zensical doesn't include a dedicated citation or bibliography extension, but you can build a simple one using a references page.

!!! info "How the PDF handles this"
    Python-Markdown's [attribute list](https://zensical.org/docs/authoring/formatting/#attribute-lists) extension - used below - is understood natively by the live website, but this template's PDF is built by [Pandoc](https://pandoc.org/), which has no idea what a standalone `{: #id }` line means and would otherwise leave it sitting in the output as literal, visible text. `build_pdf.py` automatically rewrites each entry into an equivalent raw HTML `<p>` tag before handing the page to Pandoc (see `convert_reference_attr_list_paragraphs` in `build_pdf.py`), so you can write plain attr_list Markdown below and both outputs render correctly - no manual HTML needed.

1. Create a page for your sources (this template includes one at [`docs/references.md`](../references.md)). List each source as a paragraph, and give it a short, unique id using attr_list syntax on the line directly below it (no heading needed - attr_list works on plain paragraphs too):

    ``` markdown
    Skoulikari, A. (2023) *Learning Git: A Hands-On and Visual Guide to the Basics of Git*. Sebastopol, CA: O'Reilly Media.
    {: #skou2023 .reference }
    ```

    Each entry needs a blank line before and after it - attr_list only recognises `{: ... }` as an id (rather than literal visible text) when it's the last line of its own paragraph, and `build_pdf.py`'s conversion for the PDF relies on that same boundary. Removing the blank lines to save space merges entries into one paragraph and breaks both outputs.

2. Add the page to `nav` in `zensical.toml` so it appears in the sidebar, and gets a number like your other sections.
3. Cite the source in-text by linking to that paragraph's id, wrapping the link in an extra pair of square brackets so it reads like an in-text citation:

    ``` markdown
    Git is a tool used to manage version control.[[Skoulikari, 2023](references.md#skou2023)]
    ```

    Which renders as: Git is a tool used to manage version control.[[Skoulikari, 2023](../references.md#skou2023)]

    (The path here is `../references.md` rather than `references.md` because this page lives in `docs/starthere/` - from `docs/section1.md` itself, `references.md` is correct, as shown in the code block above.)

    !!! warning
        In-text citation links like this resolve correctly on the website, but internal cross-page links generally don't resolve to the right place within the built PDF (a pre-existing limitation of this template's Pandoc-based PDF pipeline, not specific to references) - the link ends up pointing at a local file path rather than jumping to the anchor.

4. Consecutive entries get the browser's normal spacing between paragraphs by default - noticeably looser than a typical bibliography. Give each entry's attr_list line a `.reference` class alongside its id (as shown in the code block above) so the template's layout rules - described next - can target them.

5. Set `project.extra.reference_style` in `zensical.toml` to control how `.reference` entries are laid out, on both the website and the PDF build:

    ``` toml
    [project.extra]
    reference_style = "european" # or "global"
    ```

    * `"european"` (the default) - single line spacing throughout, no indent, entries close together. Implemented by [`docs/stylesheets/extra.css`](../stylesheets/extra.css)'s `.md-typeset p.reference + p.reference` rule on the website.
    * `"global"` - single line spacing within each entry, double spacing between entries, with a 0.5in/1.27cm hanging indent on wrapped lines (the common APA/MLA/Chicago style). Implemented by the `reference_style()` macro (see `macros.py`), called once near the top of the references page - `{{ reference_style() }}` - which injects an overriding `<style>` block only when `"global"` is set.

    !!! warning "The website and PDF need separate CSS for this"
        Pandoc's HTML output for the PDF has no `.md-typeset` wrapper element at all, so any `.md-typeset`-prefixed selector - including the default `.reference` rule above - silently matches nothing there. `build_pdf.py` reads the same `reference_style` setting and writes the equivalent plain `.reference` (no `.md-typeset` prefix) CSS directly into the PDF's compiled stylesheet instead. If you adjust the spacing/indent values, update both `docs/stylesheets/extra.css` and the matching block in `build_pdf.py` (search for `reference_style_css`) to keep the website and PDF in sync.

!!! tip
    Keep ids short and stable (e.g. `skou2023`, author surname plus year) so citations keep working even if you reorder entries on the references page later. If a page citing a source is nested in a subdirectory, adjust the relative path to `references.md` accordingly.

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
