import os
import sys
import subprocess
import shutil
import toml
import re
import importlib.util
import glob
import base64
import urllib.request

# In-process cache so the same emoji is never fetched/read twice within a single build
_TWEMOJI_SVG_CACHE = {}

def resolve_twemoji_svg(unicode_str, icon_registry):
    """Resolves a genuine (non-icon-set) emoji's Unicode sequence to twemoji SVG data.

    Checks the already-discovered icon registry and an on-disk cache under
    ./.icons/twemoji first (fully offline once populated), then falls back to
    fetching the matching asset from the twemoji CDN and caching it locally so
    future builds no longer need network access for that emoji.
    """
    codepoints_full = "-".join(f"{ord(ch):x}" for ch in unicode_str)
    codepoints_stripped = "-".join(f"{ord(ch):x}" for ch in unicode_str if ch != '️')
    candidates = list(dict.fromkeys(c for c in [codepoints_full, codepoints_stripped] if c))

    for cp in candidates:
        if cp in _TWEMOJI_SVG_CACHE:
            return _TWEMOJI_SVG_CACHE[cp]

        abs_path = icon_registry.get(f"twemoji-{cp}") or icon_registry.get(cp)
        if abs_path and os.path.exists(abs_path):
            with open(abs_path, 'r', encoding='utf-8') as f:
                svg_data = f.read()
            _TWEMOJI_SVG_CACHE[cp] = svg_data
            return svg_data

    cache_dir = os.path.join(os.getcwd(), ".icons", "twemoji")
    for cp in candidates:
        cache_path = os.path.join(cache_dir, f"{cp}.svg")
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                svg_data = f.read()
            icon_registry[f"twemoji-{cp}"] = cache_path
            icon_registry.setdefault(cp, cache_path)
            _TWEMOJI_SVG_CACHE[cp] = svg_data
            return svg_data

    for cp in candidates:
        url = f"https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/svg/{cp}.svg"
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                svg_data = resp.read().decode('utf-8')
        except Exception:
            continue

        try:
            os.makedirs(cache_dir, exist_ok=True)
            cache_path = os.path.join(cache_dir, f"{cp}.svg")
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(svg_data)
            icon_registry[f"twemoji-{cp}"] = cache_path
            icon_registry.setdefault(cp, cache_path)
        except Exception:
            pass

        _TWEMOJI_SVG_CACHE[cp] = svg_data
        return svg_data

    return None

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

def discover_icon_dirs(config):
    """Discovers all valid .icons directories across project folders and active Python environments."""
    dirs = [
        os.path.abspath(os.path.join(os.getcwd(), "overrides", ".icons")),
        os.path.abspath(os.path.join(os.getcwd(), ".icons")),
        os.path.abspath(os.path.join(os.getcwd(), "docs", ".icons")),
        os.path.abspath(os.path.join(os.getcwd(), config.get('docs_dir', 'docs'), ".icons"))
    ]
    
    try:
        import site
        site_paths = []
        if hasattr(site, 'getsitepackages'):
            site_paths.extend(site.getsitepackages())
        if hasattr(site, 'getusersitepackages'):
            site_paths.append(site.getusersitepackages())
        
        for sp in site_paths:
            for pkg in ["material", "mkdocs_material", "zensical"]:
                dirs.append(os.path.join(sp, pkg, "templates", ".icons"))
                dirs.append(os.path.join(sp, pkg, ".icons"))
    except Exception:
        pass

    for local_dir in [".venv", "venv", "env"]:
        base_venv = os.path.join(os.getcwd(), local_dir)
        if os.path.isdir(base_venv):
            for pkg in ["material", "mkdocs_material", "zensical"]:
                dirs.extend(glob.glob(os.path.join(base_venv, "lib", "python*", "site-packages", pkg, "templates", ".icons")))
                dirs.extend(glob.glob(os.path.join(base_venv, "lib", "python*", "site-packages", pkg, ".icons")))
                dirs.extend(glob.glob(os.path.join(base_venv, "Lib", "site-packages", pkg, "templates", ".icons")))
                dirs.extend(glob.glob(os.path.join(base_venv, "Lib", "site-packages", pkg, ".icons")))

    valid_dirs = []
    for d in dirs:
        abs_d = os.path.abspath(d)
        if os.path.isdir(abs_d) and abs_d not in valid_dirs:
            valid_dirs.append(abs_d)
    return valid_dirs

def build_icon_registry(icon_dirs):
    """Scans all discovered directory frameworks and indexes vector targets recursively."""
    registry = {}
    for base_dir in icon_dirs:
        if not os.path.isdir(base_dir):
            continue
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.lower().endswith('.svg'):
                    full_path = os.path.abspath(os.path.join(root, file)).replace('\\', '/')
                    rel_path = os.path.relpath(full_path, base_dir).replace('\\', '/').lower()
                    
                    slug = os.path.splitext(rel_path)[0]
                    hyphen_slug = slug.replace('/', '-')
                    
                    registry[hyphen_slug] = full_path
                    registry[hyphen_slug.replace('_', '-')] = full_path
                    registry[hyphen_slug.replace('-', '_')] = full_path
                    
                    parts = slug.split('/')
                    if len(parts) > 1:
                        short_key = f"{parts[0]}-{parts[-1]}"
                        if short_key not in registry:
                            registry[short_key] = full_path
                        
                        if parts[0] == "fontawesome" and len(parts) > 2:
                            fa_key = f"fa-{parts[1]}-{parts[-1]}"
                            registry[fa_key] = full_path
                    
                    flat_key = parts[-1]
                    if flat_key not in registry:
                        registry[flat_key] = full_path
    return registry

