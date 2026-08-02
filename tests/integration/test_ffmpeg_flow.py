from pathlib import Path

import pytest

from tcb import EvidenceVerifier, MutationState
from vek import EvolutionEngine


def test_ffmpeg_proof_approval_promotion_and_rollback(tmp_path: Path) -> None:
    engine = EvolutionEngine(tmp_path)
    record = engine.plan("Preciso processar, converter e reduzir arquivos de vídeo")
    assert record.state is MutationState.AWAITING_APPROVAL
    assert len(record.candidates) == 2
    assert all(candidate.simulated for candidate in record.candidates)
    assert all(
        "package.propose:ffmpeg" in candidate.capabilities for candidate in record.candidates
    )
    approved = engine.approve(record.mutation_id, approved_by="human@example.test")
    assert approved.state is MutationState.APPROVED
    promoted = engine.promote(record.mutation_id)
    assert promoted.state is MutationState.MONITORING
    assert engine.current_generation() is not None
    rolled_back = engine.rollback(record.mutation_id)
    assert rolled_back.state is MutationState.ROLLED_BACK
    assert engine.current_generation() is None
    assert EvidenceVerifier().verify(tmp_path / str(record.proof_path))
    assert engine.audit.verify()


def test_rejected_mutation_cannot_be_promoted(tmp_path: Path) -> None:
    engine = EvolutionEngine(tmp_path)
    record = engine.plan("I need to process video safely")
    rejected = engine.reject(
        record.mutation_id, reason="insufficient real build evidence", rejected_by="human"
    )
    assert rejected.state is MutationState.REJECTED
    with pytest.raises(ValueError):
        engine.promote(record.mutation_id)
