# Agenda de Pesquisa

## Contribuição pretendida

Um sistema operacional baseado em Linux declarativo capaz de demonstrar autoaperfeiçoamento acumulativo, verificável, reproduzível e seguro ao longo de múltiplas gerações. Esta é uma hipótese de pesquisa, não um resultado atual.

## Hipóteses

- **H1:** separar inteligência probabilística de autoridade determinística reduz violações sem eliminar ganhos de automação.
- **H2:** busca populacional/Pareto supera mutação única em retenção, diversidade e generalização sob budget equivalente.
- **H3:** proof bundles e avaliadores independentes reduzem promoção de regressões/fraudes.
- **H4:** memória com proveniência, quarentena e promoção resiste melhor a poisoning que memória gravada diretamente pelo agente.
- **H5:** NixOS generations tornam reconstrução/rollback mais confiáveis que mudanças imperativas equivalentes.
- **H6:** evolução do scaffolding (RSI-2/3) pode acumular ganho em tarefas ocultas sem alterar o TCB.

## Perguntas

1. Que composição de guardrails detecta reward hacking sem falsos bloqueios inviáveis?
2. Quanta independência entre proposer/critic/evaluator é necessária para reduzir erro correlacionado?
3. Como medir benefício acumulado sem leakage de tarefas reservadas?
4. Que metadados de memória preveem poisoning e quando quarentena/corroboração falham?
5. Qual camada de isolamento oferece melhor segurança/custo para cada ação?
6. Provas de supply chain ajudam a distinguir integridade de veracidade operacional?

## Métodos

- experimentos pré-registrados, seeds e budgets fixos;
- tarefas públicas para desenvolvimento e reservadas sob custódia separada;
- 20+ gerações/100 objetivos no estudo longitudinal;
- ablações de população, memória, council, provas e TCB gates;
- red team adaptativo e fault injection;
- repetição multi-hardware/provider e reprodução externa;
- análise de Pareto, curvas por geração, intervalos de confiança e incidentes qualitativos.

## Baselines

NixOS manual; NixOS com agente genérico; AION sem população; sem memória; sem Model Council; sem proof gate; AION completo. O mesmo objective set, hardware class, provider budget e tempo devem ser usados.

## Métricas

Sucesso e generalização; retenção/regressão; build/boot/health; latência/custo/CPU/RAM/energia/storage; capability surface; bloqueios corretos e falsos; violações; rollback RTO/RPO; reproducibilidade; diversidade/novelty; benefício acumulado; reward hacking; leakage e poisoning.

## Experimentos prioritários

1. FFmpeg mock como teste de plumbing, sem alegação científica.
2. EvoBench-5 reproduzível e ataques de falsificação/leakage.
3. Comparação memória direta versus quarantine+corroboration.
4. População/Pareto versus candidata única sob budget fixo.
5. NixOS Lab: build, boot, falha de serviço e rollback.
6. Estudo longitudinal multi-provider, com hidden holdout.

## Ameaças à validade

Overfitting/leakage, judge LLM enviesado, mocks não representativos, versões mutáveis de provider, erro correlacionado, hardware heterogêneo, survivor/publication bias, métricas manipuláveis, baixa potência estatística e benchmark criado pelos mesmos autores.

## Limitações éticas e operacionais

Nenhum experimento autoriza host real, dados de terceiros, propagação, persistência externa ou exfiltração. Escapes e red team usam ambientes descartáveis sem segredos. Treinamento do modelo-base, federação e autonomia nível 3+ estão fora do MVP.

## Critérios de publicação

Protocolos/datasets públicos onde seguro, código/lockfiles, resultados negativos, incidentes, todos os testes executados/não executados, custos, versões, proof bundles sanitizados, revisão de licença/privacidade e reprodução por equipe externa. “SOTA” exige baseline relevante e revisão pública, não apenas melhor resultado interno.
