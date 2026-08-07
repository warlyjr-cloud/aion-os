# Roadmap

## P0 — fundação do MVP

- [x] schemas e contratos estabilizados;
- [x] TCB/policy/state machine com testes independentes;
- [x] actions/capabilities/MockProvider/audit/proof integrados;
- [x] tool/plugin inventory e configuração Claude revisados;
- [x] status real reconciliado no handoff.

## P1 — fluxo ponta a ponta

- [x] objetivo FFmpeg sem mutação do host;
- [x] duas candidatas, comparação Pareto e prova;
- [x] aprovação/rejeição, generation/lineage e rollback mock;
- [x] CLI/daemon exercitados com evidência.

## P2 — avaliação

- [x] cinco tarefas EvoBench reproduzíveis;
- [x] reward hacking, report forgery e hidden-test access;
- [x] memory poisoning e prompt injection;
- [x] baselines, seeds e relatório versionado.

## P3 — Lab de build/rollback

- [ ] módulo de configuração e serviço systemd nativos do AION;
- [ ] verificação de build própria do AION, VM build, boot e rollback executados;
- [ ] isolamento/egress e artifact capture validados.

## P4 — pesquisa avançada

- [ ] população/novelty/ablation longitudinal;
- [ ] Immune Memory e Council com independência real;
- [ ] shadow/canary e fault injection;
- [ ] registry local, Wasmtime/Firecracker e attestations.

## Gates

Nenhuma fase avança só por scaffolding. Cada item requer artefato, comando/ambiente, resultado, limitações e revisor. RSI-3+, federação e promoção autônoma real continuam fora do MVP.
