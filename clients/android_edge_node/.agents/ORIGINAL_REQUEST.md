# Original User Request

## Initial Request — 2026-08-05T13:17:58-03:00

Criar um aplicativo Android (Edge Node) para a rede AION OS que utiliza C++ nativo (JNI/NDK) para gerar Provas de Espaço-Tempo (PoST). O app atuará como um nó de infraestrutura descentralizada, provando fisicamente sua dedicação de hardware matemático.

Working directory: `C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node`
Integrity mode: development

## Requirements

### R1. Cálculo de PoST Robusto em C++ (Bare-Metal/NDK)
A equipe deve implementar uma função nativa em C++ que aloque memória física no dispositivo e execute um loop matemático criptográfico para validar o esforço real do hardware, expondo o resultado via JNI para o Android.

### R2. Design e Arquitetura do App
A equipe tem autonomia total para decidir a arquitetura visual e estrutural do aplicativo (Interface ou Headless Daemon).

### R3. Utilização de Ferramentas Nativas
A criação do projeto Android e o gerenciamento de builds/testes devem ser executados com ferramentas padrão de linha de comando ou pela skill `android-cli`.

## Acceptance Criteria

### Verificação Matemática e de Interoperabilidade
- [ ] A equipe provou a corretude do código através de testes unitários automatizados (JUnit/Espresso) que chamam a função JNI (C++) nativamente, atestando que os cálculos retornam o Hash criptográfico correto.
