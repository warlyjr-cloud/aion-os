# Security Policy

AION OS gates model-proposed system mutations behind two independent
review layers (an LLM council and a non-LLM deterministic verifier),
typed capabilities, and a hash-chained audit trail. It runs in
simulation-only mode by default — see `docs/PROJECT_STATUS.md` for what
is proven real vs. scaffold.

## Supported Versions
Only the `main` branch is currently supported for security fixes.

## Reporting a Vulnerability
If you discover a vulnerability — especially anything that lets a
model-proposed mutation bypass the deterministic verifier, execute
outside the capability/allowlist gate, or reach the host without
`AION_RUNTIME_MODE=real` and `AION_ALLOW_HOST_MUTATION=1` both set:
1. **DO NOT** open a public issue on GitHub.
2. Open a private security advisory on this repository (or contact the
   maintainer directly if you don't have access).
3. Include reproduction steps and the affected commit.

*Note: there is currently no active bug bounty program.*
