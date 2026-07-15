-- Extended spike: combines the new tabbed-set restructuring with the
-- EXISTING heading-numbering logic verbatim from build_pdf.py's own
-- tabbox_filter.lua Header() function (chapter_id hardcoded to "7" here,
-- matching installtooling.md's real nav position - the real pipeline
-- computes this per-page via chapter_identifiers, see issue #91).

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

local h1, h2, h3 = 6, 0, 0

function Header(block)
  if not block.classes:includes('unnumbered') then
    if block.level == 1 then
      h2 = 0
      h3 = 0
      h1 = h1 + 1
      table.insert(block.content, 1, pandoc.Str(tostring(h1) .. '. '))
    elseif block.level == 2 then
      h2 = h2 + 1
      h3 = 0
      table.insert(block.content, 1, pandoc.Str(tostring(h1) .. '.' .. tostring(h2) .. ' '))
    elseif block.level == 3 then
      h3 = h3 + 1
      table.insert(block.content, 1, pandoc.Str(tostring(h1) .. '.' .. tostring(h2) .. '.' .. tostring(h3) .. ' '))
    end
  end
  return block
end
