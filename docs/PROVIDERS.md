# Providers de modelo

## Interface

`ProviderAdapter` recebe prompt/contexto sanitizados, role, risk tier, budget, timeout e schema de saída; retorna output estruturado, model ID/version, usage, latency, finish reason, policy metadata e erro explícito.

## Implementações pretendidas

- `MockProvider`: determinístico, offline e padrão do MVP.
- OpenAI/Codex, Anthropic/Claude e Gemini: adaptadores futuros com rede allowlisted.
- Local: endpoint/runtime local com avaliação de capacidade e recursos.
- Compatible API: somente após revisão de origem, TLS, retention e auth.

## Regras

Provider nunca recebe capability de runtime nem promove mudanças. Segredos são injetados fora de prompts/logs; retries são limitados e idempotentes; output invalida em schema mismatch; fallback não reduz privacy/risk tier; versão e parâmetros entram na proveniência.

## Seleção

Privacidade e risco são filtros; depois custo, latência, qualidade histórica e disponibilidade. Dados confidenciais sem provider autorizado resultam em bloqueio, não fallback público.

## Testes

Contract tests sem rede, timeout, malformed output, usage inconsistente, indisponibilidade, retry budget, redaction e circuit breaker. Testes reais precisam de conta/consentimento e não podem vazar secrets em CI.
