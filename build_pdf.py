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
    """Parses template conditionals, applies dark/light asset filtering, and wraps 

    typography and layout utility classes using safe inline raw LaTeX structural tags.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # ☀️/🌙 THE IMAGE FILTER: Discard dark mode images and strip light mode hash tags
    processed_lines = []
    for line in content.splitlines():
        if '#only-dark' in line:
            continue  # Discard the dark-mode graphic row completely
        if '#only-light' in line:
            line = line.replace('#only-light', '')  # Keep asset but strip the trailing hash
        processed_lines.append(line)
    content = '\n'.join(processed_lines)

    # Collate static configurations with runtime macro definitions
    project_vars = config.get('project', {})
    extra_vars = config.get('extra', {})
    vars_dict = {}
    if isinstance(project_vars, dict): vars_dict.update(project_vars)
    if isinstance(extra_vars, dict): vars_dict.update(extra_vars)
    vars_dict.update(calculated_vars)

    lines = content.splitlines()
    filtered_lines = []
    state_stack = []

    # 1. Evaluate Template Conditional Rules
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

    # 🎨 COVER PAGE & SYSTEM CSS MATRIX TRANSLATION
    if is_index:
        # Strip web-specific layout container blocks
        content = re.sub(r'<div[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'</div>', '', content, flags=re.IGNORECASE)

        # Matched style configurations: 18 Title Classes
        def convert_html_typography(match):
            align = match.group(1)          # 'ctr' or 'left'
            is_bold = bool(match.group(2))     # True if '-b' is matched
            size_num = match.group(3)        # '1' through '6'
            text = match.group(4).strip()
            
            text = re.sub(r'<br\s*/?>', r' \\\\ ', text, flags=re.IGNORECASE)
            
            size_map = {
                '1': r'\LARGE', '2': r'\Large', '3': r'\large',
                '4': r'\normalsize', '5': r'\small', '6': r'\footnotesize'
            }
            latex_size = size_map.get(size_num, r'\normalsize')
            latex_bold = r' \bfseries' if is_bold else ''
            latex_align = r'\centering' if align == 'ctr' else r'\raggedright'
            
            return f" `{{{latex_align} {latex_size}{latex_bold}`{{=latex}} {text}`\\par}}`{{=latex}} "

        content = re.sub(
            r'<p\s+class="title-(ctr|left)(-b)?([1-6])"[^>]*>(.*?)</p>',
            convert_html_typography,
            content,
            flags=re.DOTALL | re.IGNORECASE
        )

        # ✨ THE LAYOUT UTILITY FIX: Dynamic mapping parser for general text classes
        def convert_html_text_alignment(match):
            align = match.group(1).lower()  # 'center', 'right', 'justify'
            text = match.group(2).strip()
            
            text = re.sub(r'<br\s*/?>', r' \\\\ ', text, flags=re.IGNORECASE)
            
            if align == 'center':
                latex_align = r'\centering'
            elif align == 'right':
                latex_align = r'\raggedleft'
            else:
                latex_align = r'\justifying'
                
            return f" `{{{latex_align}`{{=latex}} {text}`\\par}}`{{=latex}} "

        content = re.sub(
            r'<p\s+class="text-(center|right|justify)"[^>]*>(.*?)</p>',
            convert_html_text_alignment,
            content,
            flags=re.DOTALL | re.IGNORECASE
        )

        # Convert web line breaks into clear LaTeX vertical spacing blocks
        content = re.sub(r'<br\s*/?>', r'\n\n```{=latex}\n\\vspace{1.5cm}\n```\n\n', content, flags=re.IGNORECASE)
        
        # Sandwich the cover text layout using standalone, separate block fences.
        content = (
            "```{=latex}\n"
            "\\begin{titlepage}\n"
            "\\centering\n"
            "\\vspace*{2cm}\n"
            "```\n\n"
            + content +
            "\n\n```{=latex}\n"
            "\\end{titlepage}\n"
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
            "\\usepackage{ragged2e}\n"  # Added package reference to unlock the \justifying switch environment
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

    cmd = [
        "pandoc",
        *compiled_paths,
        "-o", output_pdf,
        f"--pdf-engine={pdf_engine}",
        "-f", "markdown",
        "--resource-path=.",
        f"--resource-path={docs_dir}",
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