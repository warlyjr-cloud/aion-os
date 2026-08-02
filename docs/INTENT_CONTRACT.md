# Contrato de Intenção

## Função

Congelar antes da mutação o que deve melhorar, o que não pode mudar e como sucesso/falha serão decididos. O contrato reduz specification gaming, mas não o elimina.

## Campos obrigatórios

- `intent_id`, versão, autor, timestamp e objetivo;
- contexto e resultado esperado observável;
- restrições e invariantes constitucionais;
- dados autorizados/proibidos e classificação;
- tier de risco e risco residual aceitável;
- recursos, orçamento, prioridade e prazo;
- métricas, baseline, guardrails e tarefas reservadas referenciadas por ID;
- critérios de sucesso, interrupção e rollback;
- capabilities solicitadas, isolamento e egress;
- aprovações exigidas e separação de papéis;
- suposições e questões abertas.

## Validação

Objetivos críticos vagos, métricas controláveis pela candidata, ausência de baseline, conflitos de dados, rollback inexistente ou permissões amplas resultam em `requires_clarification`/`deny`. A candidata recebe apenas o que precisa; testes reservados não são incorporados ao prompt.

## Imutabilidade

Após `intent_validated`, mudanças semânticas criam nova versão e invalidam resultados anteriores. Hashes vinculam contrato, baseline, candidatas e prova. Aprovação de uma versão não vale para outra.

## Exemplo FFmpeg

Objetivo: reduzir tamanho mantendo limiar mínimo de qualidade. Proibido: instalar no host, ler arquivos fora da fixture, acessar rede. Baseline: bytes, tempo e qualidade da fixture. Guardrails: build simulado/isolado, nenhum path escape, nenhuma capability extra. Sucesso mock não autoriza instalação real.
