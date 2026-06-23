---
icon: lucide/book-open
---

<style>
  /* Reset the page and sidebar to start at 4 */
  .md-typeset { counter-reset: h1-count 3 !important; }
  .md-nav--primary { counter-reset: toc1 4 !important; }
</style>

# Zensical basics {: .reset-heading-counter-2 }

Some brief Zensical notation is below. For full documentation visit [zensical.org](https://zensical.org/docs/).

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

Zensical supports nested lists. You can create a list within a list by indenting the inner list by 4 spaces.

!!! warning "The 4 Space Rule"

    If you are nesting Tabs, Admonitions, or Code Blocks inside a list, you must indent by exactly 4 spaces. If your ordered list numbering resets to "1", check your indentation!

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

!!! note

    The COMM058 Architectural Thinking for Security module does not use any of these documentation types.

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
    Note that MathJax is included via a `script` tag on this page and isn't
    configured in the generated default configuration to avoid including it
    in a pages that don't need it. See the documentation for details on how
    to configure it on all your pages if they're more maths-heavy than these
    simple starter pages.

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
