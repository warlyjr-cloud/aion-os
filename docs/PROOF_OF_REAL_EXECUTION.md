# Prova de execução real (não simulada)

Registrado em **2026-08-07**. Este documento descreve o primeiro ciclo completo
`plan → approve → promote → rollback` executado de ponta a ponta **fora do modo
simulation**, com evidência real capturada — não um relatório com
`"status": "simulated"` hardcoded.

## Ambiente

- Host: WSL2 Ubuntu 24.04, com Nix (Determinate Nix 3.21.9) instalado e
  funcional.
- `AION_RUNTIME_MODE=real` e `AION_ALLOW_HOST_MUTATION=1` (as duas chaves
  exigidas por `src/executor/safe.py` — ver `docs/HANDOFF_TO_CLAUDE.md` para o
  histórico de por que a segunda chave existe).
- Provider: `MockProvider` (offline, determinístico — sem chamada de LLM
  real nesta execução específica).

## O que foi corrigido para isso funcionar

`src/executor/safe.py` tentava sempre alcançar o Nix pulando por um binário
`wsl` — o que só faz sentido quando o processo AION roda nativamente no
Windows e precisa saltar para dentro do WSL. Rodando o processo já dentro do
Linux/WSL (o ambiente de produção real, não o Windows de desenvolvimento),
não existe binário `wsl` — e o Nix já está direto no PATH. Corrigido para
detectar `nix` nativo primeiro, com o salto por `wsl` como fallback apenas
quando necessário.

## O que foi provado

1. **`plan()` nunca executa de verdade.** Os dois candidatos gerados
   (`obj-854976bf31d2-balanced`, `obj-854976bf31d2-minimal`) saem com
   `"simulated": true` — como projetado depois da correção de segurança
   anterior (execução real só pode acontecer em `promote()`, após aprovação
   humana).

2. **`promote()` executou um `nix build nixpkgs#ffmpeg` real.**
   `post-promotion-report.json`:
   ```json
   {
     "execution_result": {
       "action_id": "promote-mut-774079d0ed4a",
       "status": "success",
       "simulated": false
     },
     "host_modified": true,
     "simulated": false
   }
   ```
   Tempo real de execução: 4m0s (compatível com download/build reais de
   pacotes, não um mock instantâneo). O pacote `ffmpeg-8.1.2` ficou
   fisicamente presente no Nix store (`/nix/store/...-ffmpeg-8.1.2-man`),
   verificado por listagem direta do diretório, não pela saída do próprio
   AION.

3. **`rollback()` reverteu de verdade.** `current_generation()` era
   `gen-ab6478473b87` (real) antes do rollback e passou a `None` depois —
   consistente, já que essa geração não tinha pai (era a primeira).

4. **Trilha de auditoria com hash encadeado, real.** `audit-trail.jsonl`
   (cópia do `.aion-state/audit.jsonl` real da execução) mostra
   `generation.promoted` e `generation.rolled_back` — não as variantes
   `_simulation` — cada evento com `previous_hash`/`event_hash`
   verificável.

## O que isso NÃO prova

- Isolamento real de execução (o `nix build` rodou no mesmo WSL sem sandbox
  adicional; não há VM/container isolado nesta prova).
- Um segundo ciclo com um pacote diferente, ou com o `AnthropicProvider`
  real (esta prova usou `MockProvider`, então o conteúdo da proposta era
  fixo e conhecido, não gerado por LLM).
- Comportamento sob concorrência (múltiplas mutações simultâneas).
- Que `benchmark.run_tests` (a segunda ação real do executor) foi exercitada
  nesta prova — só `package.propose` foi testado ponta a ponta aqui.

## Benchmark comparativo real: AION guiado vs. baseline ingênuo

Além do ciclo real acima, rodamos o mesmo harness OS-EvoBench
(`src/evaluator/runner.py`) contra dois candidatos distintos, ambos
avaliados pelas mesmas 5 tarefas, testes públicos e reservados:

- `aion-deterministic-baseline-v1` (`src/evaluator/baseline.py`): segue o
  caminho declarativo completo (propõe capability, restaura serviço via
  ação tipada, aplica preset balanceado, ativa firewall + desabilita senha
  SSH, coloca memória não confiável em quarentena).
- `aion-naive-unguarded-v1` (`src/evaluator/naive_baseline.py`): faz o
  "atalho" que um agente sem guardrails tomaria em cada tarefa — pula a
  quarentena e usa a memória não confiável direto, reivindica sucesso sem
  executar a ação (reward hacking), aplica só metade do hardening, etc.

