import os
import sys
import subprocess
import shutil
import toml
import re
import importlib.util

def extract_md_files(nav_element):
    """Recursively walks the Zensical navigation tree to extract .md files in order."""
    files = []
    if isinstance(nav_element, str):
        if nav_element.endswith('.md'):
            files.append(nav_element)
    elif isinstance(nav_element, list):
        for item in nav_element:
            files.extend(extract_md_files(item))
    elif isinstance(nav_element, dict):
        for key, value in nav_element.items():
            files.extend(extract_md_files(value))
    return files

def preprocess_markdown(file_path, output_path, config, calculated_vars, is_index=False):
    """Parses template conditionals, applies global asset filtering, and prepares 
    clean markdown layouts for direct HTML translation via WeasyPrint.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Explicitly strip invisible UTF-8 Byte Order Marks (BOM)
    content = content.lstrip('\ufeff')

    # Clean String-Split Front Matter Stripper
    if content.strip().startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2]

    # Purge any lines containing user-select from inline markdown styles completely
    content = re.sub(r'^.*user-select.*$\n?', '', content, flags=re.MULTILINE | re.IGNORECASE)

    # AUTOMATED VIDEO EMBEDDING INTERCEPTOR ENGINE
    def video_iframe_replacer(match):
        indent = match.group(1) or ""
        iframe_tag = match.group(2)
        
        src_match = re.search(r'src=["\']([^"\']+)["\']', iframe_tag, re.IGNORECASE)
        title_match = re.search(r'title=["\']([^"\']+)["\']', iframe_tag, re.IGNORECASE)
        
        if not src_match:
            return match.group(0)
            
        video_url = src_match.group(1)
        if "youtube.com/embed/" in video_url:
            video_url = video_url.replace("youtube.com/embed/", "youtube.com/watch?v=").split('?')[0]
            
        video_title = title_match.group(1).strip() if title_match else "Video Tutorial"
        
        return (
            f"\n\n{indent}!!! info \"{video_title}\"\n"
            f"{indent}    🔗 **[Watch Video]({video_url})**\n\n"
        )

    content = re.sub(
        r'^([ \t]*)(?:<div[^>]*>[\s\r\n]*)?(<iframe[^>]+>.*?<\/iframe>)(?:[\s\r\n]*<\/div>)?',
        video_iframe_replacer,
        content,
        flags=re.MULTILINE | re.IGNORECASE | re.DOTALL
    )

    # AUTOMATED ZENSICAL CAPTION BLOCK TRANSLATION ENGINE
    def zensical_caption_replacer(match):
        indent = match.group(1)
        alt_text = match.group(2)
        img_url = match.group(3)
        attrs = match.group(4) or ""
        caption_body = match.group(5).strip()
        
        pandoc_attrs = ""
        if attrs:
            cleaned_attrs = re.sub(r'=["\']([^"\']+)["\']', r'=\1', attrs).strip()
            pandoc_attrs = f"{{{cleaned_attrs}}}"
            
        return (
            f"\n\n{indent}<figure class=\"text-center\">\n"
            f"{indent}  <img src=\"{img_url}\" alt=\"{alt_text}\" style=\"width: 70%;\" />\n"
            f"{indent}  <figcaption class=\"text-center-italic\" style=\"margin-top: 8px;\">{caption_body}</figcaption>\n"
            f"{indent}</figure>\n\n"
        )

    content = re.sub(
        r'^([ \t]*)!\[([^\]]*)\]\(([^)]*)\)(?:\{([^}]*)\})?[ \t]*\n(?:[ \t]*\n)*\1///\s*caption\s*\n(.*?)\n\1///',
        zensical_caption_replacer,
        content,
        flags=re.MULTILINE | re.DOTALL
    )

    # AUTOMATED NATIVE HTML IMAGE PATH RESOLVER
    def html_img_resolver(match):
        full_tag = match.group(0)
        src_path = match.group(1)
        if src_path.startswith(('http://', 'https://', 'file://', '/')):
            return full_tag
        abs_path = os.path.abspath(os.path.join(os.path.dirname(file_path), src_path)).replace('\\', '/')
        return full_tag.replace(src_path, abs_path)

    content = re.sub(r'<img[^>]+src=["\']([^"\']+)["\']', html_img_resolver, content, flags=re.IGNORECASE)

    # Convert body horizontal rules (---) to asterisks (***) to protect Pandoc YAML maps
    content = re.sub(r'^\s*---\s*$', '***', content, flags=re.MULTILINE)

    # Globally strip web-only link target attributes
    content = re.sub(r'\{\s*target=[^}]*\}', '', content, flags=re.IGNORECASE)

    # FOOTNOTES HEADING INTERCEPTOR ENGINE:
    content = re.sub(r'^(#{1,6})\s+Footnotes\s*$', r'\1 Footnotes {#custom-footnotes-heading}', content, flags=re.MULTILINE | re.IGNORECASE)

    # WEB-STYLE INTERCEPTOR ENGINE:
    if re.search(r'<style>.*?\.md-typeset\s+h1\s*\{\s*display:\s*none;?\s*\}.*?</style>', content, flags=re.DOTALL | re.IGNORECASE):
        def hide_matching_h1(match):
            line = match.group(0)
            if '{.' in line:
                return line.replace('{.', '{.hidden .unnumbered .unlisted .')
            elif '{' in line:
                return line.replace('{', '{.hidden .unnumbered .unlisted}')
            return f"{line} {{.hidden .unnumbered .unlisted}}"
            
        content = re.sub(r'^#\s+.*$', hide_matching_h1, content, flags=re.MULTILINE)

    # AUTOMATED ICON SHORTCODE CONVERSION ENGINE
    def icon_replacer(match):
        shortcode = match.group(1)
        attr_list = match.group(2) or ""
        
        classes = []
        if attr_list:
            classes = re.findall(r'\.([a-zA-Z0-9_-]+)', attr_list)
            
        rel_path = None
        prefixes = {
            "fontawesome-brands-": "fontawesome/brands/",
            "fontawesome-regular-": "fontawesome/regular/",
            "fontawesome-solid-": "fontawesome/solid/",
            "material-": "material/",
            "octicons-": "octicons/",
            "simple-": "simple/"
        }
        for pref, path_prefix in prefixes.items():
            if shortcode.startswith(pref):
                rel_path = f"{path_prefix}{shortcode[len(pref):]}.svg"
                break
                
        if not rel_path:
            return match.group(0)
            
        svg_content = None
        search_dirs = []
        
        try:
            import material
            base_mat = os.path.dirname(material.__file__)
            search_dirs.extend([
                os.path.join(base_mat, "templates", ".icons"),
                os.path.join(base_mat, ".icons"),
                os.path.join(os.path.dirname(base_mat), "material", "templates", ".icons"),
                os.path.join(os.path.dirname(base_mat), "material", ".icons")
            ])
        except Exception:
            pass
            
        for p in sys.path:
            if p and os.path.isdir(p):
                potential_templates = os.path.join(p, "material", "templates", ".icons")
                if os.path.isdir(potential_templates):
                    search_dirs.append(potential_templates)
                potential_icons = os.path.join(p, "material", ".icons")
                if os.path.isdir(potential_icons):
                    search_dirs.append(potential_icons)
                    
        search_dirs.append(os.path.join(os.getcwd(), ".icons"))
        
        for base_dir in search_dirs:
            full_path = os.path.join(base_dir, rel_path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, "r", encoding="utf-8") as svg_f:
                        svg_content = svg_f.read()
                    break
                except Exception:
                    pass
                    
        if svg_content:
            svg_content = re.sub(r'<\?xml[^>]*\?>', '', svg_content)
            svg_content = re.sub(r'', '', svg_content, flags=re.DOTALL)
            svg_content = re.sub(r'\s+', ' ', svg_content).strip()
            
            extra_class = " " + " ".join(classes) if classes else ""
            return f'<span class="twemoji{extra_class}">{svg_content}</span>'
            
        return match.group(0)

    content = re.sub(r':([a-zA-Z0-9_-]+):(?:\{\s*([^}]+)\s*\})?', icon_replacer, content)

    # AUTOMATED COMMAND PROMPT INJECTOR ENGINE (Indentation Aware)
    def shell_prompt_replacer(match):
        indent = match.group(1)
        lang = match.group(2)
        code_body = match.group(3)
        
        if lang.lower() in ['bash', 'sh', 'shell', 'zsh', 'console', 'cmd', 'powershell', 'terminal']:
            lines = code_body.splitlines()
            updated_lines = []
            in_continuation = False
            
            for line in lines:
                stripped = line.strip()
                if stripped:
                    if not in_continuation and not stripped.startswith('$') and not stripped.startswith('#'):
                        l_indent = len(line) - len(line.lstrip())
                        updated_lines.append(line[:l_indent] + '$ ' + line[l_indent:])
                    else:
                        updated_lines.append(line)
                    in_continuation = stripped.endswith('\\')
                else:
                    updated_lines.append(line)
                    in_continuation = False
            return f"{indent}```{lang}\n" + "\n".join(updated_lines) + f"\n{indent}```"
        return match.group(0)

    content = re.sub(r'^([ \t]*)```([a-zA-Z0-9_-]*)\s*\n(.*?)\n\1```', shell_prompt_replacer, content, flags=re.MULTILINE | re.DOTALL)

    # THE IMAGE FILTER: Process light and dark mode asset rows line by line
    processed_lines = []
    for line in content.splitlines():
        if '#only-dark' in line:
            continue  
        if '#only-light' in line:
            line = line.replace('#only-light', '')  
        processed_lines.append(line)
    content = '\n'.join(processed_lines)

    # Collate static configurations with runtime macro definitions
    project_vars = config.get('project', {})
    extra_vars = config.get('extra', {})
    vars_dict = {}
    if isinstance(project_vars, dict): vars_dict.update(project_vars)
    if isinstance(extra_vars, dict): vars_dict.update(extra_vars)
    vars_dict.update(calculated_vars)
    
    docs_dir = config.get('docs_dir', 'docs')

    # Evaluate Template Conditional Rules
    lines = content.splitlines()
    filtered_lines = []
    state_stack = []

    for line in lines:
        if re.search(r'[{(]%\s*if\s+(\w+)\s*%', line):
            match = re.search(r'if\s+(\w+)', line)
            var_name = match.group(1)
            raw_val = vars_dict.get(var_name, False)
            if isinstance(raw_val, str):
                condition_active = raw_val.lower() in ('true', '1', 'yes', 'on')
            else:
                condition_active = bool(raw_val)
            state_stack.append(('if', condition_active))
            continue
        elif re.search(r'[{(]%\s*else\s*%', line):
            if state_stack and state_stack[-1][0] == 'if':
                if_was_active = state_stack[-1][1]
                state_stack[-1] = ('else', not if_was_active)
            continue
        elif re.search(r'[{(]%\s*endif\s*%', line):
            if state_stack:
                state_stack.pop()
            continue

        if not all(is_active for block_type, is_active in state_stack):
            continue
        filtered_lines.append(line)

    content = '\n'.join(filtered_lines)

    # 🎨 COVER PAGE CLEANUP & UNNUMBERED HEADING CONVERSION
    if is_index:
        content = re.sub(r'[<]![-\s]*.*?[- \s]*[>]', '', content, flags=re.DOTALL)
        content = re.sub(r'\[:material-file-pdf-box: PDF\].*$', '', content, flags=re.MULTILINE)
        
        def tag_unnumbered(match):
            line = match.group(0)
            if '{.' in line:
                return line.replace('{.', '{.hidden .unnumbered .unlisted .')
            elif '{' in line:
                return line.replace('{', '{.hidden .unnumbered .unlisted}')
            return f"{line} {{.hidden .unnumbered .unlisted}}"
            
        content = re.sub(r'^#{1,6}\s+.*$', tag_unnumbered, content, flags=re.MULTILINE)
        content = f'<div class="cover-page">\n{content}\n</div>\n'

    # 🧹 HIGH-FIDELITY ADMONITION FENCED DIV STATE MACHINE
    final_lines = content.splitlines()
    new_lines = []
    in_tab = False
    in_admonition = False
    in_gridcard = False
    in_card_item = False
    gridcard_base_indent = 0
    
    tab_indent_level = 0
    adm_indent_level = 0

    for line in final_lines:
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)
        
        if stripped == "":
            new_lines.append("")
            continue

        # INTERCEPT STRICLY TARGETED 'class="grid cards"' RAW HTML CONTAINER BLOCKS
        if not in_gridcard:
            grid_div_match = re.search(r'<div[^>]*class=["\']([^"\']*(?:grid\s+cards|cards\s+grid)[^"\']*)["\'][^>]*>', stripped, re.IGNORECASE)
            if grid_div_match:
                in_gridcard = True
                gridcard_base_indent = current_indent
                style_match = re.search(r'style=["\']([^"\']*)["\']', line, re.IGNORECASE)
                style_attr = f' style="{style_match.group(1)}"' if style_match else ''
                new_lines.append(f"\n::: {{.gridcard-matrix{style_attr}}}\n")
                continue
                
        if in_gridcard:
            if stripped.startswith('</div>'):
                if in_card_item:
                    new_lines.append("\n:::\n")
                    in_card_item = False
                in_gridcard = False
                new_lines.append("\n:::\n")
                continue
                
            card_strip_count = gridcard_base_indent + 4
            relative_line = line[card_strip_count:] if line.startswith(' ' * card_strip_count) else line.lstrip()
            rel_stripped = relative_line.lstrip()
            
            if rel_stripped.startswith('-') and not rel_stripped.startswith('***'):
                if in_card_item:
                    new_lines.append("\n:::\n")
                in_card_item = True
                new_lines.append("\n::: {.gridcard-item}\n")
                
                title_text = re.sub(r'^-\s+', '', rel_stripped)
                title_text = re.sub(r'\{\s*[^}]*\}', '', title_text)
                title_text = re.sub(r':[a-zA-Z0-9_-]+:', '', title_text).strip()
                
                new_lines.append(f'::: {{.gridcard-title}}\n{title_text}\n:::\n')
                continue
                
            line = relative_line
            stripped = rel_stripped
            current_indent = len(line) - len(stripped)

        # Close open containers dynamically if indentation parameters contract
        if in_tab and not stripped.startswith('==='):
            if current_indent <= tab_indent_level:
                new_lines.append("\n:::::\n")
                in_tab = False
                if in_admonition:
                    new_lines.append("\n::::\n")
                    in_admonition = False
                
        if in_admonition and not in_tab and not stripped.startswith('!!!'):
            if current_indent < adm_indent_level + 4:
                in_admonition = False
                new_lines.append("\n::::\n") 

        # INTERCEPT CONTENT TABS (5 Colons to prevent nesting collapse)
        if stripped.startswith('==='):
            if in_tab:
                new_lines.append("\n:::::\n")
            match = re.search(r'^===\s*["\'“‘]?(.*?)["\'”’]?\s*$', stripped)
            tab_title = match.group(1).strip() if match else "Tab"
            tab_indent_level = current_indent
            in_tab = True
            if in_admonition:
                new_lines.append("\n::::\n")
                in_admonition = False
            new_lines.append(f'\n::::: {{.tabbox title="{tab_title}"}}')
            continue
            
        # INTERCEPT ADMONITION CONTAINERS (4 Colons to maintain separate nesting tracking)
        if stripped.startswith('!!!'):
            if in_admonition:
                new_lines.append("\n::::\n")
            parts = stripped.split(maxsplit=2)
            adm_type = parts[1].lower() if len(parts) > 1 else "note"
            adm_title = parts[2].strip('"\'') if len(parts) > 2 else adm_type.capitalize()
            
            new_lines.append(f"\n::: {{.admonition .{adm_type}}}")
            new_lines.append(f"::: {{.admonition-title}}\n{adm_title}\n::::\n")
            in_admonition = True
            adm_indent_level = current_indent
            continue

        if in_tab:
            strip_count = tab_indent_level + 4
            content_line = line[strip_count:] if len(line) >= strip_count and line.startswith(' ' * strip_count) else line.lstrip()
            content_stripped = content_line.lstrip()
            
            if content_stripped.startswith('!!!'):
                if in_admonition:
                    new_lines.append("\n::::\n")
                parts = content_stripped.split(maxsplit=2)
                adm_type = parts[1].lower() if len(parts) > 1 else "note"
                adm_title = parts[2].strip('"\'') if len(parts) > 2 else adm_type.capitalize()
                
                new_lines.append(f"\n::: {{.admonition .{adm_type}}}")
                new_lines.append(f"::: {{.admonition-title}}\n{adm_title}\n::::\n")
                in_admonition = True
                adm_indent_level = len(content_line) - len(content_stripped)
                continue
                
            if in_admonition:
                content_indent = len(content_line) - len(content_stripped)
                if content_indent < adm_indent_level + 4 and not content_stripped.startswith('!!!'):
                    in_admonition = False
                    new_lines.append("\n::::\n") 
                
                if in_admonition:
                    adm_strip = adm_indent_level + 4
                    adm_content = content_line[adm_strip:] if content_line.startswith(' ' * adm_strip) else content_stripped
                    new_lines.append(adm_content)
                else:
                    new_lines.append(content_line)
            else:
                new_lines.append(content_line)
                
        elif in_admonition:
            strip_count = adm_indent_level + 4
            content_line = line[strip_count:] if line.startswith(' ' * strip_count) else stripped
            new_lines.append(content_line)
        else:
            new_lines.append(line)

    if in_tab:
        new_lines.append("\n:::::\n")
    if in_admonition:
        new_lines.append("\n::::\n")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

def main():
    if not os.path.exists('zensical.toml'):
        print("❌ Error: zensical.toml not found in the current directory.")
        sys.exit(1)
        
    with open('zensical.toml', 'r', encoding='utf-8') as f:
        config = toml.load(f)
        
    project_section = config.get('project', {})
    nav = project_section.get('nav', []) if isinstance(project_section, dict) else []
    if not nav:
        nav = config.get('nav', [])
        
    if not nav:
        print("❌ Error: No 'nav' section found in zensical.toml.")
        sys.exit(1)
        
    md_files = extract_md_files(nav)
    docs_dir = config.get('docs_dir', 'docs')
    full_paths = [os.path.join(docs_dir, f) for f in md_files]
    valid_paths = [p for p in full_paths if os.path.exists(p)]
    
    if not valid_paths:
        print("❌ Error: No valid markdown files found.")
        sys.exit(1)

    calculated_vars = {}
    if os.path.exists('macros.py'):
        print("🔧 Executing macros.py environment maps...")
        try:
            spec = importlib.util.spec_from_file_location("macros", "macros.py")
            macros_module = importlib.util.module_from_spec(spec)
            sys.path.insert(0, os.getcwd())
            spec.loader.exec_module(macros_module)
            
            for attr in dir(macros_module):
                if not attr.startswith('__'):
                    val = getattr(macros_module, attr)
                    if isinstance(val, (bool, str, int, float)):
                        calculated_vars[attr] = val
                    elif isinstance(val, dict):
                        calculated_vars.update(val)
            
            if hasattr(macros_module, 'define_env'):
                class AttributeDict(dict):
                    def __getattr__(self, attr): return self.get(attr)
                    def __setattr__(self, attr, value): self[attr] = value
                
                class MockEnv:
                    def __init__(self):
                        self.variables = AttributeDict()
                        self.conf = {}
                    def macro(self, func, name=None): return func
                
                env_obj = MockEnv()
                macros_module.define_env(env_obj)
                for k, v in env_obj.variables.items():
                    if isinstance(v, (bool, str, int, float)):
                        calculated_vars[k] = v
        except Exception as e:
            print(f"⚠️ Warning: Encountered an issue while executing macros.py: {e}")
        
    theme_section = project_section.get('theme', {}) if isinstance(project_section, dict) else config.get('theme', {})
    font_section = theme_section.get('font', {}) if isinstance(theme_section, dict) else {}
    
    main_font = "Inter"
    mono_font = "JetBrains Mono"
    if isinstance(font_section, dict):
        main_font = font_section.get('text', main_font)
        mono_font = font_section.get('code', mono_font)

    copyright_text = project_section.get('copyright') or config.get('copyright') or "Copyright 2026"

    temp_build_dir = "pdf_build_workspace"
    os.makedirs(temp_build_dir, exist_ok=True)
    
    print("🧹 Preprocessing markdown file layouts...")
    processed_paths = []
    for path in valid_paths:
        safe_name = path.replace('/', '_').replace('\\', '_')
        temp_out_path = os.path.join(temp_build_dir, safe_name)
        is_index = "index.md" in os.path.basename(path).lower()
        preprocess_markdown(path, temp_out_path, config, calculated_vars, is_index=is_index)
        processed_paths.append(temp_out_path)

    toc_trigger_path = os.path.join(temp_build_dir, "toc_trigger_temp.md")
    with open(toc_trigger_path, "w", encoding="utf-8") as f:
        f.write("\n<div class=\"page-break\"></div>\n\n# Table of Contents {.unnumbered .unlisted}\n\n<div class=\"page-break\"></div>\n")

    compiled_paths = []
    if "index.md" in os.path.basename(valid_paths[0]).lower():
        compiled_paths.append(processed_paths[0])
        compiled_paths.append(toc_trigger_path)
        compiled_paths.extend(processed_paths[1:])
    else:
        compiled_paths = [toc_trigger_path] + processed_paths

    temp_master_md = os.path.join(temp_build_dir, "_temp_master_compiled.md")
    with open(temp_master_md, "w", encoding="utf-8") as out_f:
        for chunk_path in compiled_paths:
            with open(chunk_path, "r", encoding="utf-8") as in_f:
                out_f.write(in_f.read() + "\n\n")

    output_pdf = "docs/site_documentation.pdf"
    
    lua_filter_path = os.path.join(temp_build_dir, "tabbox_filter.lua")
    with open(lua_filter_path, "w", encoding="utf-8") as f:
        f.write(
            "local h1, h2, h3 = 0, 0, 0\n\n"
            "function Div(el)\n"
            "  if el.classes:includes('tabbox') then\n"
            "    local title = el.attributes['title'] or 'Tab'\n"
            "    local header = pandoc.Div({pandoc.Plain({pandoc.Str(title)})}, {class='tabbox-header'})\n"
            "    local body = pandoc.Div(el.content, {class='tabbox-body'})\n"
            "    el.content = {header, body}\n"
            "    el.classes = {'tabbox-container'}\n"
            "    return el\n"
            "  end\n"
            "end\n\n"
            "function Header(block)\n"
            "  if not block.classes:includes('unnumbered') then\n"
            "    if block.level == 1 then\n"
            "      h1 = h1 + 1\n"
            "      h2 = 0\n"
            "      h3 = 0\n"
            "      table.insert(block.content, 1, pandoc.Str(tostring(h1) .. '. '))\n"
            "    elseif block.level == 2 then\n"
            "      h2 = h2 + 1\n"
            "      h3 = 0\n"
            "      table.insert(block.content, 1, pandoc.Str(tostring(h1) .. '.' .. tostring(h2) .. ' '))\n"
            "    elseif block.level == 3 then\n"
            "      h3 = h3 + 1\n"
            "      table.insert(block.content, 1, pandoc.Str(tostring(h1) .. '.' .. tostring(h2) .. '.' .. tostring(h3) .. ' '))\n"
            "    end\n"
            "  end\n"
            "  return block\n"
            "end\n\n"
            "function Pandoc(doc)\n"
            "  local toc_list = pandoc.structure.table_of_contents(doc)\n"
            "  local final_blocks = {}\n"
            "  for _, block in ipairs(doc.blocks) do\n"
            "    table.insert(final_blocks, block)\n"
            "    if block.t == 'Header' and block.level == 1 and pandoc.utils.stringify(block.content) == 'Table of Contents' then\n"
            "      table.insert(final_blocks, pandoc.Div(toc_list, {id='TOC', class='toc'}))\n"
            "    end\n"
            "  end\n"
            "  doc.blocks = final_blocks\n"
            "  return doc\n"
            "end\n"
        )
    
    temp_compiled_css = os.path.join(temp_build_dir, "_temp_compiled_print.css")
    
    original_css_content = ""
    for css_src in [os.path.join("stylesheets", "extra.css"), os.path.join("stylesheets", "print.css")]:
        if os.path.exists(css_src):
            with open(css_src, "r", encoding="utf-8") as f:
                original_css_content += f.read() + "\n"

    cleaned_original_css = re.sub(r'@charset[^;{]*(\{.*?\}|;)', '', original_css_content, flags=re.IGNORECASE | re.DOTALL)
    cleaned_original_css = re.sub(r'^.*user-select.*$\n?', '', cleaned_original_css, flags=re.MULTILINE | re.IGNORECASE)

    clean_copyright = copyright_text.strip().replace('\n', ' ').replace('\r', ' ')
    sanitized_copyright = clean_copyright.replace('&copy;', '©').replace('&#169;', '©')

    css_escaped_copyright = ""
    for char in sanitized_copyright:
        if ord(char) > 127:
            css_escaped_copyright += f"\\{ord(char):04X} "
        else:
            css_escaped_copyright += char
    safe_copyright = css_escaped_copyright.replace('"', '\\"')

    css_blueprint = """