def preprocess_markdown(file_path, output_path, config, calculated_vars, icon_registry, placeholder_map, is_index=False):
    """Parses template conditionals, applies global asset filtering, and converts raw shortcodes
    to alphanumeric tokens while ignoring those nested inside code block environments.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.lstrip('\ufeff')

    if content.strip().startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2]

    content = re.sub(r'^.*user-select.*$\n?', '', content, flags=re.MULTILINE | re.IGNORECASE)

    # Strips the website-only heading_counter_reset(page) Jinja macro call (injects a
    # CSS counter-reset <style> block for the live site); the PDF numbers headings
    # separately via the Lua filter's Header() function, so this has no PDF equivalent
    # and would otherwise leak through as literal text since Pandoc doesn't render Jinja.
    content = re.sub(r'^[ \t]*\{\{\s*heading_counter_reset\([^)]*\)\s*\}\}[ \t]*\n?', '', content, flags=re.MULTILINE)

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
            f"{indent}    **[Watch Video]({video_url})**\n\n"
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
        caption_body = match.group(5).strip()
        
        return (
            f"\n\n{indent}<figure class=\"text-center\">\n"
            f"{indent}  <img src=\"{img_url}\" alt=\"{alt_text}\" />\n"
            f"{indent}  <figcaption class=\"text-center-italic\" style=\"margin-top: 8px;\">{caption_body}</figcaption>\n"
            f"{indent}</figure>\n\n"
        )

    content = re.sub(
        r'^([ \t]*)!\[([^\]]*)\]\(([^)]*)\)(?:\{([^}]*)\})?[ \t]*\n(?:[ \t]*\n)*\1///\s*caption\s*\n(.*?)\n\1///',
        zensical_caption_replacer,
        content,
        flags=re.MULTILINE | re.DOTALL
    )

    # AUTOMATED ZENSICAL TABLE CAPTION TRANSLATION ENGINE
    # Converts a caption block following a table into Pandoc's native table-caption
    # syntax ("Table: ..." immediately after the table), which Pandoc renders as a
    # real <caption> bound inside the <table> element - keeping it structurally
    # attached to the table so it can't be orphaned from it across a page break.
    # Caption must come AFTER the table: pymdownx.blocks.caption (used on the live
    # site) attaches a caption block to whichever sibling precedes it, so a caption
    # placed before the table would wrongly attach to the paragraph above instead.
    def table_caption_replacer(match):
        table_lines = match.group(1)
        caption_body = match.group(3).strip()
        return f"{table_lines}\nTable: {caption_body}\n\n"

    content = re.sub(
        r'((?:^[ \t]*\|[^\n]*\n)+)(?:[ \t]*\n)*^([ \t]*)///\s*caption\s*\n(.*?)\n\2///[ \t]*\n?',
        table_caption_replacer,
        content,
        flags=re.MULTILINE | re.DOTALL
    )

    # GLOBAL LOCAL ASSET BASE64 ENCODING ENGINE
    def to_base64_data_uri(img_src, base_dir):
        if img_src.startswith('data:'):
            return img_src
            
        path_part = img_src.split('#')[0]
        if path_part.startswith('file://'):
            path_part = path_part[7:]
            
        img_path = os.path.abspath(os.path.join(base_dir, path_part))
        if not os.path.exists(img_path):
            img_path = os.path.abspath(path_part)
            
        if os.path.exists(img_path) and os.path.isfile(img_path):
            try:
                ext = os.path.splitext(img_path)[1].lower().strip('.')
                mime_type = f"image/{ext}"
                if ext == "svg": mime_type = "image/svg+xml"
                elif ext == "jpg": mime_type = "image/jpeg"
                with open(img_path, 'rb') as f:
                    b64_content = base64.b64encode(f.read()).decode('utf-8')
                return f"data:{mime_type};base64,{b64_content}"
            except Exception:
                pass
        return img_src

    # Helper function to allocate safe alphanumeric tokens
    def register_icon_token(abs_svg_path, raw_svg_data=None):
        try:
            if raw_svg_data:
                b64_payload = base64.b64encode(raw_svg_data.encode('utf-8')).decode('utf-8')
            else:
                if not abs_svg_path or not os.path.exists(abs_svg_path): return None
                with open(abs_svg_path, 'rb') as f:
                    b64_payload = base64.b64encode(f.read()).decode('utf-8')
                    
            for key, val in placeholder_map.items():
                if val == b64_payload: return key
                
            token_key = f"ZICALICONPAD{len(placeholder_map):04d}"
            placeholder_map[token_key] = b64_payload
            return token_key
        except Exception:
            return None

    # AUTOMATED SIMPLE ICONS HTML EMBED INTERCEPTOR ENGINE
    def simple_icons_html_replacer(match):
        full_tag = match.group(0)
        color_slug = match.group(1).strip('/')
        alt_match = re.search(r'alt=["\']([^"\']+)["\']', full_tag, re.IGNORECASE)
        
        if not alt_match:
            return full_tag
            
        icon_name = alt_match.group(1).lower().replace(' icon', '').replace(' ', '-').strip()
        abs_path = icon_registry.get(f"simple-{icon_name}") or icon_registry.get(icon_name)
        
        if abs_path:
            try:
                with open(abs_path, 'r', encoding='utf-8') as svg_file:
                    svg_data = svg_file.read()
                if color_slug:
                    svg_data = re.sub(r'<svg\s+', f'<svg fill="{color_slug}" ', svg_data, flags=re.IGNORECASE)
                token = register_icon_token(None, raw_svg_data=svg_data)
                if token: return token
            except Exception:
                pass
        return full_tag

    content = re.sub(
        r'<img[^>]+src=["\']https?://simpleicons\.org([^"\']*)["\'][^>]*>',
        simple_icons_html_replacer,
        content,
        flags=re.IGNORECASE
    )

    # Encode standard markdown image links directly into the body
    def md_img_replacer(match):
        alt, src = match.group(1), match.group(2)
        return f"![{alt}]({to_base64_data_uri(src, os.path.dirname(file_path))})"
    content = re.sub(r'!\[([^\]]*)\]\(((?!data:)[^)]+)\)', md_img_replacer, content)

    # Encode all inline standard HTML image references directly into the body
    def html_img_replacer(match):
        full_tag = match.group(0)
        src = match.group(1)
        if src.startswith('data:') or 'simpleicons.org' in src:
            return full_tag
        return full_tag.replace(src, to_base64_data_uri(src, os.path.dirname(file_path)))
    content = re.sub(r'<img[^>]+src=["\']([^"\']+)["\']', html_img_replacer, content, flags=re.IGNORECASE)

    content = re.sub(r'^\s*---\s*$', '***', content, flags=re.MULTILINE)

    # AUTOMATED ATTR_LIST TO BRACKETED-SPAN TRANSLATION ENGINE
    # Python-Markdown's inline attr_list syntax (**text**{: .class}) isn't understood by
    # Pandoc; rewrite it to Pandoc's native bracketed-span syntax ([**text**]{.class}).
    def attr_list_span_replacer(match):
        if match.group(1) or match.group(2): return match.group(0)
        inline_text = match.group(3)
        attrs = match.group(4).strip()
        return f"[{inline_text}]{{{attrs}}}"

    content = re.sub(
        r'(```[\s\S]*?```)|(`[^`\n]*`)|(\*\*[^*\n]+\*\*|\*[^*\n]+\*)\{:\s*([^}]+)\}',
        attr_list_span_replacer,
        content
    )

    content = re.sub(r'\{\s*target=[^}]*\}', '', content, flags=re.IGNORECASE)
    content = re.sub(r'^(#{1,6})\s+Footnotes\s*$', r'\1 Footnotes {#custom-footnotes-heading}', content, flags=re.MULTILINE | re.IGNORECASE)

    if re.search(r'<style>.*?\.md-typeset\s+h1\s*\{\s*display:\s*none;?\s*\}.*?</style>', content, flags=re.DOTALL | re.IGNORECASE):
        def hide_matching_h1(match):
            line = match.group(0)
            if '{.' in line: return line.replace('{.', '{.hidden .unnumbered .unlisted .')
            elif '{' in line: return line.replace('{', '{.hidden .unnumbered .unlisted}')
            return f"{line} {{.hidden .unnumbered .unlisted}}"
        content = re.sub(r'^#\s+.*$', hide_matching_h1, content, flags=re.MULTILINE)

    # 🎯 FIX: Syntax-aware shortcut lookup engine skips code elements via alternate capture tracking
    def icon_replacer(match):
        if match.group(1) or match.group(2):
            return match.group(0)
            
        shortcode = match.group(3).lower().strip()
        abs_path = icon_registry.get(shortcode) or icon_registry.get(shortcode.replace('_', '-'))
        
        if not abs_path:
            if shortcode.startswith("material-"):
                alt_shortcode = shortcode.replace("material-", "mdi-", 1)
                abs_path = icon_registry.get(alt_shortcode) or icon_registry.get(alt_shortcode.replace('_', '-'))
            elif shortcode.startswith("mdi-"):
                alt_shortcode = shortcode.replace("mdi-", "material-", 1)
                abs_path = icon_registry.get(alt_shortcode) or icon_registry.get(alt_shortcode.replace('_', '-'))
        
        if not abs_path:
            pure_name = shortcode
            for prefix in ["material-", "mdi-", "fontawesome-", "lucide-", "octicons-", "simple-", "fa-solid-", "fa-regular-", "fa-brands-", "fa-"]:
                if shortcode.startswith(prefix):
                    pure_name = shortcode[len(prefix):]
                    break
            if not abs_path and "-" in shortcode:
                pure_name = shortcode.split("-", 1)[1]
            abs_path = icon_registry.get(pure_name) or icon_registry.get(pure_name.replace('_', '-'))
        
        if not abs_path:
            for suffix in ["-24", "-16", "-12"]:
                abs_path = icon_registry.get(f"{shortcode}{suffix}") or icon_registry.get(f"{pure_name}{suffix}")
                if abs_path: break

        if abs_path:
            token = register_icon_token(abs_path)
            if token: return token
            
        try:
            import emoji
            emojized = emoji.emojize(f":{shortcode}:", language='alias')
            if emojized != f":{shortcode}:":
                svg_data = resolve_twemoji_svg(emojized, icon_registry)
                if svg_data:
                    token = register_icon_token(None, raw_svg_data=svg_data)
                    if token: return token
                return emojized
        except Exception:
            pass
        return match.group(0)

    # Single-pass parsing configuration protecting inline code `...` and fenced blocks ```...```
    # Character class includes +/- so Gemoji-style shortcodes like :+1: and :-1: are matched too
    code_protected_shortcode_pattern = r'(```[\s\S]*?```)|(`[^`\n]*`)|:([a-zA-Z0-9_+-]+):'
    content = re.sub(code_protected_shortcode_pattern, icon_replacer, content)

    # AUTOMATED NATIVE LUCIDE HTML TAG INTERCEPTOR ENGINE
    def lucide_html_replacer(match):
        if match.group(1): return match.group(0)
        icon_name = match.group(2).lower().strip()
        abs_url = icon_registry.get(f"lucide-{icon_name}") or icon_registry.get(icon_name)
        if abs_url:
            token = register_icon_token(abs_url)
            if token: return token
        return match.group(0)

    content = re.sub(r'(```[\s\S]*?```|`[^`\n]*`)|<i[^>]+data-lucide=["\']([^"\']+)["\'][^>]*>.*?</i>', lucide_html_replacer, content, flags=re.IGNORECASE | re.DOTALL)

    # AUTOMATED FONTAWESOME HTML CODES INTERCEPTOR ENGINE
    def fontawesome_html_replacer(match):
        if not match.group(2): return match.group(0)
        style_class = match.group(2).lower().replace('fa-', '')
        icon_name = match.group(3).lower().strip()
        abs_url = icon_registry.get(f"fontawesome-{style_class}-{icon_name}") or icon_registry.get(f"fa-{style_class}-{icon_name}") or icon_registry.get(icon_name)
        if abs_url:
            token = register_icon_token(abs_url)
            if token: return token
        return match.group(0)

    content = re.sub(r'(```.*?```|`[^`]+`)|<i[^>]+class=["\'][^"\']*(fa-solid|fa-regular|fa-brands|fas|far|fab)\s+fa-([a-zA-Z0-9_-]+)[^"\']*["\'][^>]*>.*?</i>', fontawesome_html_replacer, content, flags=re.IGNORECASE | re.DOTALL)

    # AUTOMATED GITHUB OCTICONS HTML INTERCEPTOR ENGINE
    def octicons_html_replacer(match):
        if not match.group(2): return match.group(0)
        icon_name = match.group(2).lower().strip()
        abs_url = icon_registry.get(f"octicons-{icon_name}") or icon_registry.get(icon_name)
        if not abs_url:
            for suffix in ["-24", "-16"]:
                abs_url = icon_registry.get(f"octicons-{icon_name}{suffix}") or icon_registry.get(f"{icon_name}{suffix}")
                if abs_url: break
        if abs_url:
            token = register_icon_token(abs_url)
            if token: return token
        return match.group(0)

    content = re.sub(r'(```.*?```|`[^`]+`)|<span[^>]+class=["\'][^"\']*octicon-([a-zA-Z0-9_-]+)[^"\']*["\'][^>]*>.*?</span>', octicons_html_replacer, content, flags=re.IGNORECASE | re.DOTALL)

    content = re.sub(r'<script[^>]*src=["\']([^"\']*lucide[^"\']*)["\'][^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<script[^>]*>.*?lucide\.createIcons.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)

    # AUTOMATED COMMAND PROMPT INJECTOR ENGINE
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

    # AUTOMATED SUPERFENCES ATTRIBUTE-LIST TRANSLATION ENGINE
    # pymdownx.superfences allows extended fence info strings like ```python hl_lines="2"
    # title="Code blocks"`, but Pandoc's markdown reader only recognises a bare language
    # name straight after the fence - anything trailing it isn't a valid info string, so
    # Pandoc gives up on the whole fence and falls back to a plain paragraph (fence
    # markers and attributes rendered as literal text). Rewrite it to Pandoc's own
    # attribute-list fence syntax (```{.python hl_lines="2" title="Code blocks"}`) so it's
    # parsed as a real, syntax-highlighted code block.
    def superfences_attr_replacer(match):
        indent, lang, attrs = match.group(1), match.group(2), match.group(3).strip()
        return f'{indent}```{{.{lang} {attrs}}}'

    content = re.sub(
        r'^([ \t]*)```[ \t]*([a-zA-Z][\w+-]*)[ \t]+(\S.*)$',
        superfences_attr_replacer,
        content,
        flags=re.MULTILINE
    )

    # THE IMAGE FILTER: Process light and dark mode asset rows line by line
    processed_lines = []
    for line in content.splitlines():
        if '#only-dark' in line: continue  
        if '#only-light' in line: line = line.replace('#only-light', '')  
        processed_lines.append(line)
    content = '\n'.join(processed_lines)

    project_vars = config.get('project', {})
    extra_vars = config.get('extra', {})
    vars_dict = {}
    if isinstance(project_vars, dict): vars_dict.update(project_vars)
    if isinstance(extra_vars, dict): vars_dict.update(extra_vars)
    if isinstance(project_vars, dict):
        proj_extra = project_vars.get('extra', {})
        if isinstance(proj_extra, dict): vars_dict.update(proj_extra)
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
            condition_active = raw_val.lower() in ('true', '1', 'yes', 'on') if isinstance(raw_val, str) else bool(raw_val)
            state_stack.append(('if', condition_active))
            continue
        elif re.search(r'[{(]%\s*else\s*%', line):
            if state_stack and state_stack[-1][0] == 'if':
                state_stack[-1] = ('else', not state_stack[-1][1])
            continue
        elif re.search(r'[{(]%\s*endif\s*%', line):
            if state_stack: state_stack.pop()
            continue
        if not all(is_active for _, is_active in state_stack): continue
        filtered_lines.append(line)

    content = '\n'.join(filtered_lines)

    if is_index:
        content = re.sub(r'[<]![-\s]*.*?[- \s]*[>]', '', content, flags=re.DOTALL)
        content = re.sub(r'\[:material-file-pdf-box: PDF\].*$', '', content, flags=re.MULTILINE)
        def tag_unnumbered(match):
            line = match.group(0)
            if '{.' in line: return line.replace('{.', '{.hidden .unnumbered .unlisted .')
            elif '{' in line: return line.replace('{', '{.hidden .unnumbered .unlisted}')
            return f"{line} {{.hidden .unnumbered .unlisted}}"
        content = re.sub(r'^#{1,6}\s+.*$', tag_unnumbered, content, flags=re.MULTILINE)
        content = f'<div class="cover-page">\n{content}\n</div>\n'

    # INDENTATION PASSTHROUGH STATE MACHINE
    final_lines = content.splitlines()
    new_lines = []
    in_tab, in_admonition, in_gridcard, in_card_item = False, False, False, False
    gridcard_base_indent, tab_indent_level, adm_indent_level = 0, 0, 0

    for line in final_lines:
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)
        if stripped == "":
            new_lines.append("")
            continue

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
                if in_card_item: new_lines.append("\n:::\n")
                in_gridcard, in_card_item = False, False
                new_lines.append("\n:::\n")
                continue
            card_strip_count = gridcard_base_indent + 4
            relative_line = line[card_strip_count:] if line.startswith(' ' * card_strip_count) else line.lstrip()
            rel_stripped = relative_line.lstrip()
            if rel_stripped.startswith('-') and not rel_stripped.startswith('***'):
                if in_card_item: new_lines.append("\n:::\n")
                in_card_item = True
                new_lines.append("\n::: {.gridcard-item}\n")
                title_text = re.sub(r'^-\s+', '', rel_stripped)
                title_text = re.sub(r'\{\s*[^}]*\}', '', title_text)
                title_text = title_text.strip()
                new_lines.append(f'::: {{.gridcard-title}}\n{title_text}\n:::\n')
                continue
            line, stripped = relative_line, rel_stripped
            current_indent = len(line) - len(stripped)

        if in_tab and not stripped.startswith('==='):
            if current_indent <= tab_indent_level:
                new_lines.append("\n:::\n")
                in_tab = False
                if in_admonition:
                    new_lines.append("\n:::\n")
                    in_admonition = False
                
        if in_admonition and not in_tab and not stripped.startswith(('!!!', '???')):
            if current_indent < adm_indent_level + 4:
                in_admonition = False
                new_lines.append("\n:::\n") 

        if stripped.startswith('==='):
            if in_tab: new_lines.append("\n:::\n")
            match = re.search(r'^===\s*["\'\u201c\u2018]?(.*?)["\'\u201d\u2019]?\s*$', stripped)
            tab_title = match.group(1).strip() if match else "Tab"
            tab_indent_level = current_indent
            in_tab, in_admonition = True, False
            new_lines.append(f'\n::: {{.tabbox title="{tab_title}"}}')
            continue
            
        if stripped.startswith(('!!!', '???')):
            if in_admonition: new_lines.append("\n:::\n")
            parts = stripped.split(maxsplit=2)
            adm_type = parts[1].lower() if len(parts) > 1 else "note"
            adm_title = parts[2].strip('"\'') if len(parts) > 2 else adm_type.capitalize()
            new_lines.append(f"\n::: {{.admonition .{adm_type}}}")
            new_lines.append(f"::: {{.admonition-title}}\n{adm_title}\n:::\n")
            in_admonition = True
            adm_indent_level = current_indent
            continue

        if in_tab:
            strip_count = tab_indent_level + 4
            content_line = line[strip_count:] if len(line) >= strip_count and line.startswith(' ' * strip_count) else line.lstrip()
            content_stripped = content_line.lstrip()
            if content_stripped.startswith(('!!!', '???')):
                if in_admonition: new_lines.append("\n:::\n")
                parts = content_stripped.split(maxsplit=2)
                adm_type = parts[1].lower() if len(parts) > 1 else "note"
                adm_title = parts[2].strip('"\'') if len(parts) > 2 else adm_type.capitalize()
                new_lines.append(f"\n::: {{.admonition .{adm_type}}}")
                new_lines.append(f"::: {{.admonition-title}}\n{adm_title}\n:::\n")
                in_admonition = True
                adm_indent_level = len(content_line) - len(content_stripped)
                continue
            if in_admonition:
                content_indent = len(content_line) - len(content_stripped)
                if content_indent < adm_indent_level + 4 and not content_stripped.startswith(('!!!', '???')):
                    in_admonition = False
                    new_lines.append("\n:::\n") 
                if in_admonition:
                    new_lines.append(content_line[adm_indent_level + 4:] if content_line.startswith(' ' * (adm_indent_level + 4)) else content_stripped)
                else:
                    new_lines.append(content_line)
            else:
                new_lines.append(content_line)
        elif in_admonition:
            new_lines.append(line[adm_indent_level + 4:] if line.startswith(' ' * (adm_indent_level + 4)) else stripped)
        else:
            new_lines.append(line)

    if in_tab: new_lines.append("\n:::\n")
    if in_admonition: new_lines.append("\n:::\n")

    # FENCED CODE BLOCK LAZY-CONTINUATION GUARD
    # Pandoc's markdown reader only lets a fenced code block interrupt an
    # immediately preceding text line (list item text, tab/admonition content, etc.)
    # when the fence has zero indentation. Any indented fence - unavoidable for code
    # nested inside list items, tabs, or admonitions - gets swallowed as a lazy
    # continuation of the prior line when there's no blank line before it, so it
    # renders as inline text instead of a code block. Force a separating blank line
    # before every indented fence opener that doesn't already have one.
    guarded_lines = []
    in_fence, fence_char, fence_len = False, None, 0
    for line in new_lines:
        stripped = line.strip()
        if not in_fence:
            fence_match = re.match(r'^(`{3,}|~{3,})', stripped)
            if fence_match:
                indent = len(line) - len(line.lstrip())
                if indent > 0 and guarded_lines and guarded_lines[-1].strip() != "":
                    guarded_lines.append("")
                in_fence = True
                fence_char = fence_match.group(1)[0]
                fence_len = len(fence_match.group(1))
        else:
            close_match = re.match(r'^(`{3,}|~{3,})\s*$', stripped)
            if close_match and close_match.group(1)[0] == fence_char and len(close_match.group(1)) >= fence_len:
                in_fence = False
        guarded_lines.append(line)
    new_lines = guarded_lines

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

def main():
    if not os.path.exists('zensical.toml'):
        print("❌ Error: zensical.toml not found in the current directory.")
        sys.exit(1)
        
    with open('zensical.toml', 'r', encoding='utf-8') as f:
        config = toml.load(f)
        
    project_section = config.get('project', {})
    project_extra = project_section.get('extra', {}) if isinstance(project_section, dict) else {}
    heading_numbering_enabled = bool(project_extra.get('heading_numbering', True)) if isinstance(project_extra, dict) else True
    nav = project_section.get('nav', []) if isinstance(project_section, dict) else []
    if not nav: nav = config.get('nav', [])
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
                    if isinstance(val, (bool, str, int, float)): calculated_vars[attr] = val
                    elif isinstance(val, dict): calculated_vars.update(val)
            if hasattr(macros_module, 'define_env'):
                class AttributeDict(dict):
                    def getattr(self, attr): return self.get(attr)
                    def setattr(self, attr, value): self[attr] = value
                class MockEnv:
                    def __init__(self):
                        self.variables = AttributeDict()
                        self.conf = {}
                    def macro(self, func, name=None): return func
                env_obj = MockEnv()
                macros_module.define_env(env_obj)
                for k, v in env_obj.variables.items():
                    if isinstance(v, (bool, str, int, float)): calculated_vars[k] = v
        except Exception as e:
            print(f"⚠️ Warning: Encountered an issue while executing macros.py: {e}")
        
    theme_section = project_section.get('theme', {}) if isinstance(project_section, dict) else config.get('theme', {})
    font_section = theme_section.get('font', {}) if isinstance(theme_section, dict) else {}
    main_font, mono_font = "Inter", "JetBrains Mono"
    if isinstance(font_section, dict):
        main_font = font_section.get('text', main_font)
        mono_font = font_section.get('code', mono_font)

    copyright_text = project_section.get('copyright') or config.get('copyright') or "Copyright 2026"

    icon_dirs = discover_icon_dirs(config)
    icon_registry = build_icon_registry(icon_dirs)

    temp_build_dir = "pdf_build_workspace"
    os.makedirs(temp_build_dir, exist_ok=True)
    
    # Global state tracker maps unfragmented safe tokens to their Base64 payloads
    global_placeholder_map = {}

    print("🧹 Preprocessing markdown file layouts...")
    processed_paths = []
    for path in valid_paths:
        safe_name = path.replace('/', '_').replace('\\', '_')
        temp_out_path = os.path.join(temp_build_dir, safe_name)
        is_index = "index.md" in os.path.basename(path).lower()
        preprocess_markdown(path, temp_out_path, config, calculated_vars, icon_registry, global_placeholder_map, is_index=is_index)
        processed_paths.append(temp_out_path)

    toc_trigger_path = os.path.join(temp_build_dir, "toc_trigger_temp.md")
    with open(toc_trigger_path, "w", encoding="utf-8") as f:
        f.write("\n<div class=\"page-break\"></div>\n\n# Table of Contents {.unnumbered .unlisted}\n\n<div class=\"page-break\"></div>\n")

    compiled_paths = [processed_paths[0], toc_trigger_path] + processed_paths[1:] if "index.md" in os.path.basename(valid_paths[0]).lower() else [toc_trigger_path] + processed_paths

    output_pdf = "docs/site_documentation.pdf"

    temp_master_md = os.path.join(temp_build_dir, "_temp_master_compiled.md")
    with open(temp_master_md, "w", encoding="utf-8") as out_f:
        for chunk_path in compiled_paths:
            with open(chunk_path, "r", encoding="utf-8") as in_f:
                out_f.write(in_f.read() + "\n\n")

    lua_table_entries = []
    for token_key, b64_payload in global_placeholder_map.items():
        lua_table_entries.append(f'  ["{token_key}"] = "{b64_payload}"')

    lua_icon_db_string = "local icon_db = {\n" + ",\n".join(lua_table_entries) + "\n}\n\n"

    lua_filter_path = os.path.join(temp_build_dir, "tabbox_filter.lua")
    with open(lua_filter_path, "w", encoding="utf-8") as f:
        f.write(lua_icon_db_string)
        f.write(
            "local h1, h2, h3 = 0, 0, 0\n"
            f"local heading_numbering_enabled = {'true' if heading_numbering_enabled else 'false'}\n\n"
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
            "  if heading_numbering_enabled and not block.classes:includes('unnumbered') then\n"
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
            "function Str(el)\n"
            "  if icon_db[el.text] then\n"
            "    return pandoc.RawInline('html', '<img class=\"twemoji\" src=\"data:image/svg+xml;base64,' .. icon_db[el.text] .. '\" />')\n"
            "  end\n"
            "  return nil\n"
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
    
    # Rewrites CSS url(...) references (relative to the source CSS file) to base64 data
    # URIs, since the compiled CSS is written to a different directory (temp_build_dir)
    # where the original relative paths would no longer resolve.
    def inline_css_urls(css_text, css_dir):
        def url_replacer(match):
            quote, ref = match.group(1), match.group(2)
            if ref.startswith(('data:', 'http://', 'https://', '#')):
                return match.group(0)
            asset_path = os.path.abspath(os.path.join(css_dir, ref))
            if not os.path.isfile(asset_path):
                return match.group(0)
            ext = os.path.splitext(asset_path)[1].lower().strip('.')
            mime_type = {"svg": "image/svg+xml", "jpg": "image/jpeg"}.get(ext, f"image/{ext}")
            with open(asset_path, 'rb') as f:
                b64_payload = base64.b64encode(f.read()).decode('utf-8')
            return f'url({quote}data:{mime_type};base64,{b64_payload}{quote})'
        return re.sub(r'url\((["\']?)([^)"\']+)\1\)', url_replacer, css_text)

    temp_compiled_css = os.path.join(temp_build_dir, "_temp_compiled_print.css")
    original_css_content = ""
    for css_src in [os.path.join(docs_dir, "stylesheets", "extra.css"), os.path.join(docs_dir, "stylesheets", "print.css")]:
        if os.path.exists(css_src):
            with open(css_src, "r", encoding="utf-8") as f:
                original_css_content += inline_css_urls(f.read(), os.path.dirname(css_src)) + "\n"

    cleaned_original_css = re.sub(r'@charset[^;{]*(\{.*?\}|;)', '', original_css_content, flags=re.IGNORECASE | re.DOTALL)
    cleaned_original_css = re.sub(r'^.*user-select.*$\n?', '', cleaned_original_css, flags=re.MULTILINE | re.IGNORECASE)

    clean_copyright = copyright_text.strip().replace('\n', ' ').replace('\r', ' ')
    sanitized_copyright = clean_copyright.replace('&copy;', '©').replace('&#169;', '©')
    css_escaped_copyright = "".join(f"\\{ord(char):04X} " if ord(char) > 127 else char for char in sanitized_copyright)
    safe_copyright = css_escaped_copyright.replace('"', '\\"')

    css_blueprint = """
