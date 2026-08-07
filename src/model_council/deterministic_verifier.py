from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict

# Patterns a candidate's declarative configuration text must never contain,
# regardless of what any LLM-based reviewer concludes. This is deliberately
# NOT an LLM: it is deterministic, has no model weights to jailbreak, and
# cannot be the same "identity" as the proposer no matter which provider
# generated the proposal - it is a genuinely independent verifier.
_DANGEROUS_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # Deliberately scoped to patterns that would NOT show up in ordinary
    # declarative Nix/config syntax (which legitimately uses `;`, `[`, `]`,
    # `{`, `}`, and even package names like `pkgs.curl`) - a naive
    # "any shell metacharacter" scan is all false positives against that
    # syntax and would make this verifier useless.
    ("command substitution", re.compile(r"\$\(|`[^`]*`")),
    ("piped remote code execution", re.compile(r"https?://\S+\s*\|\s*(sh|bash|python3?)\b")),
    ("privilege escalation", re.compile(r"\bsudo\b|\bsetuid\s*=\s*true|\bNOPASSWD\b")),
    (
        "root login / auth weakening",
        re.compile(
            r"\bpermitRootLogin\s*=\s*[\"']?yes|\bPasswordAuthentication\s*=\s*[\"']?yes",
            re.IGNORECASE,
        ),
    ),
    ("sensitive file access", re.compile(r"/etc/shadow|/etc/passwd|\.\./\.\./")),
)


class DeterministicVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    approved: bool
    verifier: str = "deterministic-verifier/v1"
    findings: list[str]


class DeterministicVerifier:
    """A non-LLM, pattern-based gate on candidate configuration text.

    Runs unconditionally alongside (not instead of) the ModelCouncil review.
    It cannot be prompt-injected, cannot silently fail open on an API error
    (there is no API), and is not the same "model" that proposed the
    candidate - so it satisfies the independent-verifier requirement even
    when the proposer and the LLM-based council reviewer happen to be the
    same underlying model.
    """

    @staticmethod
    def verify(configuration: str) -> DeterministicVerdict:
        findings = [
            label for label, pattern in _DANGEROUS_PATTERNS if pattern.search(configuration)
        ]
        return DeterministicVerdict(approved=not findings, findings=findings)
