# Claude Code no AION

Esta configuração é **opt-in**. Revise os scripts e copie `settings.example.json` para `settings.local.json`; não renomeie automaticamente em CI ou em checkout não confiável.

```powershell
Copy-Item ".claude/settings.example.json" ".claude/settings.local.json"
claude doctor
```

Dentro do Claude Code, use `/status`, `/permissions` e `/hooks` para confirmar fontes, permissões e handlers carregados. O exemplo usa PowerShell sem perfil e `-ExecutionPolicy Bypass` somente no processo do hook porque Windows PowerShell pode bloquear scripts locais; isso torna a revisão do checkout obrigatória.

## Hooks

- `pre_tool_guard.ps1`: nega elevação, comandos destrutivos, rede direta, `.env`, escrita fora do projeto e paths protegidos.
- `post_tool_checks.ps1`: valida JSON; em Python, tenta Ruff e Pyright; sinaliza arquivo protegido.
- `record_provenance.ps1`: grava apenas sessão, tool, path relativo e timestamp em `.claude/audit/` (gitignored), nunca conteúdo.
- `stop_claim_guard.ps1`: bloqueia alegações afirmativas evidentes de SOTA, RSI completo, segurança absoluta, produção pronta ou testes totalmente aprovados; respeita `stop_hook_active` para não entrar em loop.
- `pre_commit_gate.ps1`: gate manual com Gitleaks, Semgrep, Ruff, Pyright e pytest quando disponíveis. Claude Code não possui evento `PreCommit`; execute explicitamente ou integre ao framework `pre-commit` após revisão.

```powershell
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File ".claude/hooks/pre_commit_gate.ps1" -Strict
```

Hooks são defesa adicional, não sandbox/TCB. Regex de shell pode ter falsos positivos/negativos; permissões nativas, isolamento do sistema e revisão humana continuam necessários. Veja a [referência oficial de hooks](https://code.claude.com/docs/en/hooks), [settings](https://code.claude.com/docs/en/settings) e [subagentes](https://code.claude.com/docs/en/sub-agents).

## Agentes

Os nove agentes do projeto são somente leitura. Eles auditam arquitetura, NixOS, TCB, política, benchmark, red team, provas, memória e documentação. O agente que produz uma mutação nunca deve ser seu único verificador, e nenhum subagente pode substituir aprovação humana para arquivo protegido.
