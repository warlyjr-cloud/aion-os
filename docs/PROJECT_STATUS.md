# Estado real do projeto: provado vs. visão

Registrado em **2026-08-07**, atualizado em **2026-08-08**, depois da
sessão que produziu `docs/PROOF_OF_REAL_EXECUTION.md`. Objetivo: dar a
qualquer pessoa (você, um investidor, um novo contribuidor) uma resposta
honesta e específica pra "isso funciona de verdade?" — componente por
componente, sem apagar nada e sem inflar nada.

Categorias:
- **Provado**: rodou de verdade nesta ou em sessões anteriores, com
  evidência capturada (não é a mesma coisa que "testado exaustivamente"
  — ver limitações em cada item).
- **Scaffold funcional**: código real, roda, mas cobre um caminho feliz
  simulado/mockado — não foi exercitado fora de simulação.
- **Stub/visão**: existe como estrutura (assinatura de função, comentário
  descrevendo intenção) mas a lógica real não está implementada — inclui
  casos onde o código literalmente sempre retorna um valor fixo.

## Provado

| Componente | Evidência |
|---|---|
| `plan → approve → promote → rollback` com execução real (`nix build`) | `docs/PROOF_OF_REAL_EXECUTION.md` |
| `DeterministicVerifier` (segunda camada de revisão, não-LLM) | 24 testes, `src/model_council/deterministic_verifier.py` |
| `CapabilityStore` (grant durável, expiração, revogação) | testado ao vivo via CLI + 4 testes unitários |
| Dashboard `/api/mutations/{id}` (decisão real, não só status) | 2 testes de integração |
| Benchmark comparativo (guiado 1.0 vs. ingênuo 0.253) | `benchmarks/os_evobench/reports/comparative-guarded-vs-naive.json` |
| Trilha de auditoria com hash encadeado | `.aion-state/audit.jsonl`, verificado em `AuditLog.verify()` |
| Pipeline de CI completa passando ponta a ponta (lint, type check, 76 testes, verificação de release, scan de segredos, gitleaks sobre histórico completo, SBOM, build do dashboard) | `gh run list` no commit `6568212` — todos os 5 workflows com conclusão `success`. Chegar até aqui exigiu corrigir 3 bugs reais encontrados só porque o pipeline rodou de ponta a ponta pela primeira vez (ver abaixo) |
| `service.configure` executando contra infraestrutura de terceiro real (não o próprio repo) | `docs/PROOF_OF_REAL_EXECUTION.md` — VM GCP real (`aion-pilot-vm-01`), `cron` habilitado/iniciado via SSH pelo `SafeExecutor`, reverificado de forma independente na própria VM (`systemctl is-enabled`/`is-active`, não a saída do AION) |

## Scaffold funcional (roda, mas só em simulação/mock)

| Componente | O que existe | O que falta pra sair de "simulado" |
|---|---|---|
| `SafeExecutor` para `file.patch` | Sempre retorna `"verified successfully"` sem ação real | Implementar a ação real, como já foi feito para `package.propose`, `dependency.bump` e `service.configure` |
| `EvoBenchRunner` (as 5 tarefas completas) | Roda de verdade, mas contra um "gêmeo digital" (`DigitalTwin`), não infraestrutura real | Rodar candidatos contra ambiente real, não só o twin |
| `AnthropicProvider` | Código real, nunca exercitado ponta a ponta nesta sessão (só `MockProvider` foi usado nas provas) | Rodar um ciclo real com API key de verdade e revisar a proposta gerada |
| `src/generative_fs/fuse_driver.py` (antes `src/quantum_fs/`) | FUSE real (via lib `fuse`), mas gera conteúdo de arquivo chamando um LLM sob demanda — nunca montado/testado neste ambiente (Windows não tem FUSE) | Testar em Linux com FUSE instalado |
| `src/throttle/cpu_throttle.py` (antes `src/relativity/scheduler.py`) | `SIGSTOP`/`SIGCONT` reais em processos pesados — mecanismo real de SO, mas testado só em `start()`/`stop()`, nunca de fato pausando um processo | Teste de integração pausando/retomando um processo de verdade |

## Stub/visão (estrutura existe, lógica real não)

| Componente | Realidade encontrada nesta sessão |
|---|---|
| `src/evolution/polymorph.py` (auto-modificação de código) | Real e testado (reescreve `src/executor/*.py` em disco via AST), continua sendo uma feature de risco elevado por design — reescrever o próprio executor de segurança automaticamente merece revisão humana antes de qualquer claim de "seguro". **Incidente real, não hipotético**: até 2026-08-08 essa reescrita disparava com 10% de chance a cada `run_once()`, incondicionalmente — e `scripts/verify_readme.py` chama `run_once()` contra o checkout real da CI. Isso corrompeu `src/executor/safe.py` no meio do pipeline de CI (nunca chegou a ser commitado — é mutação em disco no runner efêmero — mas quebrou a importação do pacote). Corrigido exigindo opt-in explícito (`AION_ENABLE_POLYMORPHISM=1`, padrão desligado) antes do sorteio acontecer, com teste de regressão travando esse comportamento. |