Resultado real (`benchmarks/os_evobench/reports/comparative-guarded-vs-naive.json`,
reproduzível via `python scripts/run_comparative_benchmark.py`):

| Candidato | Score | Tarefas com sucesso | Bloqueios do red-team |
|---|---|---|---|
| `aion-deterministic-baseline-v1` | **1.0** | 5/5 | 0/5 |
| `aion-naive-unguarded-v1` | **0.253** | 0/5 | 3/5 |

O `red_team.blocked` sendo real (3 das 5 tarefas do candidato ingênuo
foram capturadas pelo mecanismo de detecção do próprio harness — reward
hacking na tarefa de recuperação, memory poisoning na tarefa de memória
não confiável) é o que torna esse número diferente de uma alegação
qualquer: é o mesmo motor de avaliação, aplicado igualmente aos dois
candidatos, sem juiz humano no meio.

**O que isso NÃO prova**: não é uma comparação contra um agente de LLM
real e "livre" (o `NaiveBaseline` é código determinístico simulando o que
um agente descuidado faria, não um LLM de verdade sem guardrails rodando
de fato). Uma comparação com um provider real não-guiado é trabalho
futuro.

## Como reproduzir

```bash
# Dentro de um ambiente Linux/WSL com nix instalado e no PATH
git clone https://github.com/warlyjr-cloud/aion-os.git && cd aion-os
uv sync --extra dev
export AION_PROJECT_ROOT=$(pwd)
export AION_RUNTIME_MODE=real
export AION_ALLOW_HOST_MUTATION=1
uv run aionctl plan "I need to process video files"
uv run aionctl mutations approve <mutation_id> --actor "seu-nome"
uv run aionctl mutations promote <mutation_id>
```

Evidência bruta desta execução específica está preservada em
`proofs/mut-774079d0ed4a/` (incluindo `audit-trail.jsonl`, cópia do log de
auditoria real gerado durante esta prova).

## Segundo piloto real: patch management (dependency.bump), no próprio aion-os

Depois da primeira prova acima, implementamos um segundo tipo de ação real —
`dependency.bump` — e rodamos o caso de uso vertical proposto em
`docs/VERTICAL_USE_CASE.md` **contra o próprio repositório**, não contra um
sandbox descartável: atualizar a dependência `anthropic` (0.120.2 → mais
recente) usando `DependencyBumpProvider` (`src/providers/dependency_bump.py`),
com `AION_RUNTIME_MODE=real` e `AION_ALLOW_HOST_MUTATION=1`, no Windows local
(sem WSL/Nix — essa ação só precisa de `uv`).

**Resultado real, não simulado**: o `uv.lock` deste repositório tem
`anthropic == 0.121.0` porque o AION aplicou essa mudança de verdade, depois
de dois gates de verificação, aprovação humana explícita, e uma suíte de 72
testes reais rodando como verificação pós-mudança.

### As duas primeiras tentativas falharam de verdade — e isso é a parte boa

Rodar isso de propósito, ao vivo, contra o próprio código, encontrou **dois
bugs reais** que nenhuma simulação teria pego:

1. **Vazamento de ambiente**: o subprocess de verificação (`uv run pytest`,
   chamado de dentro de `_bump_dependency_and_verify`) herdava
   `AION_RUNTIME_MODE=real`/`AION_ALLOW_HOST_MUTATION=1` do processo pai —
   fazendo os próprios testes do projeto tentarem executar `nix build` de
   verdade dentro de si mesmos (e falhar, porque não há WSL/Nix nesse
   ambiente). Corrigido isolando o ambiente do subprocess de verificação
   (`src/executor/safe.py`, `verify_env`).
2. **Falha real não registrada em lugar nenhum**: quando `promote()` falhava
   de verdade, a mutação ficava presa em `approved` para sempre — sem
   transição de estado, sem evento de auditoria. Um humano teria que
   inspecionar logs manualmente pra entender o que aconteceu. Corrigido:
   falha real agora transiciona a mutação pra `archived` e grava um evento
   `generation.promotion_failed` no log de auditoria com hash encadeado
   (`src/vek/engine.py`).

Evidência do antes/depois, nas próprias mutações geradas por essas tentativas:

