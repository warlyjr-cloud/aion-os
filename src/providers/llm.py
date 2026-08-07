import json

from anthropic import Anthropic
from anthropic.types import TextBlock

from intent.contracts import IntentContract
from security.secrets import SecretConfig, load_secret, redact_sensitive_text

from .base import CandidateProposal


class AnthropicProvider:
    identity = "anthropic/claude-3-5-sonnet-20241022"

    def __init__(self, api_key: str | None = None) -> None:
        config = SecretConfig.from_environment()
        self.api_key = (
            api_key
            or load_secret("ANTHROPIC_API_KEY", env_var="ANTHROPIC_API_KEY")
            or config.provider_api_key
        )
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required in environment variables")
        self.client = Anthropic(api_key=self.api_key)

    def propose(self, contract: IntentContract) -> list[CandidateProposal]:
        prompt = f"""
You are the AION OS Evolution Engine. Generate 2 NixOS candidate proposals
to satisfy the objective: '{contract.objective}'.
Return a valid JSON object strictly matching this schema:
{{
    "candidates": [
        {{
            "configuration": "nix code snippet",
            "skill": {{"name": "skill-name", "mode": "balanced|minimal", "shell": "disabled"}},
            "capabilities": ["action_type:target"]
        }}
    ]
}}
Do not return any other text outside the JSON block. Valid action_types:
package.propose, file.patch, service.configure.
"""
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            first_block = response.content[0]
            if not isinstance(first_block, TextBlock):
                raise TypeError(f"unexpected non-text response block: {type(first_block).__name__}")
            content = first_block.text
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()

            data = json.loads(content)
            proposals: list[CandidateProposal] = []
            for i, cand in enumerate(data.get("candidates", [])):
                proposals.append(
                    CandidateProposal(
                        candidate_id=f"{contract.objective_id}-cand-{i}",
                        provider=self.identity,
                        configuration=cand["configuration"],
                        skill=cand["skill"],
                        capabilities=cand["capabilities"],
                        metrics={"success": 0.9, "security": 0.95, "cost": 0.2, "novelty": 0.5},
                        simulated=True,
                    )
                )
            return proposals
        except Exception as e:
            print(
                f"[AnthropicProvider] Failed to generate proposals: {redact_sensitive_text(str(e))}"
            )
            return []
