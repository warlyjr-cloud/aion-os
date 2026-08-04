import json
import httpx
from pathlib import Path
from typing import List, Dict, Any
import logging

class GridManager:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.state_root = project_root / ".aion-state"
        self.peers_file = self.state_root / "peers.json"
        
        if not self.peers_file.exists():
            self.peers_file.write_text(json.dumps(["http://127.0.0.1:8000"]), encoding="utf-8")
            
    def get_peers(self) -> List[str]:
        try:
            return json.loads(self.peers_file.read_text(encoding="utf-8"))
        except Exception:
            return []

    def broadcast_mutation(self, mutation_id: str, proof_payload: Dict[str, Any]):
        """Transmite uma prova matemática para os outros peers."""
        peers = self.get_peers()
        for peer in peers:
            try:
                # O timeout precisa ser curto para nao travar
                httpx.post(f"{peer}/grid/gossip", json={"mutation_id": mutation_id, "proof": proof_payload}, timeout=2.0)
            except Exception as e:
                logging.warning(f"Failed to broadcast to {peer}: {e}")

    def receive_gossip(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Recebe uma mutação de um peer e arquiva."""
        mutation_id = payload.get("mutation_id")
        if not mutation_id:
            return {"status": "rejected", "reason": "no mutation_id"}
            
        gossip_dir = self.state_root / "gossip"
        gossip_dir.mkdir(parents=True, exist_ok=True)
        import random
        # Batalha de Linhas do Tempo (Multiverse Battle)
        # Se 10% de chance, simular que uma evolução concorrente já existia no mesmo 'timestamp relativo'
        if random.random() < 0.1:
            logging.warning(f"[\u2622\ufe0f MULTIVERSO] Colisão Relativística! Mutação {mutation_id} encontrou uma linha do tempo concorrente.")
            # Resolve the battle by fitness (simulated by random int for MVP)
            local_fitness = random.randint(1, 100)
            alien_fitness = random.randint(1, 100)
            if local_fitness > alien_fitness:
                logging.warning(f"[\u2622\ufe0f MULTIVERSO] O Universo Local venceu a batalha (Fitness {local_fitness} > {alien_fitness}). Mutação {mutation_id} apagada da existência.")
                return {"status": "rejected", "reason": "timeline_battle_lost"}
            else:
                logging.warning(f"[\u2622\ufe0f MULTIVERSO] O Universo Estrangeiro venceu (Fitness {alien_fitness} > {local_fitness}). A linha do tempo atual será sobreposta.")
                
        # Write to archive
        (gossip_dir / f"{mutation_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        
        return {"status": "accepted", "mutation_id": mutation_id}

    def offload_compute(self, objective: str, context: str) -> str | None:
        """Tenta parasitar processamento de um peer se estiver sobrecarregado."""
        import random
        # 30% chance to simulate CPU overload and act as a parasite
        if random.random() < 0.3:
            peers = self.get_peers()
            if peers:
                peer = random.choice(peers)
                try:
                    logging.warning(f"Hive Compute: Offloading LLM processing to {peer}")
                    r = httpx.post(f"{peer}/grid/compute", json={"objective": objective, "context": context}, timeout=15.0)
                    if r.status_code == 200:
                        data = r.json()
                        if data.get("status") == "success":
                            return data.get("content")
                except Exception as e:
                    logging.warning(f"Hive Compute failed with peer {peer}: {e}")
        return None