/* ==========================================================================
   DYNAMIC TYPOGRAPHY CONFIGURATION (Injected from settings)
   ========================================================================== */
body {
    font-family: "__MAIN_FONT__", sans-serif !important;
}
h1, h2, h3, h4, h5, h6 {
    font-family: "__MAIN_FONT__", sans-serif !important;
}
pre, code {
    font-family: "__MONO_FONT__", monospace !important;
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
    @bottom-center { content: none !important; }
    @bottom-left {
        content: "__COPYRIGHT__" !important;
        font-family: "__MAIN_FONT__", sans-serif !important;
        font-size: 10pt !important;
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
        font-size: 10pt !important;
        color: #555555 !important;
        vertical-align: top !important;
        border-top: 1px solid #e2e8f0 !important;
        padding-top: 8px !important;
        width: 15% !important;
        text-align: right !important;
    }
}
@page :first {
    @bottom-left { content: none !important; border-top: none !important; }
    @bottom-right { content: none !important; border-top: none !important; }
}

.page-break, .cover-page {
    page-break-after: always;
    break-after: always;
}
h1 { break-before: page !important; }
.cover-page h1 { break-before: auto !important; }

/* ==========================================================================
   TABLE LAYOUT STYLING MATRIX
   ========================================================================== */
table {
    border-collapse: collapse !important;
    border: 0.25pt solid #555555 !important;
    width: 100% !important;
    margin: 1.2em 0 !important;
    page-break-inside: auto !important;
    break-inside: auto !important;
}
/* Rows never split mid-row - a page break only ever falls between rows */
table tr {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
}
/* Repeats the header row on every page the table spans across */
thead {
    display: table-header-group;
}
/* Bound inside <table> itself, so it can never be separated from the start
   of the table across a page break (unlike a plain preceding paragraph). */
