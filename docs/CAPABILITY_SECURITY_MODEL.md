# Modelo de Segurança por Capabilities

## Definição

Uma capability é uma autorização explícita para uma operação sobre um recurso delimitado. Posse é necessária, nunca suficiente: constituição, política, estado, risco e aprovação continuam válidos.

Exemplos: `file.read:/workspace/video`, `package.propose:ffmpeg`, `service.restart:nginx`, `network.egress:api.anthropic.com`, `memory.write:operational`, `generation.build:aion-lab`.

## Claims mínimos

`capability_id`, emissor TCB, sujeito/agente, operação, recurso normalizado, ambiente, mutation/intent IDs, classificação de dados, quantidade, destino de rede, `not_before`, `expires_at`, usos restantes, risco, delegável=false, status e versão.

## Ciclo de vida

```text
requested -> policy_checked -> human_approved? -> issued -> consumed/expired/revoked
```

Capabilities não são ampliadas na renovação; novo escopo exige novo pedido. Revogação e emergency stop prevalecem sobre cache. Replay, sujeito divergente, ambiente divergente, validade expirada ou uso excedido são negados.

## Matching

- operação e recurso precisam ser iguais ou subconjuntos formais do grant;
- paths são canonicalizados e verificados contra symlinks;
- rede usa host/porta/protocolo explícitos, DNS revalidado e egress deny-by-default;
- nenhum `*` é emitido no MVP;
- uma capability nunca concede mudança no TCB/constituição.

## Auditoria e armazenamento

Registrar emissão, tentativa, decisão, consumo, revogação e motivo sem guardar segredos. Futuro: tokens autenticados/assinados e armazenamento resistente a adulteração; o MVP não deve confundir IDs/hash locais com credenciais criptograficamente fortes.

## Propriedades a testar

Ação sem capability nunca executa; capability expirada/revogada/reutilizada falha; escopo irmão/ancestral não é implícito; normalização não escapa; capability não é transferível; emergency stop invalida execução pendente.
