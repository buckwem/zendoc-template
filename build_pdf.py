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
    """Parses template conditionals, applies global light/dark asset filtering, strips web-only 

    link target attributes to prevent LaTeX math crashes, and compiles layout environments.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Globally strip web-only link target attributes to prevent unescaped underscore crashes
    content = re.sub(r'\{\s*target=[^}]*\}', '', content, flags=re.IGNORECASE)

    # ✨ THE AUTOMATED COMMAND PROMPT INJECTOR ENGINE:
    # Scans for terminal code blocks and inserts '$ ' natively while respecting
    # bash comments, pre-existing prompts, and trailing multi-line backslash strings.
    def shell_prompt_replacer(match):
        lang = match.group(1)
        code_body = match.group(2)
        
        # Target explicit shell/terminal code blocks
        if lang.lower() in ['bash', 'sh', 'shell', 'zsh', 'console', 'cmd', 'powershell', 'terminal']:
            lines = code_body.splitlines()
            updated_lines = []
            in_continuation = False
            
            for line in lines:
                stripped = line.strip()
                if stripped:
                    # Only prepend if it's not a comment, not a continuation line, and doesn't already have a prompt
                    if not in_continuation and not stripped.startswith('$') and not stripped.startswith('#'):
                        indent = len(line) - len(line.lstrip())
                        updated_lines.append(line[:indent] + '$ ' + line[indent:])
                    else:
                        updated_lines.append(line)
                    
                    # Track if this command continues onto the next line via a trailing backslash
                    in_continuation = stripped.endswith('\\')
                else:
                    updated_lines.append(line)
                    in_continuation = False # Clear continuation tracking on empty line breaks
                    
            return f"```{lang}\n" + "\n".join(updated_lines) + "\n```"
        return match.group(0)

    content = re.sub(r'```([a-zA-Z0-9_-]*)\n(.*?)\n```', shell_prompt_replacer, content, flags=re.DOTALL)

    # Dynamically parse the explicit h1-count reset value directly out of the page style blocks
    reset_match = re.search(r'counter-reset:\s*h1-count\s+(\d+)', content)
    section_reset_val = int(reset_match.group(1)) if reset_match else 0

    # THE IMAGE FILTER: Process light and dark mode image rows line by line
    processed_lines = []
    for line in content.splitlines():
        if '#only-dark' in line:
            continue  # Drop dark mode assets completely
        if '#only-light' in line:
            line = line.replace('#only-light', '')  # Clean hash modifier out of paths
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

    # 1. Evaluate Template Conditional Rules
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

    # 🎨 THE UNIFIED COVER PAGE COMPILER ENGINE
    if is_index:
        # Clear away standard comment tags as well as smart-punctuation arrow anomalies
        content = re.sub(r'[<]![-\s–—]*.*?[-–—\s]*[>⟶]', '', content, flags=re.DOTALL)

        # Strip YAML front matter blocks cleanly
        content = re.sub(r'^---.*?---', '', content, flags=re.DOTALL)
        
        # Remove raw PDF download buttons from print outputs
        content = re.sub(r'\[:material-file-pdf-box: PDF\].*$', '', content, flags=re.MULTILINE)
        
        # Strip web-specific layout container tags and hidden styling headers
        content = re.sub(r'<style>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<div[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'</div>', '', content, flags=re.IGNORECASE)
        content = re.sub(r':material-[\w-]+:', '', content)
        content = re.sub(r'\{\s*\.md-button[^}]*\}', '', content)
        
        # Discard web page navigation headers (e.g. # Cover Page)
        content = re.sub(r'^#{1,6}\s+.*$', '', content, flags=re.MULTILINE)

        # 1. Map Markdown Images to Precise Non-Floating Graphic Environments
        def convert_images(img_match):
            path = img_match.group(2).strip().split('#')[0]
            
            width_val = "0.4\\textwidth"
            width_match = re.search(r'width="(\d+)%"', img_match.group(0))
            if width_match:
                pct = int(width_match.group(1)) / 100.0
                width_val = f"{pct:.2f}\\textwidth"
                
            if not os.path.isabs(path) and not path.replace('\\', '/').startswith(docs_dir + '/'):
                path = os.path.join(docs_dir, path)
            path = path.replace('\\', '/')
            
            return f"\n\\vspace{{0.5cm}}\n{{\\centering\\includegraphics[width={width_val}]{{{path}}}\\par}}\n\\vspace{{0.5cm}}\n"
            
        content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)(?:\{\s*[^}]*\}|)', convert_images, content)

        # 2. Map standard Markdown links to safe LaTeX \href structures
        def convert_links(match):
            label = match.group(1).strip().replace('_', '\\_').replace('&', '\\&')
            url = match.group(2).strip().replace('_', '\\_')
            return f"\\href{{{url}}}{{{label}}}"
            
        content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', convert_links, content)

        # 3. Map your 18 Custom Typography Grid Classes into perfectly scoped formatting blocks
        def convert_html_typography(match):
            align = match.group(1)          # 'ctr' or 'left'
            is_bold = bool(match.group(2))     # True if 'b' is matched
            size_num = match.group(3)        # '1' through '6'
            text = match.group(4).strip()
            
            text = re.sub(r'<br\s*/?>', lambda m: r' \\ ', text, flags=re.IGNORECASE)
            text = re.sub(r'\s+', ' ', text)
            
            # Sanitize character strings inside the custom LaTeX block
            text = text.replace('_', '\\_').replace('&', '\\&').replace('%', '\\%').replace('$', '\\$')
            
            size_map = {
                '1': r'\fontsize{26pt}{32pt}\selectfont',  
                '2': r'\fontsize{22pt}{28pt}\selectfont',  
                '3': r'\fontsize{18pt}{24pt}\selectfont',  
                '4': r'\fontsize{15pt}{20pt}\selectfont',  
                '5': r'\fontsize{13pt}{17pt}\selectfont',  
                '6': r'\fontsize{11pt}{15pt}\selectfont'   
            }
            latex_size = size_map.get(size_num, r'\fontsize{12pt}{16pt}\selectfont')
            latex_bold = r'\bfseries ' if is_bold else ''
            latex_align = r'\centering' if align == 'ctr' else r'\raggedright'
            
            return f"\n{{{latex_align} {latex_size} {latex_bold}{text}\\par}}\n"

        content = re.sub(
            r'<p\s+class=[^>]*title-(ctr|left)-(b)?([1-6])[^>]*>(.*?)</p>',
            convert_html_typography,
            content,
            flags=re.DOTALL | re.IGNORECASE
        )

        # 4. Map Text Utilities (.text-center, .text-right, .text-justify) into Scoped Blocks
        def convert_html_text_alignment(match):
            align = match.group(1).lower()
            text = match.group(2).strip()
            
            text = re.sub(r'<br\s*/?>', lambda m: r' \\ ', text, flags=re.IGNORECASE)
            text = re.sub(r'\s+', ' ', text)
            text = text.replace('_', '\\_').replace('&', '\\&').replace('%', '\\%').replace('$', '\\$')
            
            if align == 'center':
                latex_align = r'\centering'
            elif align == 'right':
                latex_align = r'\raggedleft'
            else:
                latex_align = r'\justifying'
                
            return f"\n{{{latex_align} {text}\\par}}\n"

        content = re.sub(
            r'<p\s+class=[^>]*text-(center|right|justify)[^>]*>(.*?)</p>',
            convert_html_text_alignment,
            content,
            flags=re.DOTALL | re.IGNORECASE
        )

        # 5. Translate spacing break tags into vertical spacing markers
        content = re.sub(r'<br\s*/?>', r'\n\\vspace{1cm}\n', content, flags=re.IGNORECASE)

        # 6. Sweep remaining plain text elements to center and escape formatting parameters
        final_cover_lines = []
        for line in content.splitlines():
            trimmed = line.strip()
            if trimmed:
                if trimmed.startswith('\\') or trimmed.startswith('{') or trimmed.startswith('}'):
                    final_cover_lines.append(trimmed)
                else:
                    trimmed = trimmed.replace('_', '\\_').replace('&', '\\&').replace('%', '\\%').replace('$', '\\$')
                    final_cover_lines.append(f"{{\\fontsize{{12pt}}{{16pt}}\\selectfont \\centering {trimmed}\\par}}")
        latex_body = '\n'.join(final_cover_lines)

        content = (
            "```{=latex}\n"
            "\\begin{titlepage}\n"
            "\\centering\n"
            "\\vspace*{1.5cm}\n"
            + latex_body +
            "\n\\end{titlepage}\n"
            "```\n"
        )

    # 🧹 STATE-MACHINE ADMONITION & CONTENT TAB PASSTHROUGH
    final_lines = content.splitlines()
    new_lines = []
    in_tab = False
    in_admonition = False
    tab_indent_level = 0
    adm_indent_level = 0

    for line in final_lines:
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)
        
        # Handle empty lines safely within their current context
        if line.strip() == "":
            if in_tab:
                new_lines.append("> " if in_admonition else "")
            else:
                new_lines.append("> " if in_admonition else "")
            continue
            
        # Detect if the indent drops down past the active tab's header base
        if in_tab and not stripped.startswith('==='):
            if current_indent <= tab_indent_level:
                new_lines.append("")
                new_lines.append(":::")
                new_lines.append("")
                in_tab = False
                in_admonition = False
                
        if in_admonition and not in_tab and not stripped.startswith('!!!'):
            if current_indent <= adm_indent_level:
                in_admonition = False
                new_lines.append("") 

        # A. INTERCEPT MKDOCS CONTENT TABS (=== "Tab Title")
        if stripped.startswith('==='):
            if in_tab:
                new_lines.append("")
                new_lines.append(":::")
                new_lines.append("")
                
            match = re.search(r'^===\s*["\'收藏“”区域指標]?(.*?)["\'收藏“”区域指標]?\s*$', stripped)
            tab_title = match.group(1).strip() if match else "Tab"
            
            tab_indent_level = current_indent
            in_tab = True
            in_admonition = False
            
            # Write clean Pandoc Markdown block metadata attribute syntax for Lua script filter
            new_lines.append("")
            new_lines.append(f"::: {{.tabbox title=\"{tab_title}\"}}")
            new_lines.append("")
            continue
            
        # B. INTERCEPT ADMONITION CONTAINERS (!!! note "Title")
        if stripped.startswith('!!!'):
            parts = stripped.split(maxsplit=2)
            adm_type = parts[1] if len(parts) > 1 else "Note"
            adm_title = parts[2].strip('"\'“”區域区域‘’') if len(parts) > 2 else adm_type.capitalize()
            
            if in_tab:
                new_lines.append(f"\n> **{adm_title}**\n> ")
            else:
                new_lines.append(f"\n> **{adm_title}**\n> ")
            in_admonition = True
            adm_indent_level = current_indent
            continue

        # C. RESOLVE LINE STREAM ROUTING STATE RULES
        if in_tab:
            strip_count = tab_indent_level + 4
            if len(line) >= strip_count and (line.startswith(' ' * strip_count) or line.startswith('\t' * (strip_count // 4))):
                content_line = line[strip_count:]
            else:
                content_line = line.lstrip() if line.strip() == "" else line
                
            content_stripped = content_line.lstrip()
            
            if content_stripped.startswith('!!!'):
                parts = content_stripped.split(maxsplit=2)
                adm_type = parts[1] if len(parts) > 1 else "Note"
                adm_title = parts[2].strip('"\'区域区域“”') if len(parts) > 2 else adm_type.capitalize()
                new_lines.append(f"\n> **{adm_title}**\n> ")
                in_admonition = True
                adm_indent_level = len(content_line) - len(content_stripped)
                continue
                
            if in_admonition:
                content_indent = len(content_line) - len(content_stripped)
                if content_indent <= adm_indent_level and not content_stripped.startswith('!!!'):
                    in_admonition = False
                    new_lines.append("") 
                    new_lines.append(content_line)
                else:
                    adm_strip = adm_indent_level + 4
                    adm_content = content_line[adm_strip:] if content_line.startswith(' ' * adm_strip) else content_stripped
                    new_lines.append(f"> {adm_content}")
            else:
                new_lines.append(content_line)
                
        elif in_admonition:
            strip_count = adm_indent_level + 4
            content_line = line[strip_count:] if line.startswith(' ' * strip_count) else stripped
            new_lines.append(f"> {content_line}")
        else:
            new_lines.append(line)

    if in_tab:
        new_lines.append("")
        new_lines.append(":::")
        new_lines.append("")
        in_tab = False

    if not is_index:
        reset_prefix = [
            "```{=latex}",
            f"\\setcounter{{section}}{{{section_reset_val}}}",
            "```",
            ""
        ]
        new_lines = reset_prefix + new_lines

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
                    def macro(self, func, name=None):
                        return func
                
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

    temp_build_dir = "pdf_build_workspace"
    os.makedirs(temp_build_dir, exist_ok=True)
    
    print("🧹 Preprocessing markdown file layouts and compiling typography matrix...")
    processed_paths = []
    
    for path in valid_paths:
        safe_name = path.replace('/', '_').replace('\\', '_')
        temp_out_path = os.path.join(temp_build_dir, safe_name)
        
        is_index = "index.md" in os.path.basename(path).lower()
        preprocess_markdown(path, temp_out_path, config, calculated_vars, is_index=is_index)
        processed_paths.append(temp_out_path)

    toc_trigger_path = os.path.join(temp_build_dir, "toc_trigger_temp.md")
    with open(toc_trigger_path, "w", encoding="utf-8") as f:
        f.write("\n\\newpage\n\\tableofcontents\n\\newpage\n")

    compiled_paths = []
    if "index.md" in os.path.basename(valid_paths[0]).lower():
        compiled_paths.append(processed_paths[0])
        compiled_paths.append(toc_trigger_path)
        compiled_paths.extend(processed_paths[1:])
    else:
        compiled_paths = [toc_trigger_path] + processed_paths

    output_pdf = "docs/site_documentation.pdf"
    
    # Write temporary Lua filter script to intercept block content node architectures natively
    lua_filter_path = os.path.join(temp_build_dir, "tabbox_filter.lua")
    with open(lua_filter_path, "w", encoding="utf-8") as f:
        f.write(
            "function Div(el)\n"
            "  if el.classes:includes('tabbox') then\n"
            "    local title = el.attributes['title'] or 'Tab'\n"
            "    table.insert(el.content, 1, pandoc.RawBlock('latex', '\\\\begin{tabbox}{' .. title .. '}'))\n"
            "    table.insert(el.content, pandoc.RawBlock('latex', '\\\\end{tabbox}'))\n"
            "    return el.content\n"
            "  end\n"
            "end\n"
        )
    
    style_file_path = os.path.join(temp_build_dir, "admonition_styles.tex")
    with open(style_file_path, "w", encoding="utf-8") as f:
        f.write(
            "\\usepackage{graphicx}\n"
            "\\usepackage{xcolor}\n"
            "\\usepackage{ragged2e}\n"  
            "\\usepackage{tcolorbox}\n"
            # Modern Preamble Registry Loop Protection Hook
            "\\makeatletter\n"
            "\\providecommand{\\tcb@insert@after@part}{}\n"
            "\\makeatother\n"
            # Gray Admonition Container Style (Maps standard markdown blockquotes)
            "\\renewenvironment{quote}{\n"
            "  \\begin{tcolorbox}[\n"
            "    colback=gray!10,\n"
            "    colframe=gray!40,\n"
            "    boxrule=0.4mm,\n"
            "    arc=1mm,\n"
            "    left=12pt,\n"
            "    right=12pt,\n"
            "    top=10pt,\n"
            "    bottom=10pt,\n"
            "    before skip=\\medskipamount,\n"
            "    after skip=\\medskipamount,\n"
            "    after upper={\\vskip0pt}\n"
            "  ]\n"
            "}{\n"
            "  \\end{tcolorbox}\n"
            "}\n"
            # Crisp solid black heading bar featuring bold white text parameters,
            # framing the block container cleanly inside a 10% grey background panel box.
            "\\newenvironment{tabbox}[1]{\n"
            "  \\begin{tcolorbox}[\n"
            "    colback=gray!10,\n"
            "    colframe=gray!40,\n"
            "    boxrule=0.4mm,\n"
            "    arc=1mm,\n"
            "    title={#1},\n"
            "    coltitle=white,\n"
            "    colbacktitle=black,\n"
            "    fonttitle=\\bfseries\\sffamily,\n"
            "    left=12pt,\n"
            "    right=12pt,\n"
            "    top=12pt,\n"
            "    bottom=12pt,\n"
            "    before skip=\\medskipamount,\n"
            "    after skip=\\medskipamount,\n"
            "    after upper={\\vskip0pt}\n"
            "  ]\n"
            "}{\n"
            "  \\end{tcolorbox}\n"
            "}\n"
        )

    if sys.platform == "darwin":
        pdf_engine = "/Library/TeX/texbin/xelatex" if os.path.exists("/Library/TeX/texbin/xelatex") else "xelatex"
    else:
        pdf_engine = "xelatex"

    cmd = [
        "pandoc",
        *compiled_paths,
        "-o", output_pdf,
        f"--pdf-engine={pdf_engine}",
        f"--lua-filter={lua_filter_path}",
        "-f", "markdown",
        "-V", "fvextra=true",
        "-V", "fvextraoptions=breaklines",
        "--number-sections",
        "--resource-path=.",
        f"--resource-path={docs_dir}",
        "-V", "fontsize=11pt",
        "-V", "papersize=a4",
        "-V", "geometry=margin=2cm",
        f"--include-in-header={style_file_path}"
    ]
    
    if main_font:
        cmd.extend(["-V", f"mainfont={main_font}"])
    if mono_font:
        cmd.extend(["-V", f"monofont={mono_font}"])

    print(f"🚀 Compiling via XeLaTeX pipeline ({pdf_engine})...")
    try:
        subprocess.run(cmd, check=True)
        print(f"\n🎉 Success! Terminal script command formatting and box layouts compiled perfectly. PDF ready at: {output_pdf}")
    except subprocess.CalledProcessError:
        print("\n❌ Error: Pandoc/XeLaTeX failed to compile the PDF.")
    finally:
        if os.path.exists(temp_build_dir):
            shutil.rmtree(temp_build_dir)

if __name__ == "__main__":
    main()