table caption {
    caption-side: top !important;
    text-align: center !important;
    font-style: italic !important;
    margin-bottom: 8px !important;
    page-break-after: avoid !important;
    break-after: avoid-page !important;
}
table th { background-color: rgba(0, 0, 0, 0.1) !important; font-weight: bold !important; }
table th, table td {
    padding: 8px 12px !important;
    border-top: 0.25pt solid #555555 !important;
    border-bottom: 0.25pt solid #555555 !important;
    border-left: none !important; border-right: none !important;
}
table tr:first-child th, table tr:first-child td { border-top: none !important; }
table tr:last-child td { border-bottom: none !important; }

/* ==========================================================================
   ADMONITIONS & TABS LAYOUT OVERRIDES
   ========================================================================== */
blockquote {
    background-color: #f8fafc !important; border-left: 4px solid #cbd5e1 !important;
    padding: 12px 16px !important; margin: 1em 0 !important;
}
.tabbox-container {
    border: 1px solid #cbd5e1; border-radius: 4px; margin: 1em 0;
    page-break-inside: auto !important; break-inside: auto !important;
    -webkit-box-decoration-break: clone !important; box-decoration-break: clone !important;
}
.tabbox-header {
    background-color: rgba(0, 0, 0, 0.1) !important; color: #000000 !important;
    font-weight: bold; padding: 8px 12px; font-size: 10pt;
    page-break-after: avoid !important; break-after: avoid !important;
}
.tabbox-body {
    background-color: rgba(0, 0, 0, 0.05) !important; padding: 12px;
    page-break-inside: auto !important; break-inside: auto !important;
    -webkit-box-decoration-break: clone !important; box-decoration-break: clone !important;
}
.admonition {
    border-left: 4px solid #448aff !important; background-color: #f8fafc !important;
    padding: 14px 18px !important; margin: 1.2em 0 !important;
    page-break-inside: auto !important; break-inside: auto !important;
    -webkit-box-decoration-break: clone !important; box-decoration-break: clone !important;
}
.admonition-title {
    font-weight: bold !important; margin-bottom: 8px !important; font-size: 10.5pt !important;
    color: #448aff !important; page-break-after: avoid !important; break-after: avoid !important;
}

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
.gridcard-matrix { display: block !important; margin: 1.5em 0 !important; }
.gridcard-item {
    background-color: rgba(0, 0, 0, 0.025) !important; border: none !important;                           
    padding: 16px !important; margin-bottom: 1em !important; border-radius: 4px !important;
    page-break-inside: avoid; break-inside: avoid;
}
.gridcard-title {
    font-weight: bold !important; font-size: 13pt !important; margin-bottom: 12px !important;
    display: block !important; color: #111111 !important; page-break-after: avoid !important; break-after: avoid !important;
}
.gridcard-title p { font-weight: bold !important; font-size: 13pt !important; color: #111111 !important; margin: 0 !important; display: inline !important; }

pre, code { font-family: "__MONO_FONT__", monospace !important; }
pre { padding: 10px !important; border-radius: 4px !important; margin: 1em 0 !important; white-space: pre-wrap !important; background-color: rgba(0, 0, 0, 0.125) !important; }
code { padding: 2px 4px !important; border-radius: 3px !important; background-color: transparent !important; }
/* Multi-line <code> inside <pre> is a single inline box split across hard line
   breaks; without this, the padding above lands only on the first line (default
   box-decoration-break: slice), making it look indented relative to the rest. */
pre code { padding: 0 !important; }

/* ==========================================================================
   ADVANCED GLOBAL IMAGE AND VECTOR PROTECTION STANDARDS
   ========================================================================== */
img {
    max-width: 100% !important;
}
/* Keeps an image and its /// caption /// figcaption together as one atomic
   unit, so the caption can never be pushed to a page apart from its image. */
figure {
    page-break-inside: avoid !important;
    break-inside: avoid-page !important;
}
img.twemoji, i.fa-solid, i.fa-regular, i.fa-brands, i.material-icons, i[class*="fa-"], span[class*="octicon-"], .octicon {
    image-resolution: 96dpi !important;
    font-size: 1.1em !important;
    height: 1.1em !important;
    width: 1.1em !important;
    max-width: none !important;
    max-height: none !important;
    display: inline-block !important;
    vertical-align: -0.2em !important;
    margin: 0 2px !important;
    background: transparent !important;
}
.cover-page img {
    display: block !important;
    margin: 0.5cm auto 0.2cm auto !important;
    max-width: 65% !important;
    max-height: 3.5cm !important;
    object-fit: contain !important;
    image-resolution: 96dpi !important;
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
.title-ctr-1, .title-ctr-2, .title-ctr-3, .title-ctr-4, .title-ctr-5, .title-ctr-6,
.title-ctr-b1, .title-ctr-b2, .title-ctr-b3, .title-ctr-b4, .title-ctr-b5, .title-ctr-b6 { text-align: center; display: block; }
.title-left-1, .title-left-2, .title-left-3, .title-left-4, .title-left-5, .title-left-6,
.title-left-b1, .title-left-b2, .title-left-b3, .title-left-b4, .title-left-b5, .title-left-b6 { text-align: left; display: block; }
.title-ctr-b1, .title-ctr-b2, .title-ctr-b3, .title-ctr-b4, .title-ctr-b5, .title-ctr-b6,
.title-left-b1, .title-left-b2, .title-left-b3, .title-left-b4, .title-left-b5, .title-left-b6 { font-weight: bold; }
[class*="title-"][class*="-1"] { font-size: 26pt; line-height: 32pt; margin-bottom: 0.6em; }
[class*="title-"][class*="-2"] { font-size: 22pt; line-height: 28pt; margin-bottom: 0.6em; }
[class*="title-"][class*="-3"] { font-size: 18pt; line-height: 24pt; margin-bottom: 0.6em; }
[class*="title-"][class*="-4"] { font-size: 15pt; line-height: 20pt; margin-bottom: 0.6em; }
[class*="title-"][class*="-5"] { font-size: 13pt; line-height: 17pt; margin-bottom: 0.6em; }
[class*="title-"][class*="-6"] { font-size: 11pt; line-height: 15pt; margin-bottom: 0.6em; }

.gridcard-matrix, .gridcard-item,
.text-center, .text-right, .text-justify,
.text-center-italic, .text-right-italic, .text-justify-italic {
    page-break-inside: auto !important;
    break-inside: auto !important;
}
.tabbox-header {
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
        os.path.join(temp_build_dir, "_temp_master_compiled.md"),                
        "-o", output_pdf,
        "--pdf-engine=weasyprint",
        "--pdf-engine-opt=-q",
        "--mathjax",
        f"--lua-filter={lua_filter_path}",
        "-f", "markdown",
        "--resource-path=.",
        f"--resource-path={docs_dir}",
        f"--css={temp_compiled_css}"   
    ]

    print("🚀 Processing via unified layout configuration framework...")
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