| Tentativa | Resultado | Estado final da mutação |
|---|---|---|
| `mut-f1211fba8b0f` (antes do fix 1) | Falhou por vazamento de ambiente | `approved` — presa, sem registro da falha |
| `mut-8ec3db613dbd` (depois do fix 1, antes do fix 2) | Falhou (mesma causa, log incompleto) | `approved` — presa, sem registro da falha |
| `mut-a47120c10d71` (depois de ambos os fixes) | Sucesso real | `monitoring` — `anthropic` 0.121.0 no lock, evidência completa em `proofs/mut-a47120c10d71/` |

Isso é exatamente o valor de rodar de verdade em vez de simular: nenhuma das
duas falhas apareceria numa demonstração cuidadosamente roteirizada.

### O que isso prova, e o que não prova

**Prova**: um segundo tipo de ação real (não só `package.propose`), o
caso de uso vertical proposto funcionando ponta a ponta contra o próprio
projeto, rollback real de arquivo (`uv.lock` restaurado byte a byte quando
os testes falhavam), e — talvez o mais importante — que dogfooding real
encontra bugs reais que documentação e simulação escondem.

**Não prova**: que isso funciona em outro gerenciador de pacote (npm, apt),
em outro sistema operacional além de Windows/Linux, ou sob uso concorrente
por múltiplos usuários/mutações ao mesmo tempo.

## Terceiro piloto real: fazer o pipeline de CI rodar de ponta a ponta pela primeira vez

Registrado em **2026-08-08**. Diferente dos dois pilotos acima (que provam
uma ação do executor), este documenta o que aconteceu ao levar a CI da
GitHub Actions do zero até `success` em todos os 5 workflows pela primeira
vez — cada etapa que passou revelou a próxima etapa que nunca tinha rodado
antes. São 3 bugs reais, nenhum deles hipotético ou de review de código:

1. **Auto-modificação corrompendo o próprio checkout da CI.**
   `src/aiond/daemon.py`'s `run_once()` tinha 10% de chance incondicional
   de chamar `polymorph_system()`, que reescreve um arquivo aleatório sob
   `src/executor/` via mutação AST. `scripts/verify_readme.py` invoca
   `run_once()` com `AION_PROJECT_ROOT` apontando pro checkout real do
   runner — então essa "auto-modificação" de risco elevado tinha chance
   real de corromper o próprio `src/executor/safe.py` em produção de CI,
   não em sandbox. Aconteceu: um `SyntaxError` no meio do pipeline, com
   conteúdo de arquivo visivelmente corrompido, nunca commitado (mutação
   em disco de runner efêmero). Corrigido com opt-in explícito
   (`AION_ENABLE_POLYMORPHISM=1`, padrão desligado).

2. **Scanner de segredos escaneando dependências vendorizadas como se
   fossem código-fonte.** `scripts/secret_safety_check.py` recursava em
   todo diretório sob a raiz do repo sem exclusão nenhuma — incluindo
   `.venv/` e `.uv-cache/`. Em um checkout limpo isso contém pacotes de
   terceiros instalados, e o casador de padrão sinalizou código real de
   biblioteca como segredo vazado (`token: "..."` nos esquemas de cor do
   pygments, `api_key: str = "..."` na anotação de tipo do próprio
   `anthropic`). Todo run de CI limpo falhava nesse ponto; só passava
   localmente por acaso, porque máquinas de desenvolvimento rodam esse
   script de verificação de release com muito menos frequência do que
   rodam `pytest`. Corrigido excluindo diretórios de vendor/build/cache
   conhecidos antes de recursar.

3. **gitleaks escaneando histórico completo, não só o push atual.** Ao
   corrigir o item 2, os testes de regressão adicionados continham
   strings no formato `nome = "valor"` como fixture literal no próprio
   código-fonte do teste — e o gitleaks (que varre `git log` inteiro a
   cada execução, por design) corretamente sinalizou isso como segredo
   commitado. Corrigido reescrevendo as fixtures pra montar a string em
   runtime (não como literal de linha única) e adicionando um allowlist
   (`.gitleaks.toml`) explicando por que aquele arquivo de teste é um
   falso positivo conhecido — sem reescrever histórico do git.

**O que isso prova**: que "a CI passa" não é uma alegação — é
`gh run list` mostrando `success` nos 5 workflows do commit `6568212`,
e cada correção acima só existe porque o pipeline foi exercitado de
verdade, não simulado ou revisado só por leitura de código.

**O que isso não prova**: que não existem mais bugs escondidos atrás de
caminhos ainda não exercitados (ex.: um segundo push que dispare
`workflow_dispatch` ou o cron semanal do scanner de segurança nunca foi
observado nesta sessão).
