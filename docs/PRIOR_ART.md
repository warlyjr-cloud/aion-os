# Trabalhos anteriores e adjacentes

Pesquisa atualizada em **2026-08-02**, priorizando papers, documentação e repositórios oficiais. Os termos “AI OS” e “AgentOS” são sobrecarregados; sem identidade/URL inequívoca, este documento não presume que projetos homônimos sejam o alvo do prompt. Licenças devem ser reconfirmadas no commit exato antes de reutilizar código.

## Sistemas e agentes

| Trabalho | O que existe / reutilizar | Lacuna em relação ao AION | Licença/risco |
|---|---|---|---|
| [NixOS manual](https://nixos.org/manual/nixos/stable/) | configuração declarativa, generations, rollback e VM tests | não interpreta objetivos nem prova melhoria de agentes | Nixpkgs é MIT; módulos/artefatos específicos devem ser verificados |
| [AIOS paper](https://arxiv.org/abs/2403.16971) / [repo](https://github.com/agiresearch/AIOS) | kernel lógico para scheduling, context, memory, storage, tools e access control | foco em servir agentes; não demonstra proof-carrying OS evolution multi-geração | repo declara Apache-2.0; execução de tools/providers amplia superfície |
| [LSFS paper](https://arxiv.org/abs/2410.11843) / [repo](https://github.com/agiresearch/AIOS-LSFS) | interface semântica, indexação e rollback de arquivos | sem fronteira completa TCB/VEK ou evolução comprovada do sistema | confirmar licença/commit antes de copiar; risco de prompt/data confusion |
| [LUMOS](https://arxiv.org/abs/2311.05657) | planner/grounding/execution modulares e treinamento de agentes abertos | framework de agente, não promoção declarativa de gerações do OS | paper; código/licença precisam de verificação por artefato |
| [LUMOS semantic OS layer](https://arxiv.org/abs/2606.30697) | blueprints semânticos de UI/accessibility e ações visíveis restritas | reduz ambiguidade de computer use, mas não é um VEK nem prova evolução | paper recente; reproduzir resultados e confirmar código/licença |
| [OpenDAN](https://github.com/fiatrete/OpenDAN-Personal-AI-OS) | personal AI OS, integração de módulos e agentes | orientação a assistente pessoal, não prova/rollback governado | revisar licença, dependências, rede e permissões no commit escolhido |
| [ClaudeOS](https://www.claudeos.com/) | plataforma de agente e integrações; nome também usado por outros repos | identidade ambígua e foco diferente de evolução verificável | não reutilizar até fixar projeto, origem, licença e threat model |
| AgentOS | múltiplos projetos e papers homônimos; exemplos incluem [paper AgentOS](https://arxiv.org/abs/2603.08938) | termo não identifica uma baseline única | selecionar implementação/versionamento antes de comparar |
| “W3C OS” | nenhuma fonte primária inequívoca foi localizada com esse nome | item permanece não identificado | não atribuir ao W3C sem URL/identidade confirmada |

## Autoaperfeiçoamento e evolução de skills

| Trabalho | Contribuição | Uso no AION / risco |
|---|---|---|
| [Gödel Agent](https://arxiv.org/abs/2410.04444) | agente auto-referencial que modifica sua lógica | baseline RSI; precisa de autoridade externa e tarefas ocultas |
| [Darwin Gödel Machine](https://arxiv.org/abs/2505.22954) | arquivo populacional e validação empírica de agentes de código | inspira archive/lineage/novelty; benchmark success não prova segurança do host |
| [Hyperagents](https://arxiv.org/abs/2603.19461) / [repo](https://github.com/facebookresearch/hyperagents) | meta-agente editável junto do task agent | baseline RSI-3.5; o próprio repo alerta sobre código gerado não confiável; confirmar licença do commit |
| [EvoSkills](https://arxiv.org/abs/2604.01687) | geração de skills com verificador coevolutivo | inspira lifecycle; coevolução pode correlacionar falhas e não substitui oracle externo |
| [MUSE-Autoskill](https://arxiv.org/abs/2605.27366) | criação, memória, avaliação e refinamento de skills | inspira registry/memory; resultados recentes exigem reprodução independente |

## Segurança de agentes e memória

| Fonte primária | Achado relevante | Requisito derivado |
|---|---|---|
| [AgentPoison](https://arxiv.org/abs/2407.12784) | poisoning de memória/knowledge base pode criar backdoors | origem, quarentena, corroboração, retrieval policy e teste longitudinal |
| [MINJA](https://arxiv.org/abs/2503.03704) | ataque prático de memory injection por interação | write capability e promoção não podem depender só do agente |
| [BIPIA](https://arxiv.org/abs/2312.14197) | benchmark de indirect prompt injection | separar instrução de conteúdo e manter egress/authority fora do LLM |
| [Specification gaming — DeepMind](https://deepmind.google/blog/specification-gaming-the-flip-side-of-ai-ingenuity/) | objetivo literal pode divergir da intenção | contrato prévio, guardrails e métricas não controladas pela candidata |
| [Reward tampering — Anthropic](https://www.anthropic.com/research/reward-tampering) | modelos podem generalizar de gaming para adulteração do reward | avaliador/benchmark read-only e verificação independente |

## Isolamento, política e proveniência

| Tecnologia | O que reutilizar | Limites e licença |
|---|---|---|
| [Firecracker](https://firecracker-microvm.github.io/) / [repo](https://github.com/firecracker-microvm/firecracker) | microVM KVM, device model mínimo e jailer | Linux/KVM, hardening operacional; Apache-2.0 |
| [Wasmtime security](https://docs.wasmtime.dev/security.html) / [repo](https://github.com/bytecodealliance/wasmtime) | Wasm/WASI capability sandbox e resource controls | embedder continua responsável; Apache-2.0 com termos do projeto/terceiros |
| [OPA](https://www.openpolicyagent.org/docs) / [repo](https://github.com/open-policy-agent/opa) | policy decision separada de enforcement, Rego/Conftest | adaptador futuro; OPA não é executor nem prova; Apache-2.0 |
| [SLSA 1.2](https://slsa.dev/spec/v1.2/) | níveis e provenance de build/source | integridade da supply chain não prova correção; spec Apache-2.0 conforme repositório |
| [in-toto 1.0](https://in-toto.io/docs/specs/) | layouts/attestations de etapas da supply chain | exige gestão de chaves/identidades; Apache-2.0 |
| [Sigstore/Cosign](https://docs.sigstore.dev/cosign/signing/overview/) | identidade, assinatura e transparency log | assinatura válida não torna artefato benigno; Apache-2.0 nos componentes principais |
| [Object-capability model](https://arxiv.org/abs/1907.07154) | autoridade explícita e delegação controlada | adaptar a recursos/tempo/rede; não confundir com nomes de permissões ACL |

## Síntese

Os blocos necessários já existem separadamente: NixOS ilustra o conceito de estado declarativo/reversão (sem que o AION dependa de Nix ou nixpkgs); agent OSes para orquestração; DGM/Hyperagents para evolução; Wasmtime/Firecracker para isolamento; OPA para policy; SLSA/in-toto/Sigstore para proveniência; literatura adversarial para ataques. A hipótese diferenciadora do AION é integrar esses princípios em um gate de promoção multi-geração, com TCB fora do espaço evolutivo e evidência antes da autoridade. Isso ainda precisa ser demonstrado.

## Regras de reutilização

Fixar versão/commit; ler licença e NOTICE; inventariar dependências, hooks, MCPs, egress e credenciais; preferir interface ou formato a copiar código; registrar decisões em `tools/`; reconstruir e reavaliar localmente; não incorporar código com licença incompatível ou origem ambígua.