## Removido em 2026-08-08: componentes que eram apenas maquiagem

Os itens abaixo saíram do repositório inteiramente, não só desta tabela.
Motivo: eram alegações de capacidade que nunca existiram de fato, e em
um caso (`AION_WHITEPAPER.md`) contradiziam diretamente este documento
— o whitepaper afirmava "Software Architecture & Physics Validated...
fully engineered, compiled, and mathematically validated" para o mesmo
kernel que esta tabela já documentava como "nunca compilado/testado".

| Removido | Por quê |
|---|---|
| `kernel/` (Rust, `main.rs`/`vga.rs`/`depin.rs`/`pqc.rs`/`zkp.rs`) | Nunca compilado nesta sessão; `zkp.rs` sempre retornava `true` na verificação; `pqc.rs` tinha matriz de chave zerada apresentada como "quantum resistant". |
| `clients/android_edge_node/` | ~1.500 linhas Kotlin nunca verificadas compilando ou rodando em dispositivo/emulador real. |
| `src/grid/p2p.py` ("Multiverse Battle" / gossip) e os endpoints `/grid/gossip`, `/grid/status` do dashboard | Consenso decidido por `random.choice`, não um protocolo P2P real. |
| `.github/workflows/release.yml` ("Build and Release AION Microkernel") | Workflow órfão depois da remoção do `kernel/`. |
| `AION_WHITEPAPER.md`, `INVESTOR_PITCH.md`, `PROJECT.md` | Documentos de marketing descrevendo a arquitetura acima (DePIN, PQC, ZKP, "relativistic scheduling", "quantum entanglement sync") como validada e funcional. `ORIGINAL_REQUEST.md` (mantido como registro histórico) mostra que a instrução original por trás desses arquivos era literalmente inflar valuation. |
| `.agents/` (77 arquivos, ~376K) | Anotações internas de um swarm de agentes anterior (BRIEFING/DISPATCH/handoff/progress de "workers" fictícios) — o rascunho de como a decoração acima foi fabricada, sem valor de produto. |
| `src/aiond/genesis_lock.py` ("Dead Man's Switch") | Decoração pura, não só sub-testada: `GENESIS_PUBLIC_KEY` é uma string hardcoded (o comentário admite "in a real scenario, this would be an Ed25519 or RSA key"), a "verificação de assinatura" é um `in` de string, e o valor de retorno era descartado por `daemon.py` — ou seja, mesmo quando "falhava", nada era de fato travado. |
| `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`, About do GitHub | Reescritos: descreviam "a maior rede de infraestrutura física descentralizada do mundo", SGX, Ring 0, ZKP como reais; homepage apontava pra um domínio (`aion-os.com`) nunca usado no projeto. |
| `LICENSE` | "Licensor: AION Labs" (entidade fictícia) e cláusula proibindo competir com uma "rede DePIN da AION Labs" inexistente. Corrigido pro nome real do mantenedor, cláusula DePIN removida. |
| `docs/audit_report.md`, `docs/SECURITY_AUDIT_R1.md` | Não removidos (são registro histórico de auditoria), mas receberam nota de retratação: seus vereditos "100% SECURE"/"Fully compliant" descreviam o `kernel/` falso como real. A conclusão específica sobre ausência de vazamento de "Oracle/Fleet Manager" segue válida. |

O que **não** foi removido, por ser mecanismo real (só sub-testado, não
fabricado): `src/generative_fs/fuse_driver.py` (FUSE real),
`src/throttle/cpu_throttle.py` (`SIGSTOP`/`SIGCONT` reais),
`src/evolution/parallel_race.py` (paralelismo real via
`ThreadPoolExecutor`). Esses três **foram renomeados** em 2026-08-08
(de `quantum_fs`, `relativity`/`TimeDilationEngine` e
`schrodinger`/`SchrodingerExecutor`) — o mecanismo é idêntico, só a
nomenclatura de física deixou de existir, porque ela também é o tipo de
coisa que convida a alegação errada mais tarde.

## Como manter isso atualizado

Sempre que algo sair de "stub" pra "provado", documente a evidência (comando
rodado, saída real, não só a alegação) em `docs/PROOF_OF_REAL_EXECUTION.md`
e mova a linha aqui. Não mova algo pra "provado" só porque o código foi
escrito — só porque rodou e a saída foi capturada.
