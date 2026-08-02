# Governança de Autonomia

## Níveis

| Nível | Permissão máxima |
|---|---|
| 0 | observar |
| 1 | recomendar |
| 2 | construir e testar isoladamente |
| 3 | promover baixo risco sob política explícita |
| 4 | operar canários limitados |
| 5 | evolução contínua governada |

Padrão do MVP: **nível 2 em modo simulado**. Níveis 3–5 não estão autorizados apenas por esta especificação.

## Budgets

Custo monetário, tokens, CPU, GPU, energia, wall time, armazenamento, rede, mutações, risco e promoções. Todo budget tem unidade, janela, dono, limite hard/soft e ação ao exceder. Hard limit interrompe com segurança; não há auto-aumento.

## Aprovação

Tier 0: leitura segura; tier 1: reversível e limitada; tier 2: mudança relevante; tier 3: sistema/segredo/rede/protected. Tier 2+ requer humano; tier 3 requer revisão adicional e janela de recuperação. Aprovação é vinculada a intent, candidate digest, ambiente e expiração.

## Controles

Emergency stop global e por objetivo; rate limits; max consecutive failures; canary scope; health thresholds; audit; revogação de capabilities; rollback target; manutenção humana. Indisponibilidade do aprovador bloqueia, não delega ao modelo.

## Escalonamento

Elevar autonomia exige relatório de incidentes, benchmark longitudinal, zero violações constitucionais observadas, rollback reproduzido e decisão humana documentada. Regressão ou drift reduz o nível automaticamente conforme política determinística.
