# AION Edge Node (v1.0) - PoST Infrastructure for Android

![Build Status](https://img.shields.io/badge/Android-Native_C++-green?style=for-the-badge&logo=android)
![Project Phase](https://img.shields.io/badge/Phase-MVP_Functional-blue?style=for-the-badge)

O **AION Edge Node** é um nó de borda descentralizado de alta performance que transforma dispositivos Android em unidades de computação e armazenamento para a rede **AION OS**. Ele utiliza o protocolo **Proof of Space-Time (PoSt)** para validar recursos de hardware de forma soberana e incontestável.

## 🚀 Diferenciais Estratégicos (Visão para Investidores)

Este projeto resolve o problema da centralização de nuvem ao mover a infraestrutura para a borda (edge). Diferente de apps comuns, o AION Edge Node opera em nível de sistema:

- **Performance Bare-Metal:** Motor criptográfico escrito em C++ com otimizações manuais de memória, superando implementações em linguagens de alto nível.
- **Hardware Commitment:** O nó "sequestra" e trava RAM física (`mlock`) para garantir latência zero e provas de armazenamento reais.
- **Eficiência Energética:** Sistema de políticas inteligentes que automatiza o trabalho baseado no estado da bateria e conexão Wi-Fi.
- **Identidade Criptográfica:** Integração total com o Android Keystore para identidades digitais seguras e imutáveis.

## 🛠 Arquitetura Técnica

O app foi construído com uma separação rigorosa de responsabilidades:

- **`PoStBareMetalEngine` (C++):** Core engine que realiza o hashing SHA-256 e a mutação de células de memória em tempo real.
- **`JNI Bridge`:** Camada de baixa latência que expõe telemetria do Kernel Linux (como VmRSS) para o Android.
- **`PoStDaemonService`:** Serviço em foreground que mantém o nó ativo 24/7, mesmo com a tela desligada.
- **`Wallet & Network`:** Gerenciamento de chaves Ed25519 e simulação de descoberta de peers P2P.

## 📐 Validação Matemática

A segurança do sistema é baseada na dificuldade computacional de forjar um Proof of Space-Time sem possuir a memória física alocada. Veja os detalhes em:
👉 **[Documento de Prova de Memória (MEMORY_PROOF.md)](./MEMORY_PROOF.md)**

## 📈 Roadmap

1.  **V1.0 (Atual):** MVP com Motor Nativo, JNI Bridge, Daemon Service e Gestão de Energia.
2.  **V1.5 (Próximo):** Integração real de rede via `libp2p` e persistência de shards criptografados.
3.  **V2.0:** Wallet nativa com suporte a tokens AION e sistema de reputação on-chain.

## 📝 Licença

Este software faz parte do ecossistema AION OS. Consulte os termos de licenciamento no repositório principal.

---
*Developed by Codex - Built for the future of decentralized infrastructure.*
