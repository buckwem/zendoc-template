import subprocess
import sys
import os

def build_pdf(input_md, output_pdf, css_stylesheet):
    """
    Compiles a Markdown file into a PDF using Pandoc and WeasyPrint,
    applying a custom CSS stylesheet for print layout.
    """
    # Quick sanity checks
    if not os.path.exists(input_md):
        print(f"❌ Error: Input file '{input_md}' not found.")
        sys.exit(1)
    if not os.path.exists(css_stylesheet):
        print(f"⚠️ Warning: CSS file '{css_stylesheet}' not found. Output might look unstyled.")

    print(f"🚀 Compiling '{input_md}' to '{output_pdf}' using WeasyPrint backend...")

    # Construct the Pandoc command
    command = [
        "pandoc",
        input_md,
        "-o", output_pdf,
        "--pdf-engine=weasyprint",
        f"--css={css_stylesheet}",
        "--from=markdown+gfm_auto_identifiers", # Supports GitHub Flavored Markdown
        # "--toc",                            # Uncomment if you want an auto-generated Table of Contents
    ]

    try:
        # Run the command and capture output if it fails
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        print("✨ PDF successfully generated!")
        
    except subprocess.CalledProcessError as e:
        print("❌ Error: Pandoc/WeasyPrint compilation failed.", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: Pandoc is not installed or not in your system PATH.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # Define your files here (or use sys.argv to pass them via terminal)
    INPUT_MARKDOWN = "document.md"
    OUTPUT_PDF = "final_output.pdf"
    
    # Points to the 'stylesheets' subdirectory safely across all operating systems
    STYLESHEET = os.path.join("stylesheets", "print.css")

    build_pdf(INPUT_MARKDOWN, OUTPUT_PDF, STYLESHEET)