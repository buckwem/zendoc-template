# Render-pipeline migration spike (#92)

Validated proof-of-concept artifacts for migrating `build_pdf.py` from
feeding Pandoc raw regex-preprocessed markdown to feeding it real HTML,
rendered through Zensical's own `zensical.markdown.render.render()`.

Not wired into `build_pdf.py` yet - these are the pieces proven to work in
isolation, kept here as a starting point for the real integration (see #92
for full findings and remaining task list).

## Files

- `fix_tabs.py` - HTML preprocessing: strips page-chrome noise
  (`heading_counter_reset()`'s `<style>` block, `toc` permalink pilcrows,
  radio inputs), and rewrites each `pymdownx.blocks.tab` `<label>` into its
  own `<p>` so Pandoc's HTML reader doesn't merge multiple tab labels into
  one unseparated run of text (confirmed this merging happens - and is
  unrecoverable afterward - at HTML-parse time, before any Lua filter runs).
- `tabbed_set_filter.lua` - Pandoc Lua filter: reconstructs pymdownx's
  `tabbed-set`/`tabbed-labels`/`tabbed-content` structure (once `fix_tabs.py`
  has fixed label boundaries) into the same `tabbox-header`/`tabbox-body`/
  `tabbox-container` shape `build_pdf.py`'s existing `tabbox_filter.lua`
  already produces for its own `.tabbox` convention - so no CSS changes are
  needed to style it.
- `full_filter.lua` - the above combined with the existing `Header()`
  heading-numbering logic (copied verbatim from `build_pdf.py`'s current
  Lua filter), for an end-to-end proof against one real page.

## How this was validated

Against `docs/starthere/installtooling.md` (chosen for having live headings,
nested tabs/admonitions, a `figure-caption`, and multiple `table-caption`s):

```python
import zensical.config as zc
zc.parse_config('zensical.toml')
from zensical.markdown.render import render
with open('docs/starthere/installtooling.md', encoding='utf-8') as f:
    content = f.read()
result = render(content, 'starthere/installtooling.md', 'starthere/installtooling/')
html = result['content']
```

then `fix_tabs.py`'s `fix()` function, then:

```
pandoc -f html wrap.html --lua-filter=full_filter.lua --pdf-engine=weasyprint -o out.pdf
```

Produced a PDF whose heading numbers ("7. Install tooling", "7.1 Install
Visual Studio Code", "7.1.1 Install Visual Studio Code") and tab structure
(each of macOS/Windows/PowerShell/Linux clearly labeled with its own content
following) exactly match the current pipeline's real output for the same
page - see #92 for the full comparison.
