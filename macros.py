import os
import subprocess
import shutil
from pathlib import Path

# This function is called by Zensical to identify whether the documentation is being built
# in a Surrey GitLab CI/CD Pipeline or if the repository URL contains the domain `surrey.gitlab.ac.uk`.
# It sets a boolean variable `is_surrey` in the environment variables, which can be used in Markdown
# files to conditionally display content based on the build environment.

def define_env(env):
    target_domain = 'surrey.ac.uk'

    # Check 1: GitLab CI/CD Pipeline environment
    is_surrey_ci = os.getenv('CI_SERVER_HOST') == target_domain
    
    # Check 2: Local Git Remote Origin (Perfect for local 'zensical serve' testing)
    is_surrey_local_git = False
    try:
        # Automatically asks your local folder where its remote points
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"], 
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        if target_domain in remote_url:
            is_surrey_local_git = True
    except Exception:
        # Fails silently if git isn't installed or initialized in this directory
        pass

    # Check 3: Brute-force string scan of Zensical's entire config scope
    is_surrey_in_config = False
    if hasattr(env, 'config'):
        is_surrey_in_config = target_domain in str(env.config)
    if not is_surrey_in_config and hasattr(env, 'variables'):
        is_surrey_in_config = target_domain in str(env.variables)

    # Combine all checks: If ANY layer detects the domain, set to True
    final_result = is_surrey_ci or is_surrey_local_git or is_surrey_in_config

    # Live console debugging log (Visible when you run zensical serve/build)
    # print(f"\n[Is Surrey Macro Debug] CI: {is_surrey_ci} | Local Git: {is_surrey_local_git} | Config Scan: {is_surrey_in_config} => is_surrey = {final_result}\n")

    # Bind the variable to your markdown files
    env.variables['is_surrey'] = final_result
    env.variables['is_surrey'] = False  # This line is for testing purposes; remove it in production to enable the macro.

    # ==========================================
    # 2. CUSTOM MACROS
    # ==========================================
    @env.macro
    def copy_file(source: str, destination: str):
        """Copies a resource to the specified destination path during build time.
        Useful for including images, PDFs, or other assets in your documentation.
        or to override default assets in the template (like logos or favicons)."""
        src_path = Path(source)
        dest_path = Path(destination)
        
        if not src_path.exists():
            return f"**Macro Error:** Source file `{source}` not found."
            
        # Automatically make parent directories if they don't exist yet
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the file (shutil.copy2 preserves metadata)
        shutil.copy2(src_path, dest_path)
        
        # Return a silent HTML comment so it doesn't print text on your page
        return f""
    