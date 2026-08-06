# Plano de Implementação: AION Edge Node - Fase de Produção

Este plano detalha a transformação do app de uma Prova de Conceito (PoC) para um nó de borda funcional da rede AION, focando em P2P, persistência de dados, wallet e gestão de energia.

## Propostas de Mudança

### 1. Comunicação de Rede (P2P)
Implementação de uma camada de comunicação para descoberta de peers e recebimento de "challenges" da rede AION.
- [NEW] `NetworkManager.kt`: Gerencia conexões via gRPC/WebSocket (simulado para P2P inicial).
- [MODIFY] `PoStDaemonService.kt`: Integração com o NetworkManager para receber tarefas automaticamente.

### 2. Persistência de Dados (Shard Storage)
Sistema para armazenar e recuperar "shards" (pedaços) de dados que o nó se compromete a guardar.
- [NEW] `ShardStorage.kt`: Gerencia a leitura/escrita de arquivos na pasta de dados do app.
- [MODIFY] `post_engine.cpp`: Atualização do motor para validar dados de um buffer/arquivo real em vez de apenas um seed aleatório.

### 3. Sistema de Recompensas (Wallet & Identity)
Criação de uma identidade criptográfica para o nó.
- [NEW] `WalletManager.kt`: Usa o Android Keystore para gerar e armazenar com segurança um par de chaves Ed25519.
- [MODIFY] `MainActivity.kt`: Exibição do endereço da Wallet (AION ID) e saldo (simulado).

### 4. Otimização de Recursos (Power Policy)
Garantir que o nó seja um "bom cidadão" no dispositivo do usuário.
- [NEW] `PowerPolicyManager.kt`: Monitora estado da bateria, carregamento e conexão Wi-Fi.
- [MODIFY] `PoStDaemonService.kt`: Automação de pausa/retomada baseada nas políticas de energia.

---

## Detalhes Técnicos por Componente

### [Componente Nativo]
#### [MODIFY] [post_engine.cpp](file:///C:/Users/GABRIELA APSOL/.gemini/antigravity/scratch/aion-os/clients/android_edge_node/app/src/main/cpp/post_engine.cpp)
- Adicionar suporte para processar um `data_buffer` em vez de gerar dados aleatórios.
#### [MODIFY] [jni_bridge.cpp](file:///C:/Users/GABRIELA APSOL/.gemini/antigravity/scratch/aion-os/clients/android_edge_node/app/src/main/cpp/jni_bridge.cpp)
- Expor nova função `nativeComputePoStWithData` que recebe o buffer do shard.

### [Componente de Serviço]
#### [NEW] [NetworkManager.kt](file:///C:/Users/GABRIELA APSOL/.gemini/antigravity/scratch/aion-os/clients/android_edge_node/app/src/main/java/com/aionos/edgenode/network/NetworkManager.kt)
#### [NEW] [ShardStorage.kt](file:///C:/Users/GABRIELA APSOL/.gemini/antigravity/scratch/aion-os/clients/android_edge_node/app/src/main/java/com/aionos/edgenode/storage/ShardStorage.kt)
#### [NEW] [WalletManager.kt](file:///C:/Users/GABRIELA APSOL/.gemini/antigravity/scratch/aion-os/clients/android_edge_node/app/src/main/java/com/aionos/edgenode/identity/WalletManager.kt)
#### [NEW] [PowerPolicyManager.kt](file:///C:/Users/GABRIELA APSOL/.gemini/antigravity/scratch/aion-os/clients/android_edge_node/app/src/main/java/com/aionos/edgenode/policy/PowerPolicyManager.kt)

### [Interface]
#### [MODIFY] [MainActivity.kt](file:///C:/Users/GABRIELA APSOL/.gemini/antigravity/scratch/aion-os/clients/android_edge_node/app/src/main/java/com/aionos/edgenode/ui/MainActivity.kt)
- Adicionar cards para "Wallet" e "Network Status".
- Toggle para "Auto-mode" (baseado na Power Policy).

---

## Plano de Verificação

### Testes Automatizados
- Unit tests para `WalletManager` (verificar persistência de chaves).
- Unit tests para `ShardStorage` (integridade de leitura/escrita).

### Verificação Manual
- Desconectar o carregador e observar o nó entrando em pausa automática.
- Simular recebimento de um shard via NetworkManager e verificar se a prova (PoSt) gerada é válida para aquele dado.
