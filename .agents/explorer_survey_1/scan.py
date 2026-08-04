import os
import re

search_dirs = [
    r"C:\Users\GABRIELA APSOL\.gemini\antigravity\scratch\aion-os\src",
    r"C:\Users\GABRIELA APSOL\.gemini\antigravity\scratch\aion-os\kernel",
    r"C:\Users\GABRIELA APSOL\.gemini\antigravity\scratch\aion-os\docs",
]

# also search top-level markdown files
top_files = [
    r"C:\Users\GABRIELA APSOL\.gemini\antigravity\scratch\aion-os\README.md",
    r"C:\Users\GABRIELA APSOL\.gemini\antigravity\scratch\aion-os\AION_WHITEPAPER.md",
    r"C:\Users\GABRIELA APSOL\.gemini\antigravity\scratch\aion-os\SECURITY.md",
    r"C:\Users\GABRIELA APSOL\.gemini\antigravity\scratch\aion-os\AGENTS.md",
    r"C:\Users\GABRIELA APSOL\.gemini\antigravity\scratch\aion-os\CLAUDE.md",
]

keywords = ["oracle", "fleet manager", "fleet", "central routing", "centralized", "route"]

results = []

def scan_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for idx, line in enumerate(lines, 1):
            line_lower = line.lower()
            for kw in keywords:
                if kw in line_lower:
                    results.append((file_path, idx, kw, line.strip()))
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

for d in search_dirs:
    for root, dirs, files in os.walk(d):
        if "__pycache__" in root:
            continue
        for file in files:
            file_path = os.path.join(root, file)
            scan_file(file_path)

for tf in top_files:
    if os.path.exists(tf):
        scan_file(tf)

print(f"Total matches found: {len(results)}\n")
for path, line_no, kw, snippet in results:
    print(f"File: {path}:{line_no} [Keyword: '{kw}']")
    print(f"   Snippet: {snippet}\n")
