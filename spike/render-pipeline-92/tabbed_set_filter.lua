-- Spike: reconstructs pymdownx.blocks.tab's "tabbed-set" HTML structure
-- (already parsed into Pandoc's AST by this point - see fix_tabs.py for why
-- label boundaries had to be fixed *before* Pandoc's HTML reader ever saw
-- them) into the same tabbox-header/tabbox-body/tabbox-container shape the
-- existing tabbox_filter.lua already produces for build_pdf.py's own
-- ":::  {.tabbox title=...}" convention - so the same CSS
-- (.tabbox-container/-header/-body) styles both without any changes.
--
-- Unlike the existing filter (one .tabbox div per tab, already split by the
-- regex conversion pass before Pandoc runs), pymdownx groups every tab in a
-- set into one "tabbed-set" div: a "tabbed-labels" child holding one block
-- per label, and a "tabbed-content" child holding one "tabbed-block" div of
-- content per tab, in the same order. This walks both children pairwise and
-- emits one tabbox-container per tab, all in place of the original div.

function Div(el)
  if el.classes:includes('tabbed-set') then
    local labels_div, content_div
    for _, child in ipairs(el.content) do
      if child.t == 'Div' and child.classes:includes('tabbed-labels') then
        labels_div = child
      elseif child.t == 'Div' and child.classes:includes('tabbed-content') then
        content_div = child
      end
    end
    if not labels_div or not content_div then
      return el
    end

    local tabs = {}
    for i, label_block in ipairs(labels_div.content) do
      local body_block = content_div.content[i]
      if body_block then
        local header = pandoc.Div({ pandoc.Plain(label_block.content) }, { class = 'tabbox-header' })
        local body = pandoc.Div(body_block.content, { class = 'tabbox-body' })
        table.insert(tabs, pandoc.Div({ header, body }, { class = 'tabbox-container' }))
      end
    end

    return tabs
  end
end
