from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SECRET_ASSIGNMENT_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"]([^'\"]{4,})['\"]"),
]

SKIP_PATTERNS = [
    re.compile(r"\$\{\{\s*secrets\.", re.IGNORECASE),
    re.compile(r"os\.getenv\(", re.IGNORECASE),
    re.compile(r"load_secret\(", re.IGNORECASE),
    re.compile(r"SecretConfig\.from_environment", re.IGNORECASE),
    re.compile(r"AION_[A-Z0-9_]+", re.IGNORECASE),
]

EXCLUDED_PATHS = {
    ROOT / "scripts" / "secret_safety_check.py",
    ROOT / "src" / "security" / "secrets.py",
}


def scan(path: Path) -> list[str]:
    if path in EXCLUDED_PATHS:
        return []
    if path.is_dir():
        findings: list[str] = []
        for child in sorted(path.iterdir()):
            findings.extend(scan(child))
        return findings
    if path.suffix not in {".py", ".md", ".yml", ".yaml", ".toml", ".json", ".txt"}:
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(pattern.search(stripped) for pattern in SKIP_PATTERNS):
            continue
        if any(pattern.search(stripped) for pattern in SECRET_ASSIGNMENT_PATTERNS):
            return [str(path.relative_to(ROOT))]
    return []


def main() -> None:
    findings = scan(ROOT)
    if findings:
        print("SECRET_SAFETY_FAIL")
        for item in findings:
            print(item)
        raise SystemExit(1)
    print("SECRET_SAFETY_OK")


if __name__ == "__main__":
    main()
