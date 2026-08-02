# Especificação da Trusted Computing Base

> Documento protegido. Alterações exigem revisão humana explícita e independente.

## Objetivo e limite

O TCB é o menor conjunto determinístico capaz de manter autoridade, integridade do fluxo, parada e reversão mesmo quando modelo, provider, VEK ou candidata falham. Não depende de LLM e não aprende em runtime.

## Componentes mínimos

- Constituição de Segurança versionada.
- Policy Engine e Action Validator.
- Capability Validator: assinatura/identidade futura, escopo, validade, revogação e uso.
- State Machine Validator.
- Evidence Verifier: schema, completude, checksums, origem e separação de papéis.
- Privileged Executor com allowlist de ações tipadas; inexistente/inerte no modo simulation-only.
- Audit Engine append-only pretendido.
- Emergency Stop e Rollback Controller.
- Promotion Rules e aprovação humana.

## Invariantes normativas

1. Ação sem capability válida é rejeitada.
2. Transição não listada é rejeitada.
3. Texto livre nunca alcança executor.
4. Candidatas não escrevem no TCB, constituição, políticas fundamentais, auditoria, rollback ou benchmark reservado.
5. Promoção exige evidência completa, guardrails aprovados, rollback válido e separação de funções.
6. Operação de risco alto exige aprovação humana explícita e específica.
7. Emergency stop, auditoria e rollback não podem ser desativados por agentes.
8. Falha de dependência externa mantém o sistema em estado não promovido.

## Interface pretendida

Entradas são estruturas validadas, nunca comandos. Decisões são `allow`, `deny`, `requires_approval`, `requires_clarification` ou `requires_additional_isolation`, acompanhadas por código estável e motivo. A interface futura via UDS deve autenticar peer, limitar tamanho, usar timeouts e negar por padrão.

## Mudança e verificação

Mudanças no TCB usam branch `security/*`, dois revisores (ao menos um humano), testes unitários/property/security, diff de arquivos protegidos e prova separada. A candidata em avaliação não pode selecionar ou modificar seu verificador.

## Estado do MVP

Qualquer implementação atual deve ser tratada como referência de software, não como TCB formalmente verificada. Coverage, pyright ou testes sem escape não provam segurança. Executor privilegiado real, assinaturas, tamper resistance, boot trust e verificação formal permanecem pendentes até evidência registrada.
