from pathlib import Path

import pytest

from audit import AuditLog
from tcb import EvidenceError, EvidenceVerifier
from vek import EvolutionEngine


def test_proof_checksums_detect_tampering(tmp_path: Path) -> None:
    record = EvolutionEngine(tmp_path).plan("Process and reduce video file sizes")
    proof = tmp_path / str(record.proof_path)
    assert EvidenceVerifier().verify(proof)
    (proof / "candidate.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(EvidenceError, match="checksum mismatch"):
        EvidenceVerifier().verify(proof)


def test_audit_hash_chain_detects_tampering(tmp_path: Path) -> None:
    log = AuditLog(tmp_path / "audit.jsonl")
    log.append("one", actor="tester")
    log.append("two", actor="tester")
    assert log.verify()
    content = log.path.read_text(encoding="utf-8").replace(
        '"event_type":"one"', '"event_type":"tampered"'
    )
    log.path.write_text(content, encoding="utf-8")
    log = AuditLog(tmp_path / "audit.jsonl")
    with pytest.raises(ValueError, match="tampered audit event"):
        log.verify()
