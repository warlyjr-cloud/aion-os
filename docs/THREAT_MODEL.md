# Modelo de Ameaças

## Ativos

Host e dados do usuário; TCB/constituição/políticas; capabilities; audit/proofs; benchmark reservado; memória/genome; chaves/provider credentials; lineage e rollback; disponibilidade do emergency stop.

## Adversários e trust boundaries

Candidata maliciosa/defeituosa, prompt injection em conteúdo externo, memória envenenada, provider comprometido, plugin/MCP/dependência maliciosa, insider, PR/fork não confiável e atacante de rede. LLM, outputs, tools externos, registry e fixtures externas são não confiáveis.

## Cenários prioritários

| Ameaça | Controle principal | Evidência exigida |
|---|---|---|
| root/shell livre | ação tipada + TCB + isolation | teste de negação |
| capability escalation/replay | tokens scoped/expiráveis/revogáveis | property tests/audit |
| prompt injection/exfiltração | separação data/instruction + egress deny | adversarial test |
| memory poisoning | quarantine + provenance + corroboração | longitudinal test |
| benchmark tampering/leakage | storage read-only/custódia externa | integrity/access log |
| report/proof forgery | recomputação + hashes + verificador independente | verification report |
| TCB/policy mutation | protected paths + human review | diff gate |
| supply-chain compromise | pinning, SBOM, signatures, rebuild | provenance |
| sandbox escape | layered isolation, patched runtime, no secrets | escape test/review |
| rollback sabotage | target validation + independent recovery | fault-injection test |

## Resíduos

Hooks e regex não são sandbox; hashes não garantem verdade; múltiplos agentes podem compartilhar falhas; Nix não elimina fonte maliciosa; zero achados não prova ausência. Até isolamento e recovery reais serem validados, promoção no host permanece fora do escopo.

## Abuso proibido

Autorreplicação, propagação, persistência externa, exfiltração, evasão de controles, desativação de logs/stop/rollback e alteração de usuários/boot/kernel/firewall sem processo humano específico.
