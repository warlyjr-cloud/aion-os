import os
import re

TARGET_DIR = r"C:\Users\GABRIELA APSOL\.gemini\antigravity\scratch\aion-os"
EXCLUDE_DIRS = {".git", ".agents", "venv", "__pycache__"}

KEYWORDS = [
    "oracle",
    "fleet manager",
    "fleetmanager",
    "fleet_manager",
    "central routing",
    "central_routing",
    "centralized router",
    "centralized routing"
]

SECRET_PATTERNS = [
    (r'(?i)(api[_\-]?key|secret[_\-]?key|private[_\-]?key|auth[_\-]?token|password)\s*=\s*["\'][A-Za-z0-9+/=_\-]{8,}["\']', "Hardcoded API Key / Secret"),
    (r'-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----', "Private Key Header"),
    (r'(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*', "Bearer Token")
]

results = []

for root, dirs, files in os.walk(TARGET_DIR):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for file in files:
        filepath = os.path.join(root, file)
        relpath = os.path.relpath(filepath, TARGET_DIR)
        
        # Don't check binary files like .iso, .qcow2, .png, .jpg
        if file.endswith(('.iso', '.qcow2', '.png', '.jpg', '.jpeg', '.pyc', '.exe', '.dll', '.so', '.tar', '.gz', '.zip')):
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                for line_idx, line in enumerate(lines, 1):
                    # Check keywords
                    for kw in KEYWORDS:
                        if kw in line.lower():
                            # Note: check if it's in SECURITY_AUDIT_R1.md describing the past finding or audit report itself
                            results.append({
                                "file": relpath,
                                "line": line_idx,
                                "match_type": "keyword",
                                "term": kw,
                                "content": line.strip()
                            })
                    # Check secret patterns
                    for pattern, desc in SECRET_PATTERNS:
                        if re.search(pattern, line):
                            results.append({
                                "file": relpath,
                                "line": line_idx,
                                "match_type": "secret",
                                "term": desc,
                                "content": line.strip()
                            })
        except Exception as e:
            print(f"Error reading {relpath}: {e}")

print(f"Total findings: {len(results)}")
for r in results:
    print(f"[{r['match_type'].upper()}] {r['file']}:{r['line']} - Found '{r['term']}' -> {r['content'][:120]}")
