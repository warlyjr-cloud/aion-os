# Dados e Privacidade

## Padrão

Local-first, minimização e telemetria desativada. Não coletar ou enviar dados por conveniência. Egress exige finalidade, destino, classificação, retenção e consentimento explícitos no contrato/capability.

## Classes

Público; interno; confidencial; segredo; dado pessoal/sensível; benchmark reservado. Segredos e dados pessoais não entram em prompts, memória evolutiva, logs, fixtures ou proof bundles.

## Ciclo de dados

1. Inventariar fonte, dono, finalidade e base/autorização.
2. Minimizar/redigir antes de provider ou twin.
3. Restringir por capability e ambiente.
4. Registrar metadados de processamento sem reproduzir conteúdo sensível.
5. Aplicar retenção/expiração e deletion verificável quando autorizada.
6. Incluir memória/índices/caches no rollback e incident response.

## Providers

Cada adapter declara dados transmitidos, região, retention/training defaults, logs, subprocessadores e egress. Credenciais vêm de mecanismo externo; nunca de arquivo versionado. MockProvider é padrão offline.

## Direitos e governança

Exportação, correção, revogação e remoção devem alcançar memória derivada e provas compatíveis, preservando apenas registros mínimos legalmente/tecnicamente necessários. Conflitos com audit imutável exigem desenho de pseudonimização, não promessa vazia.

## Pendências

Ainda são necessários DPIA/avaliação jurídica por jurisdição, modelo de consentimento, retention schedule, redaction verificável e testes de leakage. Este documento não é parecer jurídico.
