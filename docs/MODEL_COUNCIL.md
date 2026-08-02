# Model Council

## Papéis

Planner, Builder, Nix Specialist, Security Reviewer, Critic, Evaluator, Red Team e Local Privacy Model são identidades lógicas. No MVP, podem compartilhar um `MockProvider`; isso testa separação de workflow, não independência estatística ou organizacional.

## Roteamento

Risco, complexidade, custo, latência, privacidade, histórico de calibração, disponibilidade e budgets. Dados classificados devem preferir modelo local/permitido; ausência de rota compatível resulta em bloqueio/esclarecimento.

## Regras

- proponente não aprova sozinho;
- mudança crítica exige verificador independente e humano;
- prompts, modelos, parâmetros, tools e outputs têm proveniência;
- contextos reservados não vazam para proponente;
- council recomenda; TCB decide autoridade;
- falha/indisponibilidade não reduz quorum silenciosamente.

## Independência real

Para alegar independência, variar provider/model family, operador, prompt lineage e canal de falha; medir correlação de erros. Múltiplas personas do mesmo modelo não bastam.

## Futuro

Adapters OpenAI/Codex, Anthropic/Claude, Gemini, local e APIs compatíveis, todos com egress explícito, redaction, timeout, custo e retention policy. Nenhuma chave fica em prompt, log ou repositório.