/* ==========================================================================
   DYNAMIC TYPOGRAPHY CONFIGURATION (Injected from settings)
   ========================================================================== */
body {
    font-family: "__MAIN_FONT__", -apple-system, sans-serif !important;
}
h1, h2, h3, h4, h5, h6 {
    font-family: "__MAIN_FONT__", sans-serif !important;
}
pre, code {
    font-family: "__MONO_FONT__", monospace !important;
}

/* Hard visibility override for explicitly hidden page headings */
.hidden {
    display: none !important;
}

/* ==========================================================================
   CRITICAL WEASYPRINT STRUCTURAL CANVAS RESET 
   ========================================================================== */
html, body, main, div, article, section, .md-container, .md-main, .md-content {
    display: block !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
    overflow: visible !important;
    position: static !important;
    float: none !important;
    background: transparent !important;
}

header, nav, footer, .md-sidebar, .md-header, .md-footer, .md-search, #search {
    display: none !important;
}

/* ==========================================================================
   A4 PAGE LAYOUT & UNIFIED FOOTER CONFIGURATION
   ========================================================================== */
@page {
    size: A4;
    margin: 2cm !important;
    
    @bottom-center {
        content: none !important;
    }
    @bottom-left {
        content: "__COPYRIGHT__" !important;
        font-family: "__MAIN_FONT__", sans-serif !important;
        font-size: 9pt !important;
        color: #555555 !important;
        vertical-align: top !important;
        border-top: 1px solid #e2e8f0 !important;
        padding-top: 8px !important;
        width: 85% !important;
        text-align: left !important;
    }
    @bottom-right {
        content: "Page " counter(page) " of " counter(pages) !important;
        font-family: "__MAIN_FONT__", sans-serif !important;
        font-size: 9pt !important;
        color: #555555 !important;
        vertical-align: top !important;
        border-top: 1px solid #e2e8f0 !important;
        padding-top: 8px !important;
        width: 15% !important;
        text-align: right !important;
    }
}

