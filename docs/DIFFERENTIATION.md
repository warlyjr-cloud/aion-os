# Diferenciação

## Hipótese de diferenciação

Outros sistemas usam IA para operar o computador ou orquestrar agentes. O AION foca em produzir, comparar e comprovar uma próxima geração declarativa do sistema antes de promovê-la.

| Dimensão | Assistente/agent OS típico | AION pretendido |
|---|---|---|
| Unidade de ação | comando/tool call | ação tipada + capability |
| Mudança | execução imediata | candidata isolada |
| Avaliação | resposta/resultado pontual | baseline, guardrails, Pareto e testes ocultos |
| Autoridade | frequentemente acoplada ao agente | TCB determinístico separado |
| Memória | contexto recuperável | confiança, proveniência, quarentena e rollback |
| Continuidade | logs/sessões | linhagem, gerações e proof bundle |
| Reversão | ad hoc | requisito de promoção |

## O que reutilizar

- NixOS como referência de prior art para estado declarativo, generations e rollback (citação conceitual; AION não depende de NixOS).
- microVM/VM/Wasm como camadas futuras de isolamento, sem tratá-las como prova automática.
- SLSA, in-toto e Sigstore para formatos e mecanismos de proveniência, sem criptografia própria.
- OPA/Rego como adaptador futuro, mantendo policy engine mínimo determinístico no MVP.

## Moat técnico pretendido

VEK + TCB + corpus de provas multi-geração + EvoBench resistente a manipulação. O moat ainda é uma hipótese: depende de evidência comparativa e adoção, não do volume de documentação ou scaffolding.
