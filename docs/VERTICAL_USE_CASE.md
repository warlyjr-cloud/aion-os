# Caso de uso vertical: gestão autônoma e segura de dependências

Este documento propõe **um** caso de uso fechado para o AION, composto
inteiramente de capacidades que já existem e foram provadas reais nesta
sessão (ver `docs/PROOF_OF_REAL_EXECUTION.md`). Não é uma nova feature —
é uma escolha de foco sobre o que já existe, para dar ao produto uma
narrativa vendável e testável, em vez de "evolução autônoma de qualquer
configuração de sistema".

**Esta é uma proposta, não uma decisão tomada.** Cortar ou não as outras
frentes do projeto (kernel Rust, cliente Android, grid P2P etc.) continua
sendo decisão sua — ver `docs/PROJECT_STATUS.md` para o que é real vs.
visão em cada uma delas.

## O problema

Times de plataforma/SRE gastam tempo real decidindo se e quando atualizar
uma dependência (`ffmpeg`, uma lib do sistema, um pacote de segurança):
o update pode trazer CVE corrigida, mas também pode quebrar algo. Hoje
isso é ou 100% manual (lento) ou 100% automático via Dependabot/Renovate
(rápido, mas sem julgamento — só abre PR, não avalia risco real).

## O que o AION já faz, hoje, de verdade, que resolve isso

1. **Propõe a mudança de forma declarativa e auditável** —
   `EvolutionEngine.plan()` gera candidatos com config Nix declarativa,
   nunca comando de shell livre (`src/vek/engine.py`).
2. **Barra a proposta em duas camadas independentes antes de qualquer
   execução** — `ModelCouncil` (revisão por LLM) **e**
   `DeterministicVerifier` (scan determinístico, sem LLM, não pode falhar
   aberto) — provado com 24 testes reais, `src/model_council/`.
3. **Só executa de verdade depois de aprovação humana explícita** —
   `approve()` seguido de `promote()`; nunca antes — provado com um ciclo
   real de `nix build` de 4 minutos, resultado físico no Nix store
   (`docs/PROOF_OF_REAL_EXECUTION.md`).
4. **Reverte de verdade se algo dá errado** — `rollback()` provado
   revertendo uma geração real.
5. **Escopo por time/objetivo, com expiração e revogação reais** —
   `aionctl grants issue/revoke/list`, provado nesta sessão.
6. **Trilha de auditoria consultável, não só "log"** —
   `GET /api/mutations/{id}` no dashboard mostra exatamente por que uma
   mudança foi aceita ou rejeitada, e quem aprovou.

## Fluxo do produto (usando comandos reais, já existentes)

```bash
# 1. Uma equipe de segurança emite ao AION o direito de propor
#    atualizações de pacote para o time de vídeo, por 24h.
aionctl grants issue "package.propose:ffmpeg" "team-video" "obj-patch-2026-08" \
  --ttl-minutes 1440 --max-uses 10

# 2. O AION propõe a atualização (nunca executa nada ainda).
aionctl plan "atualizar ffmpeg para corrigir CVE-2026-XXXXX"

# 3. Duas camadas de revisão automática já rodaram dentro do plan() acima
#    (ModelCouncil + DeterministicVerifier) — se qualquer uma reprovar,
#    a mutação já está arquivada antes de chegar aqui.

# 4. Um humano revisa a prova completa antes de aprovar.
curl http://localhost:8000/api/mutations/<mutation_id>

# 5. Aprovação explícita e execução real.
aionctl mutations approve <mutation_id> --actor "sre-oncall"
aionctl mutations promote <mutation_id>

# 6. Se algo quebrar em produção, reversão real.
aionctl mutations rollback <mutation_id>
```

## Por que isso é vendável como está, sem esperar mais engenharia

Todo passo acima já rodou de verdade nesta sessão — não é roteiro
aspiracional. O que falta para um piloto real com um cliente:

1. Trocar `ffmpeg`/Nix pelo gerenciador de pacote do cliente (apt, npm,
   pip — o padrão de `DeterministicVerifier` e o fluxo de aprovação são
   agnósticos ao gerenciador; só `SafeExecutor._SAFE_TARGET_PATTERN` e o
   comando real em `safe.py` precisam de um adaptador por ecossistema).
2. Rodar em ambiente do cliente (hoje provado em WSL2 + Nix local; produção
   real precisa de isolamento adicional — ver limitações em
   `docs/PROOF_OF_REAL_EXECUTION.md`).
3. Nada de kernel Rust, Android, ou criptografia pós-quântica é necessário
   para este piloto — o valor inteiro está no que já roda em Python hoje.
