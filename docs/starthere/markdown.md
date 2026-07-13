---
icon: lucide/book-open
---

<!-- 
# Copyright (c) 2025-2026 Mark Buckwell and contributors
# SPDX-License-Identifier: MIT
-->

{{ heading_counter_reset(page) }}


# Markdown basics

[Markdown](https://www.markdownguide.org/){target="_blank"} is a lightweight markup language that enables you to format plain text using a simple syntax. It's easy to read and easy to write, eventually converting into structurally valid HTML, and is widely used for documentation, readme files, and content management systems. It enables you to focus on writing without worrying about complex formatting, making it an ideal choice for collaborative documentation projects.

It's text-based, meaning you can use a text editor to create and edit Markdown files. This makes it highly portable and compatible with version control systems like Git, enabling collaborative editing and tracking of changes over time. Plain text files with the `.md` extension store the Markdown. You can then share, version, and convert these files into HTML for web publishing.

Below is a summary of the most common formatting elements you'll use in a `.md` file.

!!! Note "Zensical Markdown"

    Zensical uses a flavour of Markdown called [Python Markdown](https://python-markdown.github.io/){target=_blank} with some extensions. This ensures that your Markdown files are compatible with a wide range of tools and platforms, while also providing additional features for enhanced formatting and functionality. There are some differences between Zensical Markdown and other flavours of Markdown, so it's important to refer to the [Zensical documentation](https://zensical.org/docs/authoring/markdown/){target=_blank} for details.

!!! Tip "Markdown Live Preview"
    You can use the [Markdown Live Preview](https://markdownlivepreview.com/){target=_blank} website to see how your Markdown will look when rendered. This is a great way to check your formatting and make adjustments as needed.

## Headings

Add hash signs (#) before your text to create a heading. The number of hashes corresponds to the heading level.

```
# H1 Heading
## H2 Heading
### H3 Heading
#### H4 Heading
##### H5 Heading
###### H6 Heading
```

The [`toc`](https://python-markdown.github.io/extensions/toc/){target="_blank"} extension automatically turns every heading into a linkable anchor (the `¶` symbol you can see next to each heading on this page), and generates the sidebar and table of contents from them. The [`attr_list`](https://python-markdown.github.io/extensions/attr_list/){target="_blank"} extension lets you override the generated anchor or add a CSS class, by adding an attribute block after the heading text, for example `## Heading {: #custom-id }`.

!!! warning
    As covered in [Customisation](customise.md#customise-doc-structure), each page in this template can contain only one heading 1 (`#`) - it's what drives the automatic chapter/section numbering (e.g. "9.1") across the whole document. Start a new page instead of adding a second heading 1 to this one.

## Text formatting

You can make text bold, italic, or both to add emphasis without needing complex menus.

```
**bold text**
*italic text*
***bold and italic***
~~strikethrough~~
`inline code`
```

The [`pymdownx.betterem`](https://facelessuser.github.io/pymdown-extensions/extensions/betterem/){target="_blank"} extension handles bold and italic emphasis, and is more consistent about nested and mixed emphasis (for example `**bold _and italic_**`) than plain [Python Markdown](https://python-markdown.github.io/){target="_blank"}. Strikethrough isn't part of core Markdown at all - the [`pymdownx.tilde`](https://facelessuser.github.io/pymdown-extensions/extensions/tilde/){target="_blank"} extension provides it here. That same extension also enables subscript (`H~2~O`), and the paired [`pymdownx.caret`](https://facelessuser.github.io/pymdown-extensions/extensions/caret/){target="_blank"} extension enables superscript (`A^T^A`) and underline (`^^text^^`). See [Formatting](zensicalbasics.md#formatting) in Zensical basics for these and other extended styles, such as highlighting text and keyboard keys.

## Links and images

The syntax for these is similar. Just add an exclamation mark at the beginning for an image.

```
[Link text](https://example.com)
[Link with title](https://example.com "Hover title")
[Reference-style link][example-ref]
![Alt text](image.jpg)
![Image with title](image.jpg "Image title")

[example-ref]: https://example.com "Hover title"
```

The [`attr_list`](https://python-markdown.github.io/extensions/attr_list/){target="_blank"} extension lets you attach HTML attributes to a link or image by adding a `{: ... }` block straight after it, with no space:

```
[Link text](https://example.com){: .external-link }
```

This template uses that same syntax with a `target="_blank"` attribute throughout, to make external links (like the ones on this page) open in a new browser tab on the website. `build_pdf.py` strips those attributes back out for the PDF, since "open in a new tab" has no meaning in a printed document.

The [`pymdownx.magiclink`](https://facelessuser.github.io/pymdown-extensions/extensions/magiclink/){target="_blank"} extension also auto-links bare URLs (`https://example.com` becomes a clickable link with no `[]()` needed) and recognises shorthand references to GitHub/GitLab issues, pull requests, and commits.

## Lists

Markdown handles ordered (numbered), unordered (bulleted), and definition lists.

### Unordered lists

Use a minus sign (-), asterisk (*), or plus sign (+).

```
- Item 1
- Item 2
    - Nested item
```

### Ordered lists

Simply use numbers followed by a period. [Python Markdown](https://python-markdown.github.io/){target="_blank"} renumbers the list for you based on the *first* number used, so `1.` for every item (or repeating the same number) is a common way to avoid manually renumbering items as you edit.

```
1. First item
2. Second item
3. Third item
```

### Definition lists

The [`def_list`](https://python-markdown.github.io/extensions/definition_lists/){target="_blank"} extension adds definition lists: a term on its own line, followed by one or more indented lines starting with a colon.

```
Term
:   Definition of the term, indented under it.

Second term
:   First definition.
:   A second definition for the same term.
```

## Code blocks

Markdown is a favourite for developers because of how it handles code snippets. This template uses the [`pymdownx.superfences`](https://facelessuser.github.io/pymdown-extensions/extensions/superfences/){target="_blank"} extension for fenced code blocks (in place of Python Markdown's more limited built-in [`fenced_code`](https://python-markdown.github.io/extensions/fenced_code_blocks/){target="_blank"}), together with [`pymdownx.highlight`](https://facelessuser.github.io/pymdown-extensions/extensions/highlight/){target="_blank"} and [`pymdownx.inlinehilite`](https://facelessuser.github.io/pymdown-extensions/extensions/inlinehilite/){target="_blank"} for syntax highlighting.

* Inline code: wrap text in backticks: `code`.
* Code blocks: wrap multiple lines in "fences" using three backticks (```). Add the language name straight after the opening fence for syntax highlighting.

````
```javascript
function hello() {
  console.log("Hello, world!");
}
```
````

[`pymdownx.superfences`](https://facelessuser.github.io/pymdown-extensions/extensions/superfences/){target="_blank"} also lets you nest fenced code blocks inside other Markdown structures such as lists and admonitions, and supports custom fence types - the Mermaid diagrams in [Diagrams](zensicalbasics.md#diagrams) are a fenced ` ```mermaid ` block rather than plain code. For line highlighting, titled code blocks, and inline code with syntax highlighting, see [Code blocks](zensicalbasics.md#code-blocks) in Zensical basics.

## Tables

Use pipes `|` and hyphens `-` to create tables. The [`tables`](https://python-markdown.github.io/extensions/tables/){target="_blank"} extension is what enables this - it isn't part of core [Python Markdown](https://python-markdown.github.io/){target="_blank"}. Add colons to the separator row to control column alignment.

```
| Left-aligned | Centred | Right-aligned |
|:-------------|:-------:|--------------:|
| Row 1        | Data    | Data          |
| Row 2        | Data    | Data          |
```

## Horizontal rule

Put three or more hyphens, asterisks, or underscores on their own line, surrounded by blank lines, to create a thematic break:

```
---
```

```
***
```

```
___
```

## Task lists

Task lists aren't part of core [Python Markdown](https://python-markdown.github.io/){target="_blank"} either - they're enabled by the [`pymdownx.tasklist`](https://facelessuser.github.io/pymdown-extensions/extensions/tasklist/){target="_blank"} extension, configured in this template to render as clickable checkboxes rather than plain `[x]`/`[ ]` text.

```
- [x] Completed task
- [ ] Incomplete task
- [ ] Another task
```

## Blockquotes

Use the `>` symbol before the text to create a callout or quote. Nest additional `>` symbols to quote within a quote.

```
> This is a blockquote
> Multiple lines
>> Nested quote
```

For structured callouts with an icon and title (notes, warnings, tips), use an admonition instead - see [Admonitions](zensicalbasics.md#admonitions) in Zensical basics.

## Quick tips

* **Line breaks:** To create a line break without starting a new paragraph, end a line with two or more spaces before hitting enter.

* **Escaping characters:** If you want to show a literal character (like a `*`) without it formatting the text, use a backslash: `\*`.

* **Attributes on any element:** The [`attr_list`](https://python-markdown.github.io/extensions/attr_list/){target="_blank"} extension used for links, images, and headings above works on most other Markdown elements too - for example adding a CSS class to a paragraph or list item with `{: .my-class }` directly after it.

## Where to go next

The syntax on this page works in any Markdown file, including plain README files on GitLab or GitHub. Continue to [Zensical basics](zensicalbasics.md) for the extensions that only work in this template's own Zensical-built pages - admonitions, content tabs, diagrams, and more.