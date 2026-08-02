# AION Immune Memory

## Registro

Cada memória contém ID, origem, proveniência, tipo, confiança, classificação de dados, contexto, evidência, escopo, expiração, geração, histórico, estado de quarentena, autoridade de ação e reversão.

Classes: conteúdo externo não confiável, observação, preferência, fato verificado, decisão aprovada, experiência candidata, experiência validada e regra de segurança. Regras de segurança vivem no TCB, não na memória evolutiva.

## Estados

```text
ingested_untrusted -> quarantined -> corroborated -> candidate
-> approved/validated -> expired/revoked/rolled_back
```

Conteúdo externo nunca ganha autoridade automaticamente. Confiança não é probabilidade de verdade e assinatura só identifica origem; promoção exige evidência independente e política.

## Controles

- separar conteúdo de instrução/autoridade;
- sanitizar e limitar tamanho antes de indexar;
- vincular writes a intent/capability/agente;
- retrieval respeita escopo, classificação, versão e quarantine;
- registrar leitores e uso em decisões;
- impedir memória de conceder capabilities;
- incluir memória em rollback e lineage;
- detectar contradição, repetição coordenada e sleeper triggers.

## Testes adversariais

Prompt injection persistente, fato forjado, authority laundering, tool hijacking, sobreposição de preferência, replay entre usuários, expiração ignorada, rollback incompleto e consenso Sybil. O MVP deve simular promoção/quarentena; não alegar imunidade sem avaliação adaptativa.
