# Handoff para Claude Code

Atualizado em **2026-08-02**. Este handoff registra o estado observado durante o bootstrap; reconcilie-o com a saída final de testes antes de continuar.

> **Addendum 2026-08-07**: o diretório `nix/`, `flake.nix` e `flake.lock` foram removidos do projeto; `.github/workflows/nix.yml` e `.claude/agents/nixos-engineer.md` (renomeado `lab-engineer.md`) também. As menções a Nix abaixo são registro histórico do estado em 2026-08-02 e não devem ser usadas como instrução atual. Note que `src/executor/safe.py` ainda tem um caminho de execução real via `nix build` em WSL fora do modo simulation — isso é uma questão de segurança em aberto, não coberta por esta limpeza.

## Resumo executivo

O repositório contém um MVP Python offline/simulation-only, estrutura Nix, schemas, EvoBench, testes e documentação normativa. A presença dos arquivos não prova que suíte Python, Nix, VM, ferramentas de segurança ou demo passaram. A configuração Claude Code é opt-in e seus hooks foram testados apenas com payloads sintéticos.

## Implementado no código observado

- `EvolutionEngine` cria contrato, duas candidatas MockProvider, aplica capability/policy, seleciona por Pareto, produz proof bundle, recebe aprovação/rejeição e registra geração/rollback **simulados**.
- `SafeExecutor` tem allowlist e retorna somente `simulated=True`; não altera o host.
- state machine, capability manager, action validator, evidence/checksum verifier, audit hash chain, memory store, genome, population/lineage e Model Council lógico.
- CLI `aionctl` e `aiond` com comandos de status, plan/ask, mutations, proof, benchmark, genome, memory, generations, autonomy, rollback e stop.
- EvoBench de cinco tarefas e digital twin fechado, com testes adversariais no repositório.
- Flake/módulo/Lab/ISO/teste Nix estruturados, ainda sujeitos a validação real.

## Documentado e preparado

- visão, posicionamento, diferenciação, prior art e agenda de pesquisa;
- arquitetura, VEK, TCB, Constituição, ações, capabilities, intent e provas;
- busca evolutiva, RSI, EvoBench, memória, digital twin, council e registry;
- autonomia, ameaça, privacidade, providers, genome, toolchain e roadmap;
- README, security, contribution, conduct e provenance;
- nove agentes read-only, quatro hooks ativos no exemplo e gate pre-commit manual.

## Simulado

Build/test/benchmark/adversarial reports dentro do proof gerado pelo VEK; package proposal FFmpeg; execução de actions; promotion/monitoring/rollback; Model Council com identidades lógicas; Digital Twin; geração Nix proposta. `build-report.json` pode declarar `isolated: true` em uma simulação: trate isso como descrição do mock, não evidência de isolamento real, e considere tornar o campo mais explícito em mudança futura.

## Testado nesta frente documental

- parse de `.claude/settings.example.json` via `ConvertFrom-Json`;
- parse sintático dos cinco scripts PowerShell e frontmatter dos nove agentes;
- `pre_tool_guard`: comando seguro não foi bloqueado; `git reset --hard` e edição da Constituição foram negados em payloads artificiais;
- `post_tool_checks`: JSON válido passou e edição protegida emitiu contexto de revisão;
- `stop_claim_guard`: disclaimer seguro passou e alegação “pronto para produção” foi bloqueada após uso explícito de UTF-8;
- `record_provenance`: gravou somente metadados sanitizados de uma sessão sintética;
- 37 arquivos Markdown verificados sem links locais quebrados.

Isso não testa integração com uma versão instalada do Claude Code. Não foi criado `settings.local.json`, portanto hooks não estão ativos por padrão.

## Validação integrada executada

Executada pelo agente principal em Python **3.12.13**, no Windows, após a integração das frentes:

- `uv 0.12.1`: `uv lock` e `uv sync --extra dev --frozen` concluídos com cache local ao projeto;
- `ruff format --check .`: 113 arquivos formatados;
- `ruff check .`: sem achados;
- `pyright`: 0 erros, 0 warnings;
- `pytest`: 39 testes aprovados, cobertura total 85,60%, acima do gate de 80%;
- `python scripts/validate_schemas.py`: 18 schemas e instâncias validados;
- `aionctl --help` e `aiond --once`: inicialização aprovada em modo simulation-only;
- cinco tarefas OS-EvoBench executadas individualmente com baseline determinístico: cada tarefa obteve `success=true` e score 1,0 no digital twin;
- fluxo FFmpeg: mutação `mut-183c4b75e3bb`, duas candidatas com `package.propose:ffmpeg`, seleção `obj-19937ce9a80e-minimal`, prova verificada, geração simulada `gen-c670e4fa724d` e estado final `rolled_back`;
- report persistido da tarefa `capability-install-ffmpeg`, run `a6a1edb454d199729145a58b`.

