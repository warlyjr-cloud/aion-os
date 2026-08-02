# Posicionamento do produto

## Frase central

**AION é o Linux autoevolutivo que comprova, antes de aplicar, que cada mudança é segura e realmente melhor.**

## Para quem

Desenvolvedores, pesquisadores de agentes/RSI, profissionais de DevOps, laboratórios de IA e equipes de infraestrutura que precisam de automação auditável. O público geral não é foco inicial.

## Trabalho a realizar

“Dado um objetivo operacional, quero receber uma mudança declarativa candidata, evidência comparativa e um caminho de rollback, sem conceder autoridade irrestrita ao modelo.”

## Formas de distribuição

1. **Evolution Engine:** módulo instalável em NixOS existente; primeira adoção.
2. **AION Lab:** VM para desenvolvimento, benchmark, homologação e red team.
3. **AION OS:** distribuição completa futura, sem kernel próprio no MVP.

## Promessa responsável

O usuário informa o objetivo; o AION produz candidatas, testa em isolamento, expõe evidências e solicita a decisão apropriada. Não promete autonomia irrestrita, segurança absoluta, SOTA ou RSI completo. Hoje, o repositório deve ser tratado como MVP experimental e simulation-only.

## Não é

- chatbot empacotado como distribuição;
- agente com shell root;
- framework multiagente genérico;
- substituto do NixOS;
- licença para aplicar patches gerados por IA sem revisão.
