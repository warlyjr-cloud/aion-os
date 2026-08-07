# Verified Evolution Registry

## Escopo futuro

Catálogo de skills, capabilities, mutações, provas e compatibilidade. Não haverá federação/rede no MVP.

## Manifesto de entrada

ID/version, tipo, autores, licença, source digest, artefatos, SBOM, dependências, hardware/ambiente, schemas, capabilities requeridas, política de rede, métricas, regressões conhecidas, proof references, assinaturas e revogações.

## Ingestão local

1. Tratar tudo externo como não confiável.
2. Verificar formato, license e digests/assinaturas quando disponíveis.
3. Reconstruir em ambiente limpo e sem segredos.
4. Reavaliar com políticas e benchmarks locais, incluindo reservados.
5. Colocar em quarentena até aprovação.
6. Registrar decisão, compatibilidade e eventual revogação.

Assinatura/proveniência prova origem/integridade, não qualidade ou segurança. Resultado de outra máquina não substitui política local.

## Ameaças

Typosquatting, maintainer compromise, dependency confusion, assinatura válida de artefato malicioso, benchmark overfitting, license incompatível, capability inflation, rollback trap e revogação indisponível.

## Roadmap

MVP: especificação e store local offline. Depois: in-toto/SLSA, Sigstore, TUF-style metadata, transparency log e mirrors. Federação só após threat model, governance, privacy e recovery independentes.
