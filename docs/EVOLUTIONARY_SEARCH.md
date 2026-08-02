# Busca Evolucionária

## Modelo

Cada objetivo cria uma `EvolutionPopulation`. `CandidateArchive` preserva candidatos e avaliações; `LineageGraph` registra pais/descendentes; `ParetoSelector` mantém opções não dominadas.

## Representação

Uma candidata contém identidade, parent IDs, mutador/provider, genome delta, actions, capabilities solicitadas, orçamento, novelty descriptor, métricas, guardrails, prova e status.

## Seleção

1. Rejeitar violações de constituição/política, evidência inválida e regressões críticas.
2. Normalizar métricas somente com baseline/versionamento conhecidos.
3. Computar dominância por vetores separados: sucesso, segurança, privacidade, latência, custo, recursos, complexidade, reproducibilidade e rollback.
4. Preservar diversidade/novidade e ancestrais úteis; não selecionar apenas máximo escalar.
5. Exigir avaliação de descendentes antes de recombinação/promoção.

## Anti-gaming

Métricas e testes reservados ficam fora da escrita da candidata; avaliadores são read-only e independentes; reports são recalculáveis; divergência entre telemetria e alegação elimina a candidata.

## MVP e pesquisa

MVP: duas ou três candidatas simuladas e Pareto determinístico. Futuro: mutation operators versionados, novelty search, retorno a ancestral, recombinação com compatibilidade e experimentos multi-geração. Diversidade sem performance útil não é melhoria; performance sem guardrail não é elegível.
