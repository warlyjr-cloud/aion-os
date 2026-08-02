# Arquitetura

## Contexto e fronteiras

O AION é uma camada de evolução sobre Linux/NixOS; não substitui o kernel. A fronteira principal separa componentes probabilísticos e não confiáveis (modelos, planners, conteúdo externo) da autoridade determinística (TCB, policy enforcement, executor tipado, auditoria e rollback).

```text
                    plano de dados não confiável
User -> Intent -> Provider/Model Council -> Candidate Population
                 |                              |
                 +---- propostas tipadas -------+
                                      |
                                      v
                 plano de controle determinístico
        Policy -> TCB -> Sandbox/Builder -> Evaluators
                   |            |              |
                   +------ Proof Engine <------+
                              |
                 Human approval / Promotion / Rollback
```

## Componentes

- `aionctl`: CLI não privilegiada; apresenta estado e solicita ações.
- `aiond`: orquestrador local; futura comunicação por Unix Domain Socket.
- VEK: máquina de evolução, população, lineage, seleção e proof bundle.
- TCB: invariantes, state machine, capabilities, evidência, emergency stop e regras de promoção.
- Intent Engine: transforma objetivo em contrato validável; ambiguidade crítica exige esclarecimento.
- Semantic Action Layer: converte planos em ações com schema; texto livre não executa.
- Capability Manager: emissão, escopo, validade, uso, revogação e auditoria.
- Provider/Model Council: propostas e críticas; nenhum provider recebe autoridade.
- Evaluator/Red Team: guardrails, métricas públicas e reservadas, avaliação independente.
- Immune Memory/Genome: estado versionado com proveniência e rollback coordenado.
- Digital Twin: interface para shadow/canary/fault injection; simulado no MVP.
- Proof/Audit: conteúdo endereçado, logs append-only pretendidos e verificações.

## Fluxo de confiança

1. Contrato válido fixa objetivo, escopo, métricas, dados e limites.
2. Candidatas não confiáveis são geradas com ancestralidade.
3. Policy Engine decide `deny`, `clarify`, `approve`, `additional_isolation` ou `allow`.
4. Build/teste ocorrem no maior isolamento disponível; mock deve ser rotulado.
5. Guardrails determinísticos e adversariais eliminam candidatas.
6. Pareto compara somente sobreviventes, sem colapsar tudo em uma nota.
7. Proof Engine agrega relatórios e checksums; verificadores confirmam completude/integridade.
8. Promoção crítica requer humano; health monitor pode acionar rollback pré-definido.

## Modelo de implantação

- MVP local: processo sem privilégio, MockProvider, SQLite/JSONL e temporários.
- Lab: VM NixOS/QEMU com serviço systemd, após validação real.
- Futuro: Podman rootless, Wasmtime e Firecracker conforme risco; TPM/measured boot como defesa adicional.

## Falhas seguras

Entrada inválida, capability ausente/expirada, estado inválido, evidência incompleta, budget esgotado, avaliador indisponível ou hash divergente impedem promoção. O sistema deve continuar capaz de auditar, parar e reverter sem LLM.
