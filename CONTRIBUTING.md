# Como contribuir

Obrigado por contribuir com o AION. O projeto prioriza segurança, evidência e mudanças pequenas.

## Antes de começar

1. Leia `AGENTS.md`, `CLAUDE.md` e `docs/SAFETY_CONSTITUTION.md`.
2. Discuta mudanças arquiteturais, dependências novas e alterações protegidas antes de implementar.
3. Use uma branch `feature/*`, `research/*` ou `security/*`; candidatas `mutation/*` são locais por padrão.
4. Nunca adicione segredos, `.env`, dados pessoais ou conteúdo de benchmark reservado a logs/provas.

## Ambiente

```bash
uv venv
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run pyright
```

Não instale ferramentas globalmente nem altere kernel, bootloader, firewall, usuários ou rede do host. Validação Nix/VM deve ocorrer em ambiente apropriado e ser registrada exatamente.

## Mudanças

- Siga Python 3.12, type hints estritos e o estilo já configurado.
- Toda ação de runtime deve ser tipada; não introduza shell livre produzido por modelo.
- Trate erros explicitamente e mantenha operações limitadas, auditáveis e reversíveis.
- Adicione testes para comportamento novo e testes adversariais para novas fronteiras de autoridade.
- Não reduza testes, políticas, auditoria, sandbox, emergency stop ou rollback para obter sucesso.
- O autor de uma mutação não pode ser seu único verificador.

## Pull request

Descreva objetivo, hipótese, risco, arquivos protegidos tocados, testes executados e não executados, impacto de privacidade, plano de rollback e proveniência de IA. Anexe evidência reproduzível; “parece funcionar” não é evidência.

Commits devem ser pequenos e imperativos em inglês, por exemplo `add capability scope validation`. Não faça force-push nem reescreva histórico compartilhado sem autorização.

## Revisão protegida

Alterações na constituição, TCB, políticas fundamentais, executor privilegiado, auditoria, rollback, segurança do repositório ou avaliação reservada precisam de revisão humana específica e, quando aplicável, de um revisor de segurança independente.
