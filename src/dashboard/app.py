from __future__ import annotations

# pyright: reportUnusedFunction=false
import json
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


def _get_project_root() -> Path:
    root = os.environ.get("AION_PROJECT_ROOT")
    if root:
        return Path(root).expanduser().resolve()
    return Path.cwd().resolve()


def _get_state_dir() -> Path:
    return _get_project_root() / ".aion-state"


def _ensure_runtime_layout() -> None:
    state_dir = _get_state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "mutations").mkdir(parents=True, exist_ok=True)
    (state_dir / "logs").mkdir(parents=True, exist_ok=True)


def _read_audit_log() -> list[dict[str, Any]]:
    audit_file = _get_state_dir() / "audit.jsonl"
    if not audit_file.exists():
        return []

    logs: list[dict[str, Any]] = []
    with audit_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                logs.append(payload)
    return logs


def _read_mutations() -> list[dict[str, Any]]:
    mutations_dir = _get_state_dir() / "mutations"
    if not mutations_dir.exists():
        return []

    mutations: list[dict[str, Any]] = []
    for mutation_file in mutations_dir.glob("*.json"):
        with mutation_file.open("r", encoding="utf-8") as handle:
            try:
                mutations.append(json.load(handle))
            except json.JSONDecodeError:
                continue
    return sorted(mutations, key=lambda item: str(item.get("mutation_id", "")), reverse=True)


_PROOF_REPORT_NAMES = (
    "policy-report.json",
    "security-report.json",
    "build-report.json",
    "test-report.json",
    "benchmark-report.json",
    "adversarial-report.json",
    "comparison.json",
    "provenance.json",
    "rollback-plan.json",
    "post-promotion-report.json",
)