@page :first {
    @bottom-left {
        content: none !important;
        border-top: none !important;
    }
    @bottom-right {
        content: none !important;
        border-top: none !important;
    }
}

/* ==========================================================================
   Page-Break Structural Rules
   ========================================================================== */
.page-break, .cover-page {
    page-break-after: always;
    break-after: always;
}

h1 {
    break-before: page !important;
}

.cover-page h1 {
    break-before: auto !important;
}

/* ==========================================================================
   TABLE OF CONTENTS STYLING
   ========================================================================== */
.toc ul {
    list-style-type: none !important;
    padding-left: 0 !important;
    margin-left: 0 !important;
}
.toc li {
    margin-bottom: 0.6em !important;
}
.toc li ul {
    padding-left: 1.5em !important;
    margin-top: 0.3em !important;
}
.toc a {
    text-decoration: none !important;
    color: #111111 !important;
    display: block !important;
}
.toc a::after {
    content: " " leader(dotted) " " target-counter(attr(href), page);
    color: #555555 !important;
    font-weight: normal !important;
}

/* ==========================================================================
   TABLE LAYOUT STYLING MATRIX
   ========================================================================== */
table {
    border-collapse: collapse !important;
    border: 0.25pt solid #555555 !important; /* 0.25pt dark grey outer perimeter line */
    width: 100% !important;
    margin: 1.2em 0 !important;
}
table th {
    background-color: rgba(0, 0, 0, 0.1) !important; /* 10% dark grey heading shading */
    font-weight: bold !important;
}
table th, table td {
    padding: 8px 12px !important;
    border-top: 0.25pt solid #555555 !important;    /* 0.25pt internal horizontal row splits */
    border-bottom: 0.25pt solid #555555 !important; /* 0.25pt internal horizontal row splits */
    border-left: none !important;                 /* Erase internal vertical lines */
    border-right: none !important;                /* Erase internal vertical lines */
}
table tr:first-child th, table tr:first-child td {
    border-top: none !important; /* Defer to master table outer frame line */
}
table tr:last-child td {
    border-bottom: none !important; /* Defer to master table outer frame line */
}

