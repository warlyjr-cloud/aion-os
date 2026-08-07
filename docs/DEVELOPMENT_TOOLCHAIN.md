# Toolchain de desenvolvimento

## Python

Python 3.12, `uv`, Ruff, Pyright strict, pytest, pytest-cov, Hypothesis, Pydantic, Typer, SQLite e JSONL. Versões e ranges estão em `pyproject.toml`; lockfile Python reproduzível ainda deve ser confirmado.

```bash
uv sync --extra dev
uv run ruff check .
uv run pyright
uv run pytest
```

Property tests devem cobrir transições inválidas, capability ausente, proteção do TCB, rollback válido e memória sem authority escalation.

## Build e ambiente

Ferramentas próprias do AION para build, verificação e rollback de ambiente/VM, mais serviço systemd. Execute apenas em Linux/WSL; não instale globalmente sem autorização. Nada é “validado” até os comandos concluírem com sucesso.

## Segurança e supply chain

Gitleaks, Semgrep, OSV-Scanner, Syft, Grype e, quando aplicável, CodeQL/Trivy. Resultado sem achados não é prova absoluta. Ferramentas/ações devem ter versão/SHA, licença, origem, rede e revisão em inventário.

## Futuro

OPA/Conftest, Wasmtime, Firecracker, TLA+, model checking, fuzzing, mutation/chaos testing, OpenTelemetry, eBPF, SLSA, in-toto, Sigstore, TUF e TPM. Não adicionar antes de ameaça, interface e custo justificarem.

## Evitar agora

Frameworks agentivos grandes, Kubernetes, banco externo/vetorial, dashboard antes do VEK, MCP de shell/filesystem amplo e plugins não pinados. Preferir abstrações pequenas e testáveis.
