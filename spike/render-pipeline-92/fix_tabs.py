"""Spike preprocessing: fixes issues found feeding real Zensical-rendered
HTML straight to Pandoc, before the tabbed_set_filter.lua Lua filter can do
its job.

1. Tab labels: pymdownx.blocks.tab renders each tab's label as an inline
   <label for="__tabbed_N_M">TEXT</label> sibling inside a wrapping
   <div class="tabbed-labels">. Pandoc's HTML reader merges adjacent
   inline-level siblings with no block boundary between them into a single
   Plain block - by the time a Lua filter sees the parsed AST, all N labels
   have already collapsed into one unseparated run of text with no
   surviving boundary information. This can only be fixed here, on the raw
   HTML, before Pandoc's reader ever sees it: each <label> is rewritten as
   its own <p>, forcing Pandoc to treat it as a distinct block.
2. Page chrome noise: the "view source" button/icon and heading_counter_reset()'s
   inline <style> override aren't real content - stripped so they don't leak
   into the PDF as raw text/RawInline blocks.
3. TOC permalinks: python-markdown's toc extension appends a pilcrow (¶)
   link inside every heading for the website's own hover-to-copy-link
   affordance - meaningless in a PDF, and left alone would render as a
   literal "¶" character after every heading.
"""

from __future__ import annotations

import sys

from bs4 import BeautifulSoup


def fix(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for button in soup.select("a.md-content__button"):
        button.decompose()

    for style in soup.find_all("style"):
        style.decompose()

    for permalink in soup.select("a.headerlink"):
        permalink.decompose()

    for radio in soup.select('input[type="radio"]'):
        radio.decompose()

    for label in soup.select("div.tabbed-labels label"):
        p = soup.new_tag("p")
        p["class"] = "zendoc-tab-label"
        p.string = label.get_text()
        label.replace_with(p)

    return str(soup)


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        html = f.read()
    with open(dst, "w", encoding="utf-8") as f:
        f.write(fix(html))