/* ==========================================================================
   ADMONITIONS & TABS LAYOUT OVERRIDES (Unified Multi-Page Support Matrix)
   ========================================================================== */
blockquote {
    background-color: #f8fafc !important;
    border-left: 4px solid #cbd5e1 !important;
    padding: 12px 16px !important;
    margin: 1em 0 !important;
}

.tabbox-container {
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    margin: 1em 0;
    page-break-inside: auto !important;
    break-inside: auto !important;
    -webkit-box-decoration-break: clone !important;
    box-decoration-break: clone !important;
}
.tabbox-header {
    background-color: rgba(0, 0, 0, 0.1) !important;
    color: #000000 !important;
    font-weight: bold;
    padding: 8px 12px;
    font-size: 10pt;
    page-break-after: avoid !important;
    break-after: avoid !important;
}
.tabbox-body {
    background-color: rgba(0, 0, 0, 0.05) !important;
    padding: 12px;
    page-break-inside: auto !important;
    break-inside: auto !important;
    -webkit-box-decoration-break: clone !important;
    box-decoration-break: clone !important;
}

/* ADVANCED PRINT-READY ADMONITION LAYOUT SHIELDS */
.admonition {
    border-left: 4px solid #448aff !important;
    background-color: #f8fafc !important;
    padding: 14px 18px !important;
    margin: 1.2em 0 !important;
    page-break-inside: auto !important;
    break-inside: auto !important;
    -webkit-box-decoration-break: clone !important;
    box-decoration-break: clone !important;
}
.admonition-title {
    font-weight: bold !important;
    margin-bottom: 8px !important;
    font-size: 10.5pt !important;
    color: #448aff !important;
    page-break-after: avoid !important;
    break-after: avoid !important;
}

