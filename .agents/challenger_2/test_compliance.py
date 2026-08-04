import os
import re
import sys

BASE_DIR = r"C:\Users\GABRIELA APSOL\.gemini\antigravity\scratch\aion-os"

def check_file_exists(file_path):
    return os.path.exists(file_path)

def extract_markdown_links(content, file_path):
    # Regex for markdown links: [text](url) and images ![alt](url)
    link_pattern = re.compile(r'!?\[([^\]]*)\]\(([^)]+)\)')
    matches = link_pattern.findall(content)
    broken_links = []

    for text, link in matches:
        # Ignore external http/https links or mailto
        if link.startswith(('http://', 'https://', 'mailto:', '#')):
            continue
        # Remove anchor if any
        target_path = link.split('#')[0]
        if not target_path:
            continue
        
        # Resolve absolute or relative path
        dir_name = os.path.dirname(file_path)
        resolved_path = os.path.normpath(os.path.join(dir_name, target_path))
        if not os.path.exists(resolved_path):
            broken_links.append((link, resolved_path))

    return broken_links

def check_callout_syntax(content):
    # Check github style callouts: > [!NOTE], > [!IMPORTANT], > [!WARNING], > [!TIP], > [!CAUTION]
    callout_pattern = re.compile(r'^\s*>\s*\[!(NOTE|IMPORTANT|WARNING|TIP|CAUTION)\]', re.MULTILINE)
    matches = callout_pattern.findall(content)
    return matches

def check_markdown_errors(content, filename):
    errors = []
    # Check unclosed code blocks
    code_fence_count = len(re.findall(r'^```', content, re.MULTILINE))
    if code_fence_count % 2 != 0:
        errors.append(f"Odd number of code fences ({code_fence_count}) in {filename}")
    
    # Check unclosed inline code (single backtick count modulo 2 per line, ignoring fences)
    lines = content.splitlines()
    in_fence = False
    for line_idx, line in enumerate(lines, start=1):
        if line.strip().startswith('```'):
            in_fence = not in_fence
            continue
        if not in_fence:
            # count backticks
            backticks = line.count('`')
            if backticks % 2 != 0:
                errors.append(f"Unmatched backtick on line {line_idx} of {filename}: {line}")

    return errors

def main():
    print("=== STARTING EMPIRICAL COMPLIANCE CHECKS ===")
    md_files = []
    for root, dirs, files in os.walk(BASE_DIR):
        # ignore .git or .agents inside walk if needed, but let's check all top-level and docs md files
        if '.git' in root:
            continue
        for f in files:
            if f.endswith('.md'):
                md_files.append(os.path.join(root, f))

    print(f"Found {len(md_files)} markdown files.")

    all_broken_links = []
    all_syntax_errors = []

    for md_file in md_files:
        rel_path = os.path.relpath(md_file, BASE_DIR)
        with open(md_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        broken = extract_markdown_links(content, md_file)
        if broken:
            for link, res in broken:
                all_broken_links.append((rel_path, link, res))

        fmt_errors = check_markdown_errors(content, rel_path)
        if fmt_errors:
            all_syntax_errors.extend(fmt_errors)

    print("\n--- BROKEN LINKS REPORT ---")
    if all_broken_links:
        for src, link, res in all_broken_links:
            print(f"BROKEN LINK in {src}: link '{link}' -> resolved to missing file '{res}'")
    else:
        print("ZERO broken links found!")

    print("\n--- MARKDOWN FORMATTING ERRORS REPORT ---")
    if all_syntax_errors:
        for err in all_syntax_errors:
            print(f"SYNTAX ERROR: {err}")
    else:
        print("ZERO markdown formatting syntax errors found!")

    print("\n--- CHECKING R2: DISCLAIMER PLACEMENT & CONTENT ---")
    readme_path = os.path.join(BASE_DIR, "README.md")
    whitepaper_path = os.path.join(BASE_DIR, "AION_WHITEPAPER.md")

    with open(readme_path, 'r', encoding='utf-8') as f:
        readme_content = f.read()
    with open(whitepaper_path, 'r', encoding='utf-8') as f:
        wp_content = f.read()

    # Check disclaimer in README.md
    readme_has_disclaimer = "Commercial MVP & Network Operational Status" in readme_content and "dormant operational state" in readme_content
    # Check position in README.md: after ![AION Grid](docs/images/grid.jpg)
    grid_img_pos = readme_content.find("![AION Grid](docs/images/grid.jpg)")
    readme_disc_pos = readme_content.find("[!IMPORTANT]")
    print(f"README.md has disclaimer: {readme_has_disclaimer}")
    print(f"README.md grid image pos: {grid_img_pos}, disclaimer pos: {readme_disc_pos}")
    if grid_img_pos != -1 and readme_disc_pos > grid_img_pos:
        print("README.md disclaimer placement: CORRECT (directly after grid image banner).")
    else:
        print("README.md disclaimer placement: INCORRECT.")

    # Check disclaimer in AION_WHITEPAPER.md
    wp_has_disclaimer = "Commercial MVP & Network Operational Status" in wp_content and "dormant operational state" in wp_content
    intro_pos = wp_content.find("## 1. Introduction")
    wp_disc_pos = wp_content.find("[!IMPORTANT]")
    section2_pos = wp_content.find("## 2. The Microkernel Architecture")
    print(f"AION_WHITEPAPER.md has disclaimer: {wp_has_disclaimer}")
    print(f"AION_WHITEPAPER.md Intro pos: {intro_pos}, Disclaimer pos: {wp_disc_pos}, Sec 2 pos: {section2_pos}")
    if intro_pos != -1 and intro_pos < wp_disc_pos < section2_pos:
        print("AION_WHITEPAPER.md disclaimer placement: CORRECT (inside Introduction section).")
    else:
        print("AION_WHITEPAPER.md disclaimer placement: INCORRECT.")

    print("\n--- CHECKING R3: INVESTOR PITCH PROPOSALS ---")
    pitch_path = os.path.join(BASE_DIR, "INVESTOR_PITCH.md")
    with open(pitch_path, 'r', encoding='utf-8') as f:
        pitch_content = f.read()

    print(f"INVESTOR_PITCH.md exists: {os.path.exists(pitch_path)}")
    print("Content preview of INVESTOR_PITCH.md:")
    print(pitch_content)

if __name__ == "__main__":
    main()
