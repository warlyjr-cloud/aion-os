# System Genome

## Definição

Manifesto versionado do estado evolutivo necessário para reconstruir uma geração: configuração Nix, packages/services, schemas, policies referenciadas, capabilities, skills, provider routing, memória validada, evaluator versions e lineage.

## Propriedades

- canonicalização e schema versionado;
- conteúdo endereçado por digest;
- referências imutáveis ou pinadas;
- ausência de secrets e dados pessoais;
- deltas legíveis e reversíveis;
- compatibilidade/migração explícita;
- vínculo com proof bundle e geração ancestral.

## Operações

`show` exibe resumo sanitizado; `export` produz manifesto sem credenciais; `diff` compara vetores e artefatos; `validate` verifica schema/referências; `restore` só cria plano de rollback aprovado. Nenhuma operação aplica o genome diretamente ao host.

## Rollback

Sistema, capabilities, memória, skills e routing devem voltar de forma coordenada. Geração parcial ou referência ausente é inválida. A integridade do manifesto não prova que seus artefatos são seguros; rebuild e avaliação continuam obrigatórios.

## MVP

JSON local e hashes podem representar o genome. Migração, assinatura, storage tamper-evident e reconstrução Nix multi-máquina são pendentes.
