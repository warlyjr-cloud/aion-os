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

## Scaffold funcional (roda, mas só em simulação/mock)

| Componente | O que existe | O que falta pra sair de "simulado" |
|---|---|---|
| `SafeExecutor` para `service.configure`/`file.patch` | Sempre retorna `"verified successfully"` sem ação real | Implementar a ação real por tipo, como já foi feito para `package.propose` |
| `EvoBenchRunner` (as 5 tarefas completas) | Roda de verdade, mas contra um "gêmeo digital" (`DigitalTwin`), não infraestrutura real | Rodar candidatos contra ambiente real, não só o twin |
| `AnthropicProvider` | Código real, nunca exercitado ponta a ponta nesta sessão (só `MockProvider` foi usado nas provas) | Rodar um ciclo real com API key de verdade e revisar a proposta gerada |
| `src/grid/p2p.py` (Multiverse Battle / gossip) | 113 linhas, usa `random` pra decidir "qual universo vence" — mecanismo de consenso simbólico, não um protocolo P2P real testado em rede | Definir o que "consenso real" significa pro produto antes de investir mais aqui |
| `src/quantum_fs/fuse_driver.py` | FUSE real (via lib `fuse`), mas gera conteúdo de arquivo chamando um LLM sob demanda — nunca montado/testado neste ambiente (Windows não tem FUSE) | Testar em Linux com FUSE instalado |
| `src/relativity/scheduler.py` | `SIGSTOP`/`SIGCONT` reais em processos pesados — mecanismo real de SO, mas testado só em `start()`/`stop()`, nunca de fato pausando um processo | Teste de integração pausando/retomando um processo de verdade |
| `src/aiond/genesis_lock.py` (Dead Man's Switch) | O comentário no próprio código diz: *"For the MVP/Demo, we simulate a failure if the file doesn't exist... we will bypass it for the local test"* — ou seja, o próprio autor documentou que o bypass é intencional para demo | Decidir se esse "kill switch" deve ser real antes de qualquer claim de segurança sobre ele |

## Stub/visão (estrutura existe, lógica real não)

| Componente | Realidade encontrada nesta sessão |
|---|---|
| `kernel/src/pqc.rs` (Post-Quantum Cryptography) | `LatticeCryptoEngine` tem `public_matrix: [[0; 4]; 4]` (matriz de zeros) e `is_quantum_resistant: true` hardcoded. Não há Kyber/Dilithium real — o comentário no código diz "Stub para chaves". |
| `kernel/src/zkp.rs` (Zero-Knowledge Proof verifier) | `SNARKVerifier::verify_proof()` **sempre retorna `true`**, com comentário `// Stub: A verdadeira implementação calcularia a verificação polinomial`. Isso verifica nada. |
| `kernel/` como um todo | 133 linhas Rust ao todo (`main.rs`, `vga.rs`, `depin.rs`, `pqc.rs`, `zkp.rs`). Nunca compilado/testado nesta sessão — não há evidência de que builda, muito menos boota. |
| `clients/android_edge_node/` | ~1.500 linhas Kotlin (mais substancial que o kernel), incluindo um `PoStDaemonService` e `MainActivity`. Não verificado nesta sessão se compila ou roda em um dispositivo/emulador real. |
| `src/evolution/polymorph.py` (auto-modificação de código) | Real e testado (reescreve `src/executor/*.py` em disco via AST), continua sendo uma feature de risco elevado por design — reescrever o próprio executor de segurança automaticamente merece revisão humana antes de qualquer claim de "seguro". **Incidente real, não hipotético**: até 2026-08-08 essa reescrita disparava com 10% de chance a cada `run_once()`, incondicionalmente — e `scripts/verify_readme.py` chama `run_once()` contra o checkout real da CI. Isso corrompeu `src/executor/safe.py` no meio do pipeline de CI (nunca chegou a ser commitado — é mutação em disco no runner efêmero — mas quebrou a importação do pacote). Corrigido exigindo opt-in explícito (`AION_ENABLE_POLYMORPHISM=1`, padrão desligado) antes do sorteio acontecer, com teste de regressão travando esse comportamento. |

## Como manter isso atualizado

Sempre que algo sair de "stub" pra "provado", documente a evidência (comando
rodado, saída real, não só a alegação) em `docs/PROOF_OF_REAL_EXECUTION.md`
e mova a linha aqui. Não mova algo pra "provado" só porque o código foi
escrito — só porque rodou e a saída foi capturada.