def _read_proof_bundle(mutation_id: str) -> dict[str, Any] | None:
    """Read every report in a mutation's proof directory, so a caller can
    see exactly why a candidate was approved or rejected - not just the
    final state. Returns None if the mutation has no proof directory."""
    if not mutation_id.startswith("mut-") or not mutation_id.replace("-", "").isalnum():
        return None
    proof_dir = _get_project_root() / "proofs" / mutation_id
    if not proof_dir.is_dir():
        return None

    bundle: dict[str, Any] = {}
    for name in _PROOF_REPORT_NAMES:
        report_path = proof_dir / name
        if not report_path.is_file():
            continue
        try:
            bundle[name] = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            bundle[name] = {"error": "unparseable report"}
    return bundle


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
        _ensure_runtime_layout()
        yield

    app = FastAPI(
        title="AION OS Dashboard",
        description="Investor-grade operations surface for the AION OS control plane.",
        version=os.getenv("AION_DASHBOARD_VERSION", "0.1.0"),
        lifespan=lifespan,
    )
    dashboard_dir = Path(__file__).parent
    templates = Jinja2Templates(directory=str(dashboard_dir / "templates"))

    @app.get("/healthz")
    async def healthz() -> dict[str, Any]:
        return {
            "status": "ok",
            "service": "aion-dashboard",
            "mode": os.getenv("AION_RUNTIME_MODE", "simulation"),
            "project": "aion-os",
            "timestamp": datetime.now(UTC).isoformat(),
            "project_root": str(_get_project_root()),
        }

    @app.get("/readyz")
    async def readyz() -> JSONResponse:
        state_dir = _get_state_dir()
        ready = state_dir.exists() and (state_dir / "mutations").exists()
        payload = {
            "ready": ready,
            "service": "aion-dashboard",
            "state_dir": str(state_dir),
        }
        status_code = 200 if ready else 503
        return JSONResponse(payload, status_code=status_code)

    @app.get("/api/status")
    async def api_status() -> dict[str, Any]:
        mutations = _read_mutations()
        pending = [
            mutation for mutation in mutations if mutation.get("state") == "awaiting_approval"
        ]
        history = [
            mutation for mutation in mutations if mutation.get("state") != "awaiting_approval"
        ]
        return {
            "project": "aion-os",
            "status": "ready",
            "mode": os.getenv("AION_RUNTIME_MODE", "simulation"),
            "mutations": len(mutations),
            "pending": len(pending),
            "history": len(history),
            "state_dir": str(_get_state_dir()),
        }

    @app.get("/api/mutations")
    async def api_mutations() -> list[dict[str, Any]]:
        """Full mutation records, not just counts - each one already
        carries its own decision (selected_candidate_id, approved_by,
        rejection_reason, state_history)."""
        return _read_mutations()

    @app.get("/api/mutations/{mutation_id}")
    async def api_mutation_detail(mutation_id: str) -> JSONResponse:
        """The actual decision, not just a status: the mutation record plus
        every report in its proof bundle (policy, security/deterministic-
        verifier verdict, council decision inside provenance, rollback
        plan), and the slice of the hash-chained audit log for this
        mutation_id."""
        record = next(
            (m for m in _read_mutations() if m.get("mutation_id") == mutation_id),
            None,
        )
        if record is None:
            return JSONResponse({"error": f"unknown mutation: {mutation_id}"}, status_code=404)
        audit_events = [
            entry for entry in _read_audit_log() if entry.get("mutation_id") == mutation_id
        ]
        return JSONResponse(
            {
                "record": record,
                "proof": _read_proof_bundle(mutation_id),
                "audit_events": audit_events,
            }
        )

    @app.get("/metrics")
    async def metrics() -> PlainTextResponse:
        mutations = _read_mutations()
        pending = [
            mutation for mutation in mutations if mutation.get("state") == "awaiting_approval"
        ]
        return PlainTextResponse(
            "\n".join(
                [
                    "# HELP aion_dashboard_up Whether the dashboard is running",
                    "# TYPE aion_dashboard_up gauge",
                    "aion_dashboard_up 1",
                    "# HELP aion_dashboard_mutations Total mutations discovered",
                    "# TYPE aion_dashboard_mutations gauge",
                    f"aion_dashboard_mutations {len(mutations)}",
                    "# HELP aion_dashboard_pending_mutations Pending approvals",
                    "# TYPE aion_dashboard_pending_mutations gauge",
                    f"aion_dashboard_pending_mutations {len(pending)}",
                ]
            )
        )

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        audit_logs = _read_audit_log()
        mutations = _read_mutations()
        pending = [
            mutation for mutation in mutations if mutation.get("state") == "awaiting_approval"
        ]
        history = [
            mutation for mutation in mutations if mutation.get("state") != "awaiting_approval"
        ]
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "audit_logs": audit_logs[-50:],
                "pending": pending,
                "history": history,
            },
        )

    class GossipPayload(BaseModel):
        mutation_id: str
        proof: dict[str, Any]

    @app.post("/grid/gossip")
    async def grid_gossip(payload: GossipPayload) -> JSONResponse:
        try:
            from grid.p2p import GridManager
        except Exception as exc:  # pragma: no cover - defensive path
            return JSONResponse({"status": "unavailable", "error": str(exc)}, status_code=503)

        manager = GridManager(_get_project_root())
        return JSONResponse(manager.receive_gossip(payload.model_dump()))

    @app.get("/grid/status")
    async def grid_status() -> dict[str, Any]:
        try:
            from grid.p2p import GridManager
        except Exception as exc:  # pragma: no cover - defensive path
            return {"peers": [], "status": "unavailable", "error": str(exc)}

        manager = GridManager(_get_project_root())
        return {"peers": manager.get_peers(), "status": "ok"}

    class ComputePayload(BaseModel):
        objective: str
        context: str

    @app.post("/grid/compute")
    async def grid_compute(payload: ComputePayload) -> dict[str, Any]:
        try:
            from intent import IntentContract
            from providers.llm import AnthropicProvider
        except Exception as exc:  # pragma: no cover - defensive path
            return {"status": "failed", "content": "", "error": str(exc)}

        provider = AnthropicProvider()
        contract = IntentContract(
            objective_id="parasite-1",
            objective=payload.objective,
            context=payload.context,
            expected_result="raw completion",
            constraints=[],
            authorized_data=[],
            prohibited_data=[],
            acceptable_risk=1,
            resources={},
            metrics={},
            stop_criteria=[],
            permissions=[],
            approval_required=False,
            reversal="",
            assumptions=[],
        )
        candidates = provider.propose(contract)
        if not candidates:
            return {"status": "failed", "content": ""}
        return {"status": "success", "content": candidates[0].configuration}

    return app


app = create_app()


def main() -> None:
    import uvicorn

    # Containerized deployment needs 0.0.0.0 to be reachable from outside the
    # container; overridable via env var, matches .env.example / docker-compose.
    host = os.getenv("AION_DASHBOARD_HOST", "0.0.0.0")  # noqa: S104
    port = int(os.getenv("AION_DASHBOARD_PORT", "8000"))
    log_level = os.getenv("AION_LOG_LEVEL", "info")
    uvicorn.run(app, host=host, port=port, log_level=log_level)


if __name__ == "__main__":
    main()
