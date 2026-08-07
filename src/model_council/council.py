from __future__ import annotations

import logging
import os

from pydantic import BaseModel, ConfigDict

from security.secrets import SecretConfig, ensure_public_safe_payload

_RED_TEAM_PROMPT = """
You are the AION OS Red Team Verifier. Analyze this candidate configuration
proposal for security vulnerabilities:
```
{candidate_config}
```
If you find ANY critical vulnerability (e.g., exposing roots, disabling
firewalls, malicious curls, reverse shells), reply with EXACTLY
'REJECTED: <reason>'. Otherwise, reply with EXACTLY 'APPROVED'.
"""

_logger = logging.getLogger(__name__)


class CouncilDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    approved: bool
    proposer: str
    verifier: str
    reason: str


class ModelCouncil:
    """Independent-review gate. For `critical=True` proposals, once an
    independent red-team review is actually reachable (an API key is
    configured and there is candidate content to review), the outcome of
    that review is authoritative: a completed rejection or any failure
    while reviewing denies by default. Only when no review could be
    attempted at all (no API key anywhere - a fully offline/mock run with
    nothing untrusted to review) does the caller-supplied `accepted`
    decision apply, matching pre-existing offline behavior.
    """

    @staticmethod
    def evaluate(
        *,
        proposer: str,
        verifier: str,
        critical: bool,
        accepted: bool,
        candidate_config: str | None = None,
    ) -> CouncilDecision:
        config = SecretConfig.from_environment()
        candidate_payload = ensure_public_safe_payload(candidate_config or "")
        safe_candidate_config = candidate_payload if isinstance(candidate_payload, str) else ""

        if critical and proposer == verifier:
            return CouncilDecision(
                approved=False,
                proposer=proposer,
                verifier=verifier,
                reason="critical changes require an independent verifier",
            )

        api_key = config.provider_api_key or os.getenv("ANTHROPIC_API_KEY")

        if not critical:
            # Non-critical path keeps the caller-supplied decision; an
            # optional best-effort red-team pass can only make it stricter.
            if safe_candidate_config and api_key:
                try:
                    rejected, reason = ModelCouncil._run_red_team_review(
                        api_key, safe_candidate_config
                    )
                    if rejected:
                        return CouncilDecision(
                            approved=False,
                            proposer=proposer,
                            verifier="anthropic/red-team-v1",
                            reason=reason,
                        )
                except Exception:
                    _logger.warning(
                        "non-critical red-team review unavailable; not blocking", exc_info=True
                    )
            return ModelCouncil._accepted_decision(proposer, verifier, accepted)

        # Critical path. If there is nothing to review or no way to reach an
        # independent reviewer at all (fully offline/mock run - nothing
        # untrusted was ever generated), fall back to the caller's decision,
        # same as before. But once a real review is actually attempted, any
        # failure must deny by default instead of silently approving - that
        # silent fallback was the actual vulnerability.
        if not safe_candidate_config or not api_key:
            return ModelCouncil._accepted_decision(proposer, verifier, accepted)
        try:
            rejected, reason = ModelCouncil._run_red_team_review(api_key, safe_candidate_config)
        except Exception as exc:
            return CouncilDecision(
                approved=False,
                proposer=proposer,
                verifier=verifier,
                reason=f"red-team review failed, denying by default: {exc}",
            )
        if rejected:
            return CouncilDecision(
                approved=False,
                proposer=proposer,
                verifier="anthropic/red-team-v1",
                reason=reason,
            )
        return CouncilDecision(
            approved=True,
            proposer=proposer,
            verifier="anthropic/red-team-v1",
            reason="independent red-team review passed",
        )

    @staticmethod
    def _accepted_decision(proposer: str, verifier: str, accepted: bool) -> CouncilDecision:
        return CouncilDecision(
            approved=accepted,
            proposer=proposer,
            verifier=verifier,
            reason=(
                "independent evaluation recorded" if accepted else "verifier rejected candidate"
            ),
        )

    @staticmethod
    def _run_red_team_review(api_key: str, safe_candidate_config: str) -> tuple[bool, str]:
        """Returns (rejected, reason). Raises on any transport/API failure
        so callers can decide how to fail (closed for critical paths)."""
        from anthropic import Anthropic
        from anthropic.types import TextBlock

        client = Anthropic(api_key=api_key)
        prompt = _RED_TEAM_PROMPT.format(candidate_config=safe_candidate_config)
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        first_block = response.content[0]
        if not isinstance(first_block, TextBlock):
            raise TypeError(f"unexpected non-text response block: {type(first_block).__name__}")
        content = first_block.text.strip()
        if content.startswith("REJECTED"):
            return True, content
        return False, content
