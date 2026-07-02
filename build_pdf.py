import os
import sys
import subprocess
import shutil
import toml

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

def preprocess_markdown(file_path, output_path):
    """Converts MkDocs admonitions (!!!) into native Markdown blockquotes (>).

    Injects explicit empty lines upon exit to prevent Pandoc's 'lazy blockquote
    continuation' from accidental merging.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    new_lines = []
    in_admonition = False

    for line in lines:
        if line.lstrip().startswith('!!!'):
            in_admonition = True
            parts = line.strip().split(maxsplit=2)
            adm_type = parts[1] if len(parts) > 1 else "Note"
            adm_title = parts[2].strip('"') if len(parts) > 2 else adm_type.capitalize()
            
            new_lines.append(f"> **{adm_title}**")
            new_lines.append("> ")  # Spacing line for inner markdown tracking
            continue

        if in_admonition:
            if line.startswith('    ') or line.startswith('\t'):
                content_line = line[4:] if line.startswith('    ') else line[1:]
                new_lines.append(f"> {content_line}")
            elif line.strip() == "":
                new_lines.append("> ")
            else:
                # ✨ THE FIX: We hit an unindented line. The admonition is over!
                in_admonition = False
                new_lines.append("")  # Force-inject a true empty line to kill the blockquote
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
        
    temp_build_dir = "pdf_build_workspace"
    os.makedirs(temp_build_dir, exist_ok=True)
    
    print("🧹 Preprocessing markdown files and breaking blockquote continuations...")
    processed_paths = []
    for path in valid_paths:
        safe_name = path.replace('/', '_').replace('\\', '_')
        temp_out_path = os.path.join(temp_build_dir, safe_name)
        preprocess_markdown(path, temp_out_path)
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

    # Configure global quote environment styling override
    style_header_path = os.path.join(temp_build_dir, "admonition_styles.tex")
    with open(style_header_path, "w", encoding="utf-8") as f:
        f.write(
            "\\usepackage{xcolor}\n"
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

    output_pdf = "site_documentation.pdf"
    
    cmd = [
        "pandoc",
        *compiled_paths,
        "-o", output_pdf,
        "--pdf-engine=/Library/TeX/texbin/xelatex",
        "-f", "markdown",
        "-V", "papersize=a4",
        "-V", "geometry=margin=2cm",
        f"--include-in-header={style_header_path}"
    ]
    
    print(f"🚀 Compiling print-ready PDF structure via MacTeX...")
    try:
        subprocess.run(cmd, check=True)
        print(f"\n🎉 Success! Beautifully styled boxes applied safely. PDF generated: {output_pdf}")
    except subprocess.CalledProcessError:
        print("\n❌ Error: Pandoc failed to compile the PDF.")
    finally:
        if os.path.exists(temp_build_dir):
            shutil.rmtree(temp_build_dir)

if __name__ == "__main__":
    main()