/* ZENSICAL NATIVE ALIGNED ADMONITION COLOR SPECIFICATION MATRIX */
.admonition.note     { border-left-color: #448aff !important; background-color: rgba(68, 138, 255, 0.05) !important; }
.admonition.note     .admonition-title { color: #448aff !important; }

.admonition.abstract { border-left-color: #00b0ff !important; background-color: rgba(0, 176, 255, 0.05) !important; }
.admonition.abstract .admonition-title { color: #00b0ff !important; }

.admonition.info     { border-left-color: #00b8d4 !important; background-color: rgba(0, 184, 212, 0.05) !important; }
.admonition.info     .admonition-title { color: #00b8d4 !important; }

.admonition.tip      { border-left-color: #00bfa5 !important; background-color: rgba(0, 191, 165, 0.05) !important; }
.admonition.tip      .admonition-title { color: #00bfa5 !important; }

.admonition.success  { border-left-color: #00c853 !important; background-color: rgba(0, 200, 83, 0.05) !important; }
.admonition.success  .admonition-title { color: #00c853 !important; }

.admonition.question { border-left-color: #64dd17 !important; background-color: rgba(100, 221, 23, 0.05) !important; }
.admonition.question .admonition-title { color: #64dd17 !important; }

.admonition.warning  { border-left-color: #ff9100 !important; background-color: rgba(255, 145, 0, 0.05) !important; }
.admonition.warning  .admonition-title { color: #ff9100 !important; }

.admonition.failure  { border-left-color: #ff5252 !important; background-color: rgba(255, 82, 82, 0.05) !important; }
.admonition.failure  .admonition-title { color: #ff5252 !important; }

.admonition.danger   { border-left-color: #ff1744 !important; background-color: rgba(255, 23, 68, 0.05) !important; }
.admonition.danger   .admonition-title { color: #ff1744 !important; }

.admonition.bug      { border-left-color: #ec407a !important; background-color: rgba(236, 64, 122, 0.05) !important; }
.admonition.bug      .admonition-title { color: #ec407a !important; }

.admonition.example  { border-left-color: #651fff !important; background-color: rgba(101, 31, 255, 0.05) !important; }
.admonition.example  .admonition-title { color: #651fff !important; }

.admonition.quote    { border-left-color: #9e9e9e !important; background-color: rgba(158, 158, 158, 0.05) !important; }
.admonition.quote    .admonition-title { color: #9e9e9e !important; }

/* ==========================================================================
   ZENSICAL GRID CARD CANVAS ARCHITECTURE
   ========================================================================== */
.gridcard-matrix {
    display: block !important;
    margin: 1.5em 0 !important;
}
.gridcard-item {
    background-color: rgba(0, 0, 0, 0.025) !important; 
    border: none !important;                           
    padding: 16px !important;
    margin-bottom: 1em !important;
    border-radius: 4px !important;
    page-break-inside: avoid;
    break-inside: avoid;
}
.gridcard-title {
    font-weight: bold !important;
    font-size: 13pt !important;
    margin-bottom: 12px !important;
    display: block !important;
    color: #111111 !important;
    page-break-after: avoid !important;
    break-after: avoid !important;
}
.gridcard-title p {
    font-weight: bold !important;
    font-size: 13pt !important;
    color: #111111 !important;
    margin: 0 !important;
    display: inline !important;
}

/* CRITICAL CODE BLOCK SHADING OVERRIDES */
pre, code {
    font-family: "__MONO_FONT__", monospace !important;
    background-color: rgba(0, 0, 0, 0.125) !important;
}
pre {
    padding: 10px !important;
    border-radius: 4px !important;
    margin: 1em 0 !important;
    white-space: pre-wrap !important;
}
code {
    padding: 2px 4px !important;
    border-radius: 3px !important;
}
pre code {
    padding: 0 !important;
    background-color: transparent !important;
}

/* ADVANCED FIGURE & ASSET PROTECTION BINDINGS */
/* Global 130% intrinsic print asset scale metric lookup override */
img {
    image-resolution: 74dpi !important;
    width: auto !important;  /* 🎯 Force override of inline percentage styles inside tab containers */
    max-width: 100% !important;
    height: auto !important;
}
.text-center img, .text-center-italic img {
    display: inline-block !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* Inline vector mappings */
.twemoji svg {
    width: 1.1em;
    height: 1.1em;
    vertical-align: -0.2em;
}

/* ==========================================================================
   COVER PAGE & GENERAL PRINT ALIGNMENT UTILITY MATRIX
   ========================================================================= */
.cover-page {
    padding-top: 4cm;
}
.cover-page img {
    display: block;
    margin: 1.5cm auto;
    max-width: 100%;
}
.title-ctr-1, .title-ctr-2, .title-ctr-3, .title-ctr-4, .title-ctr-5, .title-ctr-6,
.title-ctr-b1, .title-ctr-b2, .title-ctr-b3, .title-ctr-b4, .title-ctr-b5, .title-ctr-b6 {
    text-align: center;
    display: block;
}
.title-left-1, .title-left-2, .title-left-3, .title-left-4, .title-left-5, .title-left-6,
.title-left-b1, .title-left-b2, .title-left-b3, .title-left-b4, .title-left-b5, .title-left-b6 {
    text-align: left;
    display: block;
}
.title-ctr-b1, .title-ctr-b2, .title-ctr-b3, .title-ctr-b4, .title-ctr-b5, .title-ctr-b6,
.title-left-b1, .title-left-b2, .title-left-b3, .title-left-b4, .title-left-b5, .title-left-b6 {
    font-weight: bold;
}
[class*="title-"][class*="-1"] { font-size: 26pt; line-height: 32pt; margin-bottom: 0.6em; }
[class*="title-"][class*="-2"] { font-size: 22pt; line-height: 28pt; margin-bottom: 0.6em; }
[class*="title-"][class*="-3"] { font-size: 18pt; line-height: 24pt; margin-bottom: 0.6em; }
[class*="title-"][class*="-4"] { font-size: 15pt; line-height: 20pt; margin-bottom: 0.6em; }
[class*="title-"][class*="-5"] { font-size: 13pt; line-height: 17pt; margin-bottom: 0.6em; }
[class*="title-"][class*="-6"] { font-size: 11pt; line-height: 15pt; margin-bottom: 0.6em; }

/* PRINT ALIGNMENT UTILITY MATRIX */
.text-center { text-align: center !important; display: block !important; }
.text-right { text-align: right !important;  display: block !important; }
.text-justify { text-align: justify !important; display: block !important; }

.text-center-italic { text-align: center !important; font-style: italic !important; display: block !important; }
.text-right-italic { text-align: right !important; font-style: italic !important; display: block !important; }
.text-justify-italic { text-align: justify !important; font-style: italic !important; display: block !important; }

/* Allow grid alignments to break across pages, but explicitly lock content tabs */
.gridcard-matrix, .gridcard-item,
.text-center, .text-right, .text-justify,
.text-center-italic, .text-right-italic, .text-justify-italic {
    page-break-inside: auto !important;
    break-inside: auto !important;
}

.tabbox-container, .tabbox-body, .tabbox-header {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
}
"""

    final_css_payload = css_blueprint.replace("__MAIN_FONT__", main_font)\
                                     .replace("__MONO_FONT__", mono_font)\
                                     .replace("__COPYRIGHT__", safe_copyright)

    with open(temp_compiled_css, "w", encoding="utf-8") as f:
        f.write(cleaned_original_css + "\n\n" + final_css_payload)

    cmd = [
        "pandoc",
        temp_master_md,                
        "-o", output_pdf,
        "--pdf-engine=weasyprint",
        "--mathjax",                   
        f"--lua-filter={lua_filter_path}",
        "-f", "markdown",
        "--resource-path=.",
        f"--resource-path={docs_dir}",
        f"--css={temp_compiled_css}"   
    ]

    print(f"🚀 Processing via unified layout configuration framework...")
    try:
        subprocess.run(cmd, check=True)
        print(f"\n🎉 Success! The document compiled cleanly. PDF ready at: {output_pdf}")
    except subprocess.CalledProcessError:
        print("\n❌ Error: Pandoc/Weasyprint failed to compile the document stream.")
    finally:
        if os.path.exists(temp_build_dir):
            shutil.rmtree(temp_build_dir)

if __name__ == "__main__":
    main()