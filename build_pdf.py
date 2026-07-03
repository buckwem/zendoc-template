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
    """Parses template conditionals, applies global light/dark asset filtering, and compiles

    custom typography classes into balanced block-level environments to ensure perfect alignment.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # ☀️/🌙 THE IMAGE FILTER: Discard dark mode rows and sanitize light mode configurations
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

    # 🎨 THE UNIFIED COVER PAGE COMPLIER ENGINE
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
            
            # Convert internal HTML breaks and strip out tracking layout newlines
            text = re.sub(r'<br\s*/?>', lambda m: r' \\ ', text, flags=re.IGNORECASE)
            text = re.sub(r'\s+', ' ', text)
            
            # Sanitize character strings inside the custom LaTeX block
            text = text.replace('_', '\\_').replace('&', '\\&').replace('%', '\\%').replace('$', '\\$')
            
            # ✨ THE TYPOGRAPHY MATRIX OVERHAUL: We explicitly set absolute point sizes
            # and matching baseline line-height steps to scale beautifully on print profiles.
            size_map = {
                '1': r'\fontsize{26pt}{32pt}\selectfont',  # ~1.5rem prominent title
                '2': r'\fontsize{22pt}{28pt}\selectfont',  # ~1.4rem
                '3': r'\fontsize{18pt}{24pt}\selectfont',  # ~1.3rem crisp metadata block
                '4': r'\fontsize{15pt}{20pt}\selectfont',  # ~1.2rem
                '5': r'\fontsize{13pt}{17pt}\selectfont',  # ~1.1rem
                '6': r'\fontsize{11pt}{15pt}\selectfont'   # ~1.0rem
            }
            latex_size = size_map.get(size_num, r'\fontsize{12pt}{16pt}\selectfont')
            latex_bold = r'\bfseries ' if is_bold else ''
            latex_align = r'\centering' if align == 'ctr' else r'\raggedright'
            
            return f"\n{{{latex_align} {latex_size} {latex_bold}{text}\\par}}\n"

        # Quote-agnostic attribute scanner translates custom elements seamlessly
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
                    final_cover_lines.append(f"{{\\centering \\normalsize {trimmed}\\par}}")
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

    # 🧹 ADMONITION BOX CONVERSION
    final_lines = content.splitlines()
    new_lines = []
    in_admonition = False

    for line in final_lines:
        if line.lstrip().startswith('!!!'):
            in_admonition = True
            parts = line.strip().split(maxsplit=2)
            adm_type = parts[1] if len(parts) > 1 else "Note"
            adm_title = parts[2].strip('"') if len(parts) > 2 else adm_type.capitalize()
            
            new_lines.append(f"> **{adm_title}**")
            new_lines.append("> ")  
            continue

        if in_admonition:
            if line.startswith('    ') or line.startswith('\t'):
                content_line = line[4:] if line.startswith('    ') else line[1:]
                new_lines.append(f"> {content_line}")
            elif line.strip() == "":
                new_lines.append("> ")
            else:
                in_admonition = False
                new_lines.append("")  
                new_lines.append(line)
        else:
            new_lines.append(line)

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

    # Read calculated macros.py values via runtime mock environment context
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
    
    style_file_path = os.path.join(temp_build_dir, "admonition_styles.tex")
    with open(style_file_path, "w", encoding="utf-8") as f:
        f.write(
            "\\usepackage{graphicx}\n"
            "\\usepackage{xcolor}\n"
            "\\usepackage{ragged2e}\n"  
            "\\usepackage[framemethod=default]{mdframed}\n"
            "\\renewenvironment{quote}{\n"
            "  \\begin{mdframed}[\n"
            "    backgroundcolor=gray!10,\n"
            "    linecolor=gray!40,\n"
            "    linewidth=0.4mm,\n"
            "    roundcorner=1mm,\n"
            "    innerleftmargin=12pt,\n"
            "    innerrightmargin=12pt,\n"
            "    innertopmargin=10pt,\n"
            "    innerbottommargin=10pt,\n"
            "    skipabove=\\medskipamount,\n"
            "    skipbelow=\\medskipamount\n"
            "  ]\n"
            "}{\n"
            "  \\end{mdframed}\n"
            "}\n"
        )

    if sys.platform == "darwin":
        pdf_engine = "/Library/TeX/texbin/xelatex" if os.path.exists("/Library/TeX/texbin/xelatex") else "xelatex"
    else:
        pdf_engine = "xelatex"

    # ✨ THE GLOBAL BASES FIX: Configured standard 12pt document baseline scaling 
    # to elevate body readability text across all child pages dynamically.
    cmd = [
        "pandoc",
        *compiled_paths,
        "-o", output_pdf,
        f"--pdf-engine={pdf_engine}",
        "-f", "markdown",
        "--resource-path=.",
        f"--resource-path={docs_dir}",
        "-V", "fontsize=12pt",
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
        print(f"\n🎉 Success! Custom site typography and layout utilities applied. PDF ready at: {output_pdf}")
    except subprocess.CalledProcessError:
        print("\n❌ Error: Pandoc/XeLaTeX failed to compile the PDF.")
    finally:
        if os.path.exists(temp_build_dir):
            shutil.rmtree(temp_build_dir)

if __name__ == "__main__":
    main()