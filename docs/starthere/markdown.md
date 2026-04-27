---
icon: lucide/book-open
---

<style>
  /* This page starts at 3 */
  .md-typeset {
    counter-reset: h1-count 2 !important; 
  }

  /* This specific page sidebar starts at 3 */
  .md-nav--primary {
    counter-reset: toc1 3 !important;
  }
</style>

# Markdown in 5min

Markdown is a lightweight markup language that allows you to format plain text using a simple syntax. It was designed to be easy to read and easy to write, eventually converting into structurally valid HTML.

Here is a summary of the most common formatting elements you’ll use in a .md file.

## Headers

Headings are created by adding hash signs (#) before your text. The number of hashes corresponds to the heading level.

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

The syntax for these is very similar; images just add an exclamation mark at the beginning for an image.

```
[Link text](https://example.com)
[Link with title](https://example.com "Hover title")
![Alt text](image.jpg)
![Image with title](image.jpg "Image title")
```

## Lists

Markdown handles both ordered (numbered) and unordered (bulleted) lists easily.

### Unordered Lists

Use a minus sign (-), asterisk (*), or plus sign (+).

```
- Item 1
- Item 2
  - Nested item
```

### Ordered Lists

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

Tables are created using pipes `|` and hyphens `-`. The second row defines the alignment using colons.

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

## Blockquotes and Rules

To highlight quotes or separate sections:

* **Blockquote:** Use the `>` symbol before the text to create a callout or quote.
```
> This is a blockquote
> Multiple lines
>> Nested quote
```

* **Horizontal Rule** Use three dashes `---` on a line by themselves to create a thematic break.


## Quick Tips

* **Line Breaks:** To create a line break without a new paragraph, end a line with two or more spaces before hitting enter.

* **Escaping Characters:** If you want to show a literal character (like a *) without it formatting the text, use a backslash: `\*`.