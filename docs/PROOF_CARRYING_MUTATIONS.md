# Proof-Carrying Mutations

## Princípio

Uma mutação só avança acompanhada de evidência suficiente para reproduzir o que foi proposto, executado e decidido. “Proof” aqui é um pacote de evidência verificável; não é prova formal de correção.

## Estrutura canônica

```text
proofs/<mutation-id>/
  manifest.json              intent-contract.json
  hypothesis.md              baseline.json
  candidate.json             policy-report.json
  build-report.json          test-report.json
  security-report.json       benchmark-report.json
  adversarial-report.json    comparison.json
  provenance.json            rollback-plan.json
  post-promotion-report.json summary.md
  checksums.txt               artifacts/
```

## Manifesto

Registra schema, mutation/generation/parent IDs, arquivos e digests, proponente, modelos, ferramentas/versões, ambiente, capabilities, budgets, timestamps, etapas executadas/não executadas, warnings, decisão e verificadores. Caminhos são relativos e normalizados.

## Verificação mínima

1. Schema e conjunto de arquivos esperados.
2. Checksums recalculados em ordem determinística.
3. Vínculo entre intent, baseline, candidata, reports e decisão.
4. Identidades separadas para proponente e verificador.
5. `execution_mode` explícito em cada relatório.
6. Nenhuma etapa obrigatória ausente ou marcada sucesso sem resultado.
7. Rollback aponta para geração válida.

Checksums detectam alteração acidental/intencional após captura, mas não provam que o produtor disse a verdade. Futuro: in-toto/SLSA predicates, Sigstore/Cosign, SBOM, TUF e âncoras de hardware. Não criar criptografia própria.
