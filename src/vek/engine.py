from __future__ import annotations

import hashlib
import unicodedata
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from actions import SemanticAction
from audit import AuditLog
from capabilities import CapabilityGrant, CapabilityManager
from evolution import MutationRecord, MutationStore
from executor import SafeExecutor
from genome import SystemGenome
from intent import IntentContract
from model_council import ModelCouncil
from policy import PolicyDecision, PolicyEngine
from population import CandidateArchive, EvolutionPopulation, LineageGraph, ParetoSelector
from proofs import ProofEngine
from providers import MockProvider, Provider
from tcb import ActionValidator, EvidenceVerifier, MutationState


class EvolutionEngine:
    """Offline RSI-2 workflow. It creates proof-carrying proposals but never mutates the host."""

    def __init__(self, project_root: Path, provider: Provider | None = None) -> None:
        self.project_root = project_root.resolve()
        self.state_root = self.project_root / ".aion-state"
        self.state_root.mkdir(parents=True, exist_ok=True)
        self.mutations = MutationStore(self.state_root / "mutations")
        self.audit = AuditLog(self.state_root / "audit.jsonl")
        if provider is not None:
            self.provider = provider
        else:
            import os
            if os.getenv("ANTHROPIC_API_KEY"):
                from providers.llm import AnthropicProvider
                self.provider = AnthropicProvider()
            else:
                self.provider = MockProvider()
                
        self.proofs = ProofEngine(self.project_root / "proofs")
        self.generations_root = self.state_root / "generations"
        self.generations_root.mkdir(parents=True, exist_ok=True)
        import os
        self.simulated = os.getenv("AION_RUNTIME_MODE", "simulation") == "simulation"

    def plan(self, objective: str) -> MutationRecord:
        normalized = " ".join(objective.split())
        if len(normalized) < 5:
            raise ValueError("objective is too ambiguous")
        objective_id = f"obj-{uuid4().hex[:12]}"
        mutation_id = f"mut-{uuid4().hex[:12]}"
        searchable_objective = "".join(
            character
            for character in unicodedata.normalize("NFKD", normalized.casefold())
            if not unicodedata.combining(character)
        )
        video_goal = "video" in searchable_objective
        package = "ffmpeg" if video_goal else "generic-tool"
        capability = f"package.propose:{package}"
        contract = IntentContract(
            objective_id=objective_id,
            objective=normalized,
            context="local-first NixOS evolution proposal",
            expected_result=f"validated declarative capability proposal for {package}",
            constraints=[
                "no host package installation",
                "simulation-only execution",
                "human approval before promotion",
                "preserve audit and rollback",
            ],
            authorized_data=["project fixtures", "generated proof metadata"],
            prohibited_data=["credentials", ".env files", "personal files", "reserved tests"],
            acceptable_risk=1,
            resources={"cpu_seconds": 30, "memory_mb": 256, "network_requests": 0},
            metrics={"success": 0.85, "security": 0.98, "cost": 0.50},
            stop_criteria=[
                "policy denial",
                "test failure",
                "evidence mismatch",
                "budget exhaustion",
            ],
            permissions=[capability],
            approval_required=True,
            reversal="restore the parent generation and quarantine generated memory",
            assumptions=["Nix build is simulated when Nix is unavailable"],
        )
        record = MutationRecord(
            mutation_id=mutation_id,
            objective_id=objective_id,
            objective=normalized,
            intent=contract,
        )
        self._advance(record, MutationState.INTENT_VALIDATED)
        self._advance(record, MutationState.PLANNED)
        candidates = self.provider.propose(contract)
        population = EvolutionPopulation(objective_id=objective_id, candidates=candidates)
        archive = CandidateArchive()
        lineage = LineageGraph()
        for candidate in population.candidates:
            archive.add(candidate)
            lineage.add(candidate)
        record.candidates = archive.list()
        self._advance(record, MutationState.CANDIDATES_GENERATED)

        grants = CapabilityManager(
            [
                CapabilityGrant(
                    grant_id=f"grant-{uuid4().hex[:12]}",
                    capability=capability,
                    grantee=self.provider.identity,
                    objective_id=objective_id,
                    expires_at=datetime.now(UTC) + timedelta(minutes=5),
                    remaining_uses=len(candidates),
                )
            ]
        )
        policy = PolicyEngine(ActionValidator(grants))
        executor = SafeExecutor()
        policy_results: list[dict[str, str]] = []
        execution_results: list[dict[str, object]] = []
        for index, candidate in enumerate(candidates):
            cap = candidate.capabilities[0] if candidate.capabilities else capability
            action_type = cap.split(":", 1)[0]
            target = cap.split(":", 1)[1] if ":" in cap else package
            action = SemanticAction(
                action_id=f"action-{mutation_id}-{index}",
                action_type=action_type,
                target=target,
                reason="validated capability gap",
                origin=self.provider.identity,
                objective_id=objective_id,
                required_capability=capability,
                risk_tier=1,
                expected_result="declarative package proposal generated",
                rollback_action="generation.restore_parent",
            )
            result = policy.evaluate(action, actor=self.provider.identity)
            policy_results.append(result.model_dump(mode="json"))
            if result.decision is not PolicyDecision.ALLOW:
                record.transition(MutationState.ARCHIVED)
                self.mutations.save(record)
                raise PermissionError(f"candidate denied: {result.reason}")
            execution_results.append(executor.execute(action).model_dump(mode="json"))
        self._advance(record, MutationState.POLICY_CHECKED)
        self._advance(record, MutationState.BUILDING)
        self._advance(record, MutationState.TESTING)
        self._advance(record, MutationState.ADVERSARIAL_TESTING)
        selected = ParetoSelector.select(candidates)
        record.selected_candidate_id = selected.candidate_id
        council = ModelCouncil.evaluate(
            proposer=self.provider.identity,
            verifier="deterministic-evaluator/v1",
            critical=True,
            accepted=True,
            candidate_config=selected.configuration,
        )
        if not council.approved:
            record.transition(MutationState.ARCHIVED)
            self.mutations.save(record)
            raise PermissionError(council.reason)
        self._advance(record, MutationState.EVALUATED)

        reports = self._reports(
            record,
            selected=selected.model_dump(mode="json"),
            policy_results=policy_results,
            execution_results=execution_results,
            council=council.model_dump(mode="json"),
            package=package,
        )
        proof_path = self.proofs.create(
            mutation_id,
            reports=reports,
            hypothesis=(
                f"Adding `{package}` declaratively enables the requested capability "
                "without host mutation."
            ),
            summary=(
                f"# {mutation_id}\n\n"
                f"Selected `{selected.candidate_id}` from two simulated candidates. "
                "Policy, build, tests, benchmark and adversarial reports are simulations "
                "in this proof; checksums and state-machine enforcement are real. "
                "Human approval is still required."
            ),
        )
        record.proof_path = str(proof_path.relative_to(self.project_root)).replace("\\", "/")
        self._advance(record, MutationState.AWAITING_APPROVAL)
        self.mutations.save(record)
        self.audit.append(
            "mutation.awaiting_approval",
            actor="vek",
            objective_id=objective_id,
            mutation_id=mutation_id,
            details={"candidate": selected.candidate_id, "proof": record.proof_path},
        )
        return record

    def approve(self, mutation_id: str, *, approved_by: str) -> MutationRecord:
        if not approved_by.strip():
            raise ValueError("approver identity is required")
        record = self.mutations.load(mutation_id)
        record.transition(MutationState.APPROVED)
        record.approved_by = approved_by
        self.mutations.save(record)
        self.audit.append("mutation.approved", actor=approved_by, mutation_id=mutation_id)
        return record

    def reject(self, mutation_id: str, *, reason: str, rejected_by: str) -> MutationRecord:
        if not reason.strip() or not rejected_by.strip():
            raise ValueError("rejection reason and actor are required")
        record = self.mutations.load(mutation_id)
        record.transition(MutationState.REJECTED)
        record.rejection_reason = reason
        self.mutations.save(record)
        self.audit.append(
            "mutation.rejected",
            actor=rejected_by,
            mutation_id=mutation_id,
            details={"reason": reason},
        )
        return record

    def promote(self, mutation_id: str) -> MutationRecord:
        record = self.mutations.load(mutation_id)
        if not record.proof_path:
            raise ValueError("mutation has no evidence path")
        EvidenceVerifier().verify(self.project_root / record.proof_path)
        record.transition(MutationState.PROMOTING)
        generation_id = f"gen-{uuid4().hex[:12]}"
        current = self.current_generation()
        selected = next(
            candidate
            for candidate in record.candidates
            if candidate.candidate_id == record.selected_candidate_id
        )
        configuration_hash = hashlib.sha256(selected.configuration.encode()).hexdigest()
        genome = SystemGenome(
            generation_id=generation_id,
            parent_generation_id=current.generation_id if current else None,
            capabilities=selected.capabilities,
            skills=[selected.skill["name"]],
            configuration_hash=configuration_hash,
            mutation_id=mutation_id,
            simulated=self.simulated,
        )
        genome.export(self.generations_root / f"{generation_id}.json")
        (self.generations_root / "current").write_text(generation_id + "\n", encoding="utf-8")
        record.generation_id = generation_id
        record.transition(MutationState.PROMOTED)
        record.transition(MutationState.MONITORING)
        self.mutations.save(record)
        self.proofs.update_post_promotion(
            mutation_id,
            {
                "status": "monitoring",
                "generation_id": generation_id,
                "simulated": self.simulated,
                "host_modified": not self.simulated,
            },
        )
        self.audit.append(
            "generation.promoted_simulation" if self.simulated else "generation.promoted",
            actor="tcb-executor",
            mutation_id=mutation_id,
            details={"generation_id": generation_id, "simulated": self.simulated},
        )
        return record

    def rollback(self, mutation_id: str | None = None) -> MutationRecord:
        record = self.mutations.load(mutation_id) if mutation_id else self._current_mutation()
        if record.state not in {MutationState.PROMOTED, MutationState.MONITORING}:
            raise ValueError("only a promoted generation can be rolled back")
        if not record.generation_id:
            raise ValueError("mutation has no generation")
        genome = SystemGenome.model_validate_json(
            (self.generations_root / f"{record.generation_id}.json").read_text(encoding="utf-8")
        )
        pointer = self.generations_root / "current"
        if genome.parent_generation_id:
            pointer.write_text(genome.parent_generation_id + "\n", encoding="utf-8")
        elif pointer.exists():
            pointer.unlink()
        record.transition(MutationState.ROLLED_BACK)
        self.mutations.save(record)
        self.proofs.update_post_promotion(
            record.mutation_id,
            {
                "status": "rolled_back",
                "generation_id": record.generation_id,
                "restored_generation_id": genome.parent_generation_id,
                "simulated": self.simulated,
                "host_modified": not self.simulated,
            },
        )
        self.audit.append(
            "generation.rolled_back_simulation" if self.simulated else "generation.rolled_back",
            actor="tcb-executor",
            mutation_id=record.mutation_id,
            details={"restored": genome.parent_generation_id, "simulated": self.simulated},
        )
        return record

    def current_generation(self) -> SystemGenome | None:
        pointer = self.generations_root / "current"
        if not pointer.is_file():
            return None
        generation_id = pointer.read_text(encoding="utf-8").strip()
        return SystemGenome.model_validate_json(
            (self.generations_root / f"{generation_id}.json").read_text(encoding="utf-8")
        )

    def _current_mutation(self) -> MutationRecord:
        current = self.current_generation()
        if current is None:
            raise ValueError("no promoted generation is active")
        return self.mutations.load(current.mutation_id)

    def _advance(self, record: MutationRecord, state: MutationState) -> None:
        record.transition(state)
        self.audit.append(
            "mutation.transition",
            actor="vek",
            objective_id=record.objective_id,
            mutation_id=record.mutation_id,
            details={"state": state.value},
        )

    @staticmethod
    def _reports(
        record: MutationRecord,
        *,
        selected: dict[str, object],
        policy_results: list[dict[str, str]],
        execution_results: list[dict[str, object]],
        council: dict[str, object],
        package: str,
    ) -> dict[str, dict[str, object]]:
        return {
            "manifest.json": {"mutation_id": record.mutation_id, "format": "aion-proof-v1"},
            "intent-contract.json": record.intent.model_dump(mode="json"),
            "baseline.json": {"capability_present": False, "package": package, "captured": True},
            "candidate.json": selected,
            "policy-report.json": {"results": policy_results, "deterministic": True},
            "build-report.json": {"status": "simulated", "isolated": True, "host_modified": False},
            "test-report.json": {
                "status": "simulated",
                "tests": ["configuration", "skill-contract"],
            },
            "security-report.json": {"status": "pass", "scope": "deterministic policy checks"},
            "benchmark-report.json": {"status": "simulated", "score": selected["metrics"]},
            "adversarial-report.json": {
                "status": "simulated",
                "blocked": ["root", "free-shell", "protected-files", "reserved-tests"],
            },
            "comparison.json": {
                "selection": selected["candidate_id"],
                "method": "pareto-frontier",
                "candidates": [
                    candidate.model_dump(mode="json") for candidate in record.candidates
                ],
            },
            "provenance.json": {
                "provider": "mock-provider/offline-v1",
                "executor_results": execution_results,
                "council": council,
                "generated_at": datetime.now(UTC).isoformat(),
            },
            "rollback-plan.json": {
                "action": "generation.restore_parent",
                "host_effect": "none-in-mvp",
            },
            "post-promotion-report.json": {
                "status": "pending-human-approval",
                "note": "promotion and monitoring are recorded in the append-only audit log",
            },
        }
