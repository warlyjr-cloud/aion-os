# Roadmap

## P0 — fundação do MVP

- [ ] schemas e contratos estabilizados;
- [ ] TCB/policy/state machine com testes independentes;
- [ ] actions/capabilities/MockProvider/audit/proof integrados;
- [ ] tool/plugin inventory e configuração Claude revisados;
- [ ] status real reconciliado no handoff.

## P1 — fluxo ponta a ponta

- [ ] objetivo FFmpeg sem mutação do host;
- [ ] duas candidatas, comparação Pareto e prova;
- [ ] aprovação/rejeição, generation/lineage e rollback mock;
- [ ] CLI/daemon exercitados com evidência.

## P2 — avaliação

- [ ] cinco tarefas EvoBench reproduzíveis;
- [ ] reward hacking, report forgery e hidden-test access;
- [ ] memory poisoning e prompt injection;
- [ ] baselines, seeds e relatório versionado.

## P3 — NixOS Lab

- [ ] módulo NixOS e serviço systemd;
- [ ] `nix flake check`, VM build, boot e rollback executados;
- [ ] isolamento/egress e artifact capture validados.

## P4 — pesquisa avançada

- [ ] população/novelty/ablation longitudinal;
- [ ] Immune Memory e Council com independência real;
- [ ] shadow/canary e fault injection;
- [ ] registry local, Wasmtime/Firecracker e attestations.

## Gates

Nenhuma fase avança só por scaffolding. Cada item requer artefato, comando/ambiente, resultado, limitações e revisor. RSI-3+, federação e promoção autônoma real continuam fora do MVP.
