from __future__ import annotations

import hashlib
from pathlib import Path


class EvidenceError(ValueError):
    pass


class EvidenceVerifier:
    REQUIRED_FILES = frozenset(
        {
            "manifest.json",
            "intent-contract.json",
            "hypothesis.md",
            "baseline.json",
            "candidate.json",
            "policy-report.json",
            "build-report.json",
            "test-report.json",
            "security-report.json",
            "benchmark-report.json",
            "adversarial-report.json",
            "comparison.json",
            "provenance.json",
            "rollback-plan.json",
            "post-promotion-report.json",
            "summary.md",
            "checksums.txt",
        }
    )

    def verify(self, proof_dir: Path) -> bool:
        missing = sorted(name for name in self.REQUIRED_FILES if not (proof_dir / name).is_file())
        if missing:
            raise EvidenceError(f"missing evidence files: {', '.join(missing)}")
        entries = self._parse_checksums(proof_dir / "checksums.txt")
        expected = set(self.REQUIRED_FILES) - {"checksums.txt"}
        if set(entries) != expected:
            raise EvidenceError("checksum manifest does not exactly cover required evidence")
        for relative_name, expected_digest in entries.items():
            actual = hashlib.sha256((proof_dir / relative_name).read_bytes()).hexdigest()
            if actual != expected_digest:
                raise EvidenceError(f"checksum mismatch: {relative_name}")
        return True

    @staticmethod
    def _parse_checksums(path: Path) -> dict[str, str]:
        entries: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            digest, separator, name = line.partition("  ")
            if separator != "  " or len(digest) != 64 or not name or "/" in name or "\\" in name:
                raise EvidenceError("malformed checksum manifest")
            if name in entries:
                raise EvidenceError(f"duplicate checksum entry: {name}")
            entries[name] = digest
        return entries
