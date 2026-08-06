# Security and IP protection

AION OS is intended to be public-facing, but the most valuable runtime logic and operational secrets should not be disclosed in the public repository.

## Public/private boundary
- Public repository contents may include architecture, interfaces, and user-facing workflow examples.
- Sensitive runtime logic such as privileged Oracle/Fleet Manager decision paths should remain in private or controlled environments.
- Secrets must never be committed to the repository and must be sourced from environment variables or a dedicated secret manager.

## Current protections
- Secrets are loaded from environment variables through `src/security/secrets.py`.
- Runtime outputs are sanitized before being emitted to the public CLI/daemon surfaces.
- A repository scan (`aion-secret-scan`) checks for obvious secret-like patterns in tracked content.

## Required release practice
- Store real secrets in GitHub Secrets, Azure Key Vault, or an equivalent vault.
- Rotate secrets periodically and scope them per environment.
- Ensure logs and error messages never contain raw secret values.
- Keep the public repository focused on interfaces, contracts, and safety workflows rather than privileged implementation details.
