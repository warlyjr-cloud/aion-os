# Lacuna para estado da arte

## Estado atual

O projeto **não é estado da arte**, não demonstra RSI completo e não está pronto para produção. A documentação define um alvo; schemas, mocks e testes locais, quando presentes, cobrem apenas uma parcela do sistema.

## Evidência ainda necessária

| Alegação | Evidência mínima | Situação |
|---|---|---|
| melhoria acumulativa | 20+ gerações, curvas e ablações | pendente |
| generalização | tarefas ocultas fora da distribuição | pendente |
| preservação | suíte histórica sem regressões | pendente |
| segurança | red team independente, escape tests e revisão | pendente |
| reprodutibilidade | reconstrução por outra máquina/equipe | pendente |
| RSI-2 | criação e promoção controlada real, sem host livre | fluxo controlado demonstrado somente em simulação; promoção real pendente |
| RSI-3/3.5 | evolução do agente/melhorador com avaliador imutável | fora do MVP |
| superioridade | NixOS manual, agente genérico e ablações | pendente |
| rollback | falha pós-promoção e restauração medida em VM/host | pendente |

## Gaps técnicos críticos

- isolamento real e políticas de egress não validados;
- executor privilegiado mínimo e canal UDS não endurecidos;
- assinaturas, attestations, SBOM e verificação externa pendentes;
- benchmark reservado precisa de custódia independente;
- defesa de prompt injection/memory poisoning precisa de avaliação adaptativa;
- Model Council mock não equivale a independência de modelos/operadores;
- custo, energia, diversidade e novelty precisam de medição consistente;
- comportamento NixOS/VM/boot ainda depende de ambiente Linux apropriado.

## Regra de alegação

Toda comunicação deve separar: implementado, testado, simulado, preparado e pendente. Ausência de falha observada não é evidência de segurança absoluta.
