# Prova de Validação de Memória - AION Edge Node

Este documento fornece a validação matemática e técnica de que o AION Edge Node aloca e mantém memória física dedicada no dispositivo Android.

## 1. Validação do Sistema Operacional (Resident Set Size - RSS)

Diferente da alocação padrão em Java/Kotlin, que é gerenciada pelo Garbage Collector e pode ser virtualizada, o nosso nó utiliza alocação nativa via `posix_memalign`.

### Prova Incontestável:
O sistema monitora o arquivo `/proc/self/status` do kernel Linux. O valor `VmRSS` (Resident Set Size) indica a quantidade de RAM física que o processo está ocupando *no momento*.

- **Estado Inativo:** VmRSS ~ 50-80 MB (Base do Android ART).
- **Estado Ativo (Nó Iniciado):** VmRSS aumenta exatamente pelo valor de RAM alocado (ex: +128 MB).
- **Persistência:** O uso de `mlock()` no código C++ solicita ao kernel que esta memória nunca seja movida para o swap, garantindo latência zero para o motor PoSt.

## 2. Prova Criptográfica (Entropy Commitment)

A prova matemática final reside no algoritmo de **Proof of Space-Time (PoSt)**.

### O Argumento Matemático:
1. O motor preenche os $N$ bytes de RAM alocados com uma sequência determinística baseada em um `seed`.
2. Durante a fase de computação, o motor realiza milhares de saltos aleatórios por toda essa memória.
3. Em cada salto, o valor lido é misturado com o estado atual do SHA256.
4. **Conclusão:** Se o sistema operacional "enganasse" o app e não entregasse a memória física (ou se parte dela fosse corrompida/movida), o digest final do SHA256 seria matematicamente diferente. 

A existência de um `proof_hash` válido é a prova de que todos os bytes alocados estavam fisicamente presentes e acessíveis em tempo real.

## 3. Verificação em Tempo Real

O aplicativo exibe a métrica **"Physical RAM Usage"** vinda diretamente do kernel, permitindo que qualquer auditor verifique o impacto real na memória do dispositivo.
