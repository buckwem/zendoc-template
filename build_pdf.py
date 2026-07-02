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
        
    # Extract font configurations directly from site theme profiles
    theme_section = project_section.get('theme', {}) if isinstance(project_section, dict) else config.get('theme', {})
    font_section = theme_section.get('font', {}) if isinstance(theme_section, dict) else {}
    
    main_font = "Inter"
    mono_font = "JetBrains Mono"
    if isinstance(font_section, dict):
        main_font = font_section.get('text', main_font)
        mono_font = font_section.get('code', mono_font)

    temp_build_dir = "pdf_build_workspace"
    os.makedirs(temp_build_dir, exist_ok=True)
    
    print("🧹 Preprocessing markdown file structures...")
    processed_paths = []
    for path in valid_paths:
        safe_name = path.replace('/', '_').replace('\\', '_')
        temp_out_path = os.path.join(temp_build_dir, safe_name)
        preprocess_markdown(path, temp_out_path)
        processed_paths.append(temp_out_path)

    # Destination folder route for Zensical live asset links
    output_pdf = "docs/site_documentation.pdf"
    
    # 1. Inject a layout separation marker block right after the cover page
    toc_marker_path = os.path.join(temp_build_dir, "toc_marker.md")
    with open(toc_marker_path, "w", encoding="utf-8") as f:
        f.write("\n\n<div class=\"cover-break\"></div>\n\n")
        
    compiled_paths = []
    if "index.md" in os.path.basename(valid_paths[0]).lower():
        compiled_paths.append(processed_paths[0])  # Page 1: Cover Page (index.md)
        compiled_paths.append(toc_marker_path)     # Drop zone marker position
        compiled_paths.extend(processed_paths[1:]) # Core text pages
    else:
        compiled_paths = [toc_marker_path] + processed_paths

    temp_html_path = os.path.join(temp_build_dir, "temp_doc.html")
    
    # 2. Use Pandoc to build a clean web HTML map structure with a dynamic TOC
    print("🏗️ Assembling raw semantic HTML document...")
    pandoc_cmd = [
        "pandoc",
        *compiled_paths,
        "-o", temp_html_path,
        "-f", "markdown",
        "-t", "html",
        "-s",  # Builds out a standalone structured file schema
        "--toc"
    ]
    subprocess.run(pandoc_cmd, check=True)
    
    # 3. Read the file stream and move the TOC container below the cover marker
    with open(temp_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    start_toc = html_content.find('<nav id="TOC">')
    if start_toc != -1:
        end_toc = html_content.find('</nav>', start_toc) + len('</nav>')
        toc_html = html_content[start_toc:end_toc]
        
        # Excise the original table of contents block from the top position
        html_content = html_content[:start_toc] + html_content[end_toc:]
        
        # Re-insert the table of contents block right below the cover marker
        marker = '<div class="cover-break"></div>'
        marker_idx = html_content.find(marker)
        if marker_idx != -1:
            insert_idx = marker_idx + len(marker)
            html_content = html_content[:insert_idx] + "\n" + toc_html + "\n" + html_content[insert_idx:]
    
    # 4. Inject web-standard CSS Paged Media rules for page sizing, layout spacing, and fonts
    css_styles = f"""
    <style>
    @page {{
        size: a4;
        margin: 2cm;
    }}
    body {{
        font-family: "{main_font}", "Helvetica", sans-serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #333333;
    }}
    code, pre {{
        font-family: "{mono_font}", "Menlo", monospace;
    }}
    /* Render callout blocks cleanly using uniform web properties */
    blockquote {{
        background-color: #f5f5f5 !important;
        border-left: 1mm solid #cccccc !important; /* Elegant accent border line */
        border: 0.4mm solid #e0e0e0;
        border-radius: 4px !important;
        padding: 14pt !important;
        margin: 16pt 0 !important;
    }}
    blockquote ** {{
        display: block;
        margin-bottom: 6pt;
    }}
    /* Force proper isolated page boundaries using clean CSS breaks */
    #TOC {{
        break-before: page !important;
        break-after: page !important;
    }}
    .cover-break {{
        break-after: page !important;
    }}
    </style>
    """
    html_content = html_content.replace("</body>", f"{css_styles}\n</body>")
    
    final_html_path = os.path.join(temp_build_dir, "final_doc.html")
    with open(final_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    # 5. Compile directly into a polished PDF using WeasyPrint
    print("🚀 Rendering print-ready layout document via WeasyPrint engine...")
    try:
        subprocess.run(["weasyprint", final_html_path, output_pdf], check=True)
        print(f"\n🎉 Success! Verified WeasyPrint PDF is ready: {output_pdf}")
    except subprocess.CalledProcessError:
        print("\n❌ Error: WeasyPrint failed to compile the PDF.")
    finally:
        if os.path.exists(temp_build_dir):
            shutil.rmtree(temp_build_dir)

if __name__ == "__main__":
    main()