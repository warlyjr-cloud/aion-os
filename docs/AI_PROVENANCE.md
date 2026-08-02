# Proveniência de IA

## Registro 2026-08-02 — bootstrap do MVP

- **Origem:** prompt mestre AION OS V4 fornecido pelo usuário.
- **Agentes:** Codex principal e subagentes especializados; este registro não identifica um modelo como autor/autorizador do TCB.
- **Escopo desta entrada:** documentação de arquitetura, pesquisa, segurança, governança e configuração Claude Code; código/runtime foi produzido em fluxos paralelos e deve ser reconciliado separadamente.
- **Ferramentas:** leitura local, busca web de fontes primárias, `apply_patch` e validações read-only.
- **Fontes externas:** listadas em `docs/PRIOR_ART.md`; nenhum código de terceiros foi copiado para os documentos.
- **Dados/segredos:** nenhum `.env` ou segredo foi lido ou solicitado.

## Mudanças documentais

Criados README, políticas comunitárias, CLAUDE.md, especificações do VEK/TCB/ações/capabilities, Constituição, modelos de evolução/memória/twin/council/registry/autonomia, threat/privacy/providers/genome/toolchain, agenda, prior art, roadmap e handoff. Hooks e agentes Claude usam configuração própria, não entram no runtime AION.

## Revisão necessária

`docs/SAFETY_CONSTITUTION.md` e `docs/TCB_SPECIFICATION.md` são protegidos e requerem revisão humana explícita. Fontes/licenças em `PRIOR_ART.md` precisam ser pinadas no commit efetivamente reutilizado. Alegações de teste pertencem ao handoff e só podem ser adicionadas após execução observada.

## Limitação

Proveniência textual não é attestation criptográfica. Ainda faltam digests de sessão/artefatos, identidade verificável, assinatura, SBOM e vínculo in-toto/SLSA.

## Validação da configuração Claude

O JSON de settings, a sintaxe dos cinco scripts e o frontmatter dos nove agentes foram analisados localmente. Sete casos sintéticos confirmaram negação de comando destrutivo, negação/alerta de escrita protegida, validação JSON, proveniência sanitizada e bloqueio de alegação de produção pronta. Também foram verificados 37 Markdown sem links locais quebrados. A política de execução do Windows inicialmente impediu `.ps1`; o exemplo passou a invocar os scripts versionados com `-ExecutionPolicy Bypass` no processo efêmero. Não houve teste de integração com o binário Claude Code.

## Registro integrado do MVP

- **Implementação:** agente principal implementou TCB, VEK, actions, capabilities, policy, audit, proofs, population, memory, provider mock, CLI, daemon e testes. Subagentes independentes produziram documentação/Claude Code, Nix/CI/supply chain e EvoBench/red team; o agente principal revisou e integrou.
- **Runtime:** Python 3.12.13 do runtime local Codex; `.venv` e cache `uv` restritos ao projeto.
- **Dependências:** pins diretos em `pyproject.toml` e resolução em `uv.lock`; nenhuma instalação global.
- **Validação:** Ruff e Pyright aprovados; 39 testes aprovados com 85,60% de cobertura; 18 schemas/instâncias validados; cinco tarefas EvoBench aprovadas no digital twin; prova FFmpeg verificada antes e depois de promotion/rollback simulados.
- **Artefatos:** prova `proofs/mut-183c4b75e3bb/`; geração simulada e audit log permanecem em `.aion-state/` local e não versionado.
- **Correção reproduzida:** a primeira execução em português tratou `vídeo` como objetivo genérico. A detecção passou a normalizar Unicode, ganhou teste de regressão e a nova prova confirma `package.propose:ffmpeg`. A prova incorreta foi preservada localmente e ignorada pelo Git.
- **GitHub:** `gh auth status` encontrou a conta pretendida, mas o token estava inválido; nenhum repositório remoto foi criado ou alterado e nenhum push ocorreu.
- **Nix/segurança:** Nix/VM/QEMU/Podman e scanners externos não foram executados por indisponibilidade local.
