# Digital Twin e Shadow Evolution

## Propósito

Reduzir risco comparando a candidata com o estado atual sob carga representativa antes de canário/promoção. Um clone nunca é presumido fiel: drift e dados incompletos são ameaças à validade.

## Fluxo pretendido

1. Capturar genome, versões e estado necessário.
2. Criar clone sem segredos reais e com dados anonimizados/sintéticos.
3. Reproduzir carga versionada.
4. Aplicar candidata isolada.
5. Injetar falhas e observar invariantes.
6. Comparar baseline/candidata e produzir prova.
7. Se elegível e aprovado, operar canário limitado.
8. Promover ou reverter segundo health policy.

## Falhas

Disco cheio, pressão de memória/CPU, perda de rede, falha de serviço, reboot, corrupção simulada e dependência lenta. Cada cenário declara oracle, timeout, budget e cleanup.

## Privacidade e segurança

Não copiar credenciais, chaves ou dados pessoais desnecessários. Egress é deny-by-default; fixtures são sanitizadas; twin não compartilha filesystem gravável com host. Futuro eBPF/OpenTelemetry exige avaliação de privacidade.

## Estado do MVP

Interfaces e fixtures podem ser simuladas. VM NixOS, shadow de carga, chaos, canary e observabilidade real permanecem pendentes até comandos e relatórios correspondentes.
