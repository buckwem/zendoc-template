---
icon: lucide/book-open
---

<!-- 
# Copyright (c) 2025-2026 Mark Buckwell and contributors
# SPDX-License-Identifier: MIT
# All contributions are certified under the DCO
-->

<style>
  /* Reset the page and sidebar to start at 5 */
  .md-typeset { counter-reset: h1-count 4 !important; }
  .md-nav--primary { counter-reset: toc1 5 !important; }
  /* Also change the numbering of the overall title number in the sidebar by editing zensical.toml */
</style>

# Markdown basics

Markdown is a lightweight markup language that enables you to format plain text using a simple syntax. It's easy to read and easy to write, eventually converting into structurally valid HTML, and is widely used for documentation, readme files, and content management systems. It enables you to focus on writing without worrying about complex formatting, making it an ideal choice for collaborative documentation projects.

It's text-based, meaning you can use a text editor to create and edit Markdown files. This makes it highly portable and compatible with version control systems like Git, enabling collaborative editing and tracking of changes over time. Plain text files with the `.md` extension store the Markdown. You can then share, version, and convert these files into HTML for web publishing.

Here is a summary of the most common formatting elements you'll use in a `.md` file.

## Headers

Add hash signs (#) before your text to create a heading. The number of hashes corresponds to the heading level.

```
# H1 Header
## H2 Header
### H3 Header
#### H4 Header
##### H5 Header
###### H6 Header
```

## Text formatting

You can make text bold, italic, or both to add emphasis without needing complex menus.

```
**bold text**
*italic text*
***bold and italic***
~~strikethrough~~
`inline code`
```

## Links and images

The syntax for these is similar. Just add an exclamation mark at the beginning for an image.

```
[Link text](https://example.com)
[Link with title](https://example.com "Hover title")
![Alt text](image.jpg)
![Image with title](image.jpg "Image title")
```

## Lists

Markdown handles both ordered (numbered) and unordered (bulleted) lists.

### Unordered lists

Use a minus sign (-), asterisk (*), or plus sign (+).

```
- Item 1
- Item 2
  - Nested item
```

### Ordered lists

Simply use numbers followed by a period.

```
1. First item
2. Second item
3. Third item
```

## Code blocks

Markdown is a favorite for developers because of how it handles code snippets.

* Inline Code: Wrap text in backticks: `code`.
* Code Blocks: Wrap multiple lines in "fences" using three backticks (```). You can often specify the language for syntax highlighting.

````
```javascript
function hello() {
  console.log("Hello, world!");
}
```
````

## Tables

Use pipes `|` and hyphens `-` to create tables. The second row defines the alignment using colons.

```
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Row 1    | Data     | Data     |
| Row 2    | Data     | Data     |
```

## Horizontal rule
```
---
or
***
or
___
```

## Task lists
```
- [x] Completed task
- [ ] Incomplete task
- [ ] Another task
```

## Blockquotes and rules

To highlight quotes or separate sections:

* **Blockquote:** Use the `>` symbol before the text to create a callout or quote.
```
> This is a blockquote
> Multiple lines
>> Nested quote
```

* **Horizontal Rule** Use three dashes `---` on a line by themselves to create a thematic break.


## Quick tips

* **Line Breaks:** To create a line break without a new paragraph, end a line with two or more spaces before hitting enter.

* **Escaping Characters:** If you want to show a literal character (like a *) without it formatting the text, use a backslash: `\*`.