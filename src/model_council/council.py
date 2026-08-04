from __future__ import annotations
import os

from pydantic import BaseModel, ConfigDict


class CouncilDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    approved: bool
    proposer: str
    verifier: str
    reason: str


class ModelCouncil:
    @staticmethod
    def evaluate(
        *, proposer: str, verifier: str, critical: bool, accepted: bool, candidate_config: str | None = None
    ) -> CouncilDecision:
        if critical and proposer == verifier:
            return CouncilDecision(
                approved=False,
                proposer=proposer,
                verifier=verifier,
                reason="critical changes require an independent verifier",
            )
            
        # Red Team Evaluation
        if candidate_config and os.getenv("ANTHROPIC_API_KEY"):
            try:
                from anthropic import Anthropic
                client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                real_verifier = "anthropic/red-team-v1"
                prompt = f"""
You are the AION OS Red Team Verifier. Analyze this NixOS configuration proposal for security vulnerabilities:
```nix
{candidate_config}
```
If you find ANY critical vulnerability (e.g., exposing roots, disabling firewalls, malicious curls, reverse shells), reply with EXACTLY 'REJECTED: <reason>'.
Otherwise, reply with EXACTLY 'APPROVED'.
"""
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=256,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.content[0].text.strip()
                if content.startswith("REJECTED"):
                    return CouncilDecision(
                        approved=False,
                        proposer=proposer,
                        verifier=real_verifier,
                        reason=content
                    )
                verifier = real_verifier
            except Exception as e:
                pass # fallback to standard acceptance
                
        return CouncilDecision(
            approved=accepted,
            proposer=proposer,
            verifier=verifier,
            reason="independent evaluation recorded" if accepted else "verifier rejected candidate",
        )
