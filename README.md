# AION OS

> Sistema Linux AI-native experimental que pretende comprovar, antes de aplicar, que cada mudança é segura e realmente melhor.

O AION combina a base declarativa do NixOS com um **Verifiable Evolution Kernel (VEK)**: objetivos viram contratos de intenção, candidatas são construídas e avaliadas em isolamento e somente evidências verificáveis podem autorizar promoção. O modelo propõe; uma base determinística de confiança decide. O VEK não substitui o kernel Linux.

## Estado do projeto

Este repositório é um **MVP de pesquisa, simulation-only por padrão**. Interfaces, schemas e fluxos mock podem existir sem equivaler a isolamento de produção, VM validada, execução privilegiada segura ou recursive self-improvement completo. Consulte [SOTA_GAP](docs/SOTA_GAP.md) e [HANDOFF_TO_CLAUDE](docs/HANDOFF_TO_CLAUDE.md) antes de interpretar resultados.

Não considere o AION pronto para produção, estado da arte ou seguro para mutar um host. Nenhuma instalação no host é necessária para a demonstração mock.

## Princípios

- **A inteligência pode evoluir; a autoridade não.**
- Toda ação é tipada, limitada por capability, auditável, temporária e reversível.
- O proponente nunca é seu único verificador.
- Guardrails eliminam candidatas antes de qualquer comparação de desempenho.
- O padrão é local-first, sem telemetria e sem shell livre no host.
- Mudanças críticas exigem revisão humana separada.

## Arquitetura resumida

```text
objetivo -> contrato -> candidatas -> política -> build/teste isolado
        -> avaliação independente -> prova -> aprovação -> promoção/rollback

LLM/provider (não confiável) -> VEK -> TCB determinístico -> executor tipado
```

Veja [ARCHITECTURE](docs/ARCHITECTURE.md), [VEK_SPECIFICATION](docs/VEK_SPECIFICATION.md), [TCB_SPECIFICATION](docs/TCB_SPECIFICATION.md) e [SAFETY_CONSTITUTION](docs/SAFETY_CONSTITUTION.md).

## Desenvolvimento local

Requisitos: Python 3.12 e, preferencialmente, `uv`. Não instale dependências globalmente.

```bash
uv venv
uv sync --extra dev
uv run aionctl --help
uv run pytest
uv run ruff check .
uv run pyright
```

Os comandos acima são os alvos esperados; consulte o handoff para saber quais foram realmente executados nesta geração. Para Nix, use apenas um ambiente Linux/WSL com Nix disponível e execute `nix flake check` antes de afirmar validação.

## Demonstração do MVP

O objetivo “processar, converter e reduzir vídeos” produz duas candidatas mock para uma capacidade baseada em FFmpeg, aplica política, compara uma fronteira multidimensional e gera um pacote de prova, sem instalar FFmpeg no host. A execução validada neste bootstrap gerou `proofs/mut-183c4b75e3bb/`, promoveu uma geração simulada e concluiu em rollback. A promoção real permanece bloqueada até validação isolada e aprovação humana separada.

## Documentação

- [Visão](docs/VISION.md) e [posicionamento](docs/PRODUCT_POSITIONING.md)
- [Modelo de ameaça](docs/THREAT_MODEL.md) e [privacidade](docs/DATA_AND_PRIVACY.md)
- [Agenda de pesquisa](docs/RESEARCH_AGENDA.md) e [trabalhos anteriores](docs/PRIOR_ART.md)
- [OS-EvoBench](docs/OS_EVOBENCH.md) e [modelo de RSI](docs/RSI_MODEL.md)
- [Roadmap](docs/ROADMAP.md) e [handoff](docs/HANDOFF_TO_CLAUDE.md)

## Contribuição e segurança

Leia [CONTRIBUTING.md](CONTRIBUTING.md) antes de propor mudanças. Vulnerabilidades devem seguir [SECURITY.md](SECURITY.md), nunca issues públicas. O projeto adota o [Contributor Covenant](CODE_OF_CONDUCT.md).

## Licença

O projeto e o metadata do pacote declaram Apache-2.0; consulte `LICENSE`. Dependências, ferramentas e artefatos externos mantêm suas próprias licenças.
