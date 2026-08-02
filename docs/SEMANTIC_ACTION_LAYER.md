# Camada Semântica de Ações

## Regra

O executor aceita objetos validados, não texto de shell. A interpretação probabilística termina antes da fronteira de autoridade.

## Envelope mínimo

```json
{
  "schema_version": "1.0",
  "action_id": "act-unique",
  "action_type": "service.restart",
  "origin": {"agent_id": "planner", "mutation_id": "mut-001"},
  "intent_id": "intent-001",
  "target": "nginx",
  "required_capability": "service.restart:nginx",
  "risk_tier": 1,
  "timeout_seconds": 30,
  "resource_limits": {"cpu_seconds": 5, "memory_mb": 128},
  "network_policy": "deny",
  "expected_result": "service_healthy",
  "rollback_action": "service.restore_previous_state"
}
```

## Famílias

Arquivos, diretórios, pacotes, serviços, processos, rede, dispositivos, configurações, memória, skills, gerações e benchmarks. Cada subtipo define schema fechado, allowlist de alvos, pré/pós-condições e rollback compatível.

## Validação

1. Schema/version e campos desconhecidos.
2. Identidade/origem e vínculo ao contrato.
3. Capability exata, não wildcard implícito.
4. Tier de risco e aprovação.
5. Paths normalizados dentro do escopo, sem symlink escape.
6. Egress, recursos e timeout.
7. Reversibilidade e observabilidade.
8. Política e estado do emergency stop.

Falha em qualquer etapa produz `deny` com código estável. O executor registra pedido, decisão e resultado; não reinterpreta strings. No MVP, executores podem somente simular e devem retornar `execution_mode: simulated`.

## Shell de desenvolvimento

Permitido apenas em ambiente descartável e isolado, com aprovação humana, comando fixo/revisado, cwd restrito, egress negado, timeout e captura integral. Nunca é promovido a ação host por inferência.
