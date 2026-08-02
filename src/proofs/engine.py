from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from tcb import EvidenceVerifier


class ProofEngine:
    REPORTS = (
        "manifest.json",
        "intent-contract.json",
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
    )

    def __init__(self, proofs_root: Path) -> None:
        self.proofs_root = proofs_root.resolve()

    def create(
        self,
        mutation_id: str,
        *,
        reports: dict[str, dict[str, Any]],
        hypothesis: str,
        summary: str,
    ) -> Path:
        proof_dir = (self.proofs_root / mutation_id).resolve()
        if proof_dir.parent != self.proofs_root:
            raise ValueError("invalid mutation id")
        proof_dir.mkdir(parents=True, exist_ok=False)
        missing = set(self.REPORTS) - set(reports)
        if missing:
            raise ValueError(f"missing reports: {', '.join(sorted(missing))}")
        for name in self.REPORTS:
            (proof_dir / name).write_text(
                json.dumps(reports[name], indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        (proof_dir / "hypothesis.md").write_text(hypothesis.rstrip() + "\n", encoding="utf-8")
        (proof_dir / "summary.md").write_text(summary.rstrip() + "\n", encoding="utf-8")
        self._write_checksums(proof_dir)
        EvidenceVerifier().verify(proof_dir)
        return proof_dir

    def update_post_promotion(self, mutation_id: str, report: dict[str, Any]) -> Path:
        proof_dir = (self.proofs_root / mutation_id).resolve()
        if proof_dir.parent != self.proofs_root or not proof_dir.is_dir():
            raise ValueError("invalid or missing proof directory")
        (proof_dir / "post-promotion-report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        self._write_checksums(proof_dir)
        EvidenceVerifier().verify(proof_dir)
        return proof_dir

    def _write_checksums(self, proof_dir: Path) -> None:
        checked_names = sorted((*self.REPORTS, "hypothesis.md", "summary.md"))
        checksums = [
            f"{hashlib.sha256((proof_dir / name).read_bytes()).hexdigest()}  {name}"
            for name in checked_names
        ]
        (proof_dir / "checksums.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")
