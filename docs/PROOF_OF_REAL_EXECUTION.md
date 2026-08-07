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
