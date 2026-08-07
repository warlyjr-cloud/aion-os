# Especificação do Verifiable Evolution Kernel (VEK)

## Propósito

O VEK é o núcleo lógico não privilegiado que transforma objetivos em evoluções candidatas comprováveis. Ele não é kernel Linux e não possui autoridade para contornar o TCB.

## Entradas e saídas

Entradas: contrato de intenção validado, baseline, genome atual, capabilities concedidas, orçamento, políticas e providers disponíveis. Saídas: candidatas, lineage, relatórios, frontier, decisão proposta, proof bundle e plano de rollback.

## Máquina de estados

```text
draft -> intent_validated -> planned -> candidates_generated -> policy_checked
-> building | build_failed -> testing | test_failed -> adversarial_testing
-> evaluated -> archived | awaiting_approval -> approved | rejected
-> promoting -> promoted -> monitoring -> rolled_back | failed
```

Toda transição é total sobre entradas válidas, rejeita origem/estado inesperado, registra ator, timestamp, evidência e motivo, e só ocorre após validação do TCB.

## Pipeline normativo

1. Validar contrato e capturar baseline antes de gerar candidatas.
2. Gerar pelo menos duas candidatas quando houver busca populacional.
3. Registrar `candidate_id`, `parent_ids`, mutador, provider, parâmetros e diffs.
4. Aplicar políticas antes de build e novamente antes de promoção.
5. Executar build, teste, benchmark e red team em isolamento compatível com o risco.
6. Eliminar qualquer candidata que viole guardrail; não compensar segurança com desempenho.
7. Manter arquivo e fronteira de Pareto com métricas independentes.
8. Produzir proof bundle completo e solicitar aprovação apropriada.
9. Promover atomicamente, monitorar saúde e reverter quando critérios de interrupção forem atingidos.

## Invariantes

- VEK não emite capabilities para si mesmo nem altera TCB, constituição, avaliadores ou métricas reservadas.
- Proponente não pode registrar a própria verificação como independente.
- Resultados `simulated` e `executed` são tipos distintos e não intercambiáveis.
- Falha/timeout de etapa obrigatória bloqueia, nunca vira sucesso parcial implícito.
- Cada geração aponta para ancestral válido e rollback target verificado.

## MVP versus futuro

MVP: duas candidatas mock, `CandidateArchive`, `LineageGraph`, `ParetoSelector`, estado local e provas com hashes. Futuro: builders próprios (AION-native)/VM reais, novelty search, recombinação controlada, canary, attestations e evolução RSI-3/3.5. Nenhuma dessas capacidades futuras é inferida pelo scaffold.