Esses resultados validam o software Python e a simulação observados nesta máquina. Não validam isolamento por VM, build Nix, boot, FFmpeg real, executor privilegiado ou segurança de produção.

## Não executado

Gitleaks, Semgrep, OSV-Scanner, Syft, Grype, CodeQL e Trivy locais; `nix flake check`; build/boot/rollback de VM; QEMU; Podman; FFmpeg real; integração com Claude Code e branch protection. Nix, QEMU e Podman não estavam instalados. O push foi registrado localmente, mas a consulta independente do repositório privado e dos GitHub Actions continuou indisponível: `gh auth status` informou token inválido e a integração oficial não possuía acesso ao repositório.

## Estado Git observado

- caminho local: `C:\Users\GABRIELA APSOL\Projects\aion-os`;
- branch: `main`;
- commits validados do bootstrap: `9db3a15` (`bootstrap safe AION OS MVP`) e `3dc63df` (`document validated handoff`); use o comando abaixo para obter o HEAD após atualizações posteriores;
- o `.git` criado no worktree ficou read-only por política da sandbox. O commit validado usa metadados Git separados em `C:\Users\GABRIELA APSOL\Projects\aion-os.git`, com `core.worktree` apontando para este diretório;
- remote configurado nesses metadados: `https://github.com/warlyjr-cloud/aion-os`;
- o reflog de `origin/main` registra `update by push` no commit `3dc63df`, e `main`/`origin/main` apontavam para o mesmo commit durante o fechamento;
- a URL privada, a visibilidade e os GitHub Actions não puderam ser confirmados independentemente porque o GitHub CLI permaneceu sem autenticação válida e a integração oficial retornou `404` sem acesso ao repositório;
- o `.git` interno continua sendo um repositório vazio protegido pela sandbox. O histórico válido permanece no Git dir separado; comandos de continuidade devem manter `GIT_DIR` até uma regularização feita fora da sandbox.

## Arquivos protegidos que exigem revisão humana

`docs/SAFETY_CONSTITUTION.md` e `docs/TCB_SPECIFICATION.md` foram criados neste bootstrap. Também trate `src/tcb/`, `policies/`, auditoria, rollback, benchmarks reservados e workflows de segurança como protegidos. O hook bloqueia novas edições por padrão, mas não substitui CODEOWNERS/branch protection.

## Riscos imediatos

1. O TCB é software Python de referência, não verificado formalmente nem resistente a adulteração.
2. Proof hashes/audit chain detectam algumas mudanças, mas não autenticam produtores nem garantem veracidade.
3. O VEK avança por estados de build/test/adversarial com relatórios simulados; consumidores precisam checar `status`/`simulated`.
4. O mesmo processo controla store, proofs e audit; não existe isolamento de autoridade forte.
5. Reserved tests estão no mesmo checkout; policy/teste podem impedir acesso lógico, não físico.
6. Hooks usam regex e PowerShell; checkout malicioso ou settings alterados podem contorná-los.
7. Nix/VM/boot/rollback e executor privilegiado real não foram validados nesta frente.
8. Licenças em prior art precisam ser pinadas; o arquivo `LICENSE` do AION deve ser revisado pelos mantenedores.

## Próxima tarefa recomendada

Em ambiente Linux/WSL separado, executar build/boot/rollback de VM real. Em seguida, executar os scanners locais, revisar humanamente a Constituição/TCB e substituir evidências simuladas de build/teste por resultados isolados antes de ampliar autoridade.

## Comandos de continuidade

```powershell
Set-Location "C:\Users\GABRIELA APSOL\Projects\aion-os"
$env:GIT_DIR = "C:\Users\GABRIELA APSOL\Projects\aion-os.git"
git status -sb
uv sync --extra dev
uv run ruff check .
uv run pyright
uv run pytest
```

Para Claude Code, revise `.claude/README.md`, copie o settings example localmente, rode `claude doctor` e confirme `/hooks`. Não use `--dangerously-skip-permissions`.
