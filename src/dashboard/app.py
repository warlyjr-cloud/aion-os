import os
from pathlib import Path
from typing import List, Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="AION OS Dashboard")
dashboard_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(dashboard_dir / "templates"))

def _get_project_root() -> Path:
    return Path(os.environ.get("AION_PROJECT_ROOT", Path.cwd())).resolve()

def _read_audit_log() -> List[Dict[str, Any]]:
    audit_file = _get_project_root() / ".aion-state" / "audit.jsonl"
    if not audit_file.exists():
        return []
    import json
    logs = []
    with open(audit_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return logs

def _read_mutations() -> List[Dict[str, Any]]:
    mutations_dir = _get_project_root() / ".aion-state" / "mutations"
    if not mutations_dir.exists():
        return []
    import json
    mutations = []
    for m_file in mutations_dir.glob("*.json"):
        with open(m_file, "r", encoding="utf-8") as f:
            try:
                mutations.append(json.load(f))
            except json.JSONDecodeError:
                pass
    # Mutacoes nao tem 'created_at' explicito na raiz do modelo as vezes, ordenar por ID ou metadata
    return sorted(mutations, key=lambda x: x.get("mutation_id", ""), reverse=True)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    audit_logs = _read_audit_log()
    mutations = _read_mutations()
    pending = [m for m in mutations if m.get("state") == "awaiting_approval"]
    history = [m for m in mutations if m.get("state") != "awaiting_approval"]
    
    return templates.TemplateResponse(
        request=request,
        name="index.html", 
        context={
            "audit_logs": audit_logs[-50:], # Show last 50
            "pending": pending,
            "history": history
        }
    )

class GossipPayload(BaseModel):
    mutation_id: str
    proof: Dict[str, Any]

@app.post("/grid/gossip")
async def grid_gossip(payload: GossipPayload):
    from grid.p2p import GridManager
    manager = GridManager(_get_project_root())
    return manager.receive_gossip(payload.model_dump())

@app.get("/grid/status")
async def grid_status():
    from grid.p2p import GridManager
    manager = GridManager(_get_project_root())
    return {"peers": manager.get_peers()}

class ComputePayload(BaseModel):
    objective: str
    context: str

@app.post("/grid/compute")
async def grid_compute(payload: ComputePayload):
    from providers.llm import AnthropicProvider
    from intent import IntentContract
    provider = AnthropicProvider()
    contract = IntentContract(
        objective_id="parasite-1",
        objective=payload.objective,
        context=payload.context,
        expected_result="raw completion",
        constraints=[], authorized_data=[], prohibited_data=[], acceptable_risk=1, resources={}, metrics={}, stop_criteria=[], permissions=[], approval_required=False, reversal="", assumptions=[]
    )
    candidates = provider.propose(contract)
    if not candidates:
        return {"status": "failed", "content": ""}
    return {"status": "success", "content": candidates[0].configuration}
