---
name: iniciar
description: "Monta o kit mínimo dos ritos de documentação num projeto: .claude/ritos.json, CLAUDE.md, HANDOFF.md, SETUP.md, docs/historico.md e docs/pendencias.md. Use quando o diretor pedir para levar os ritos (ou o plugin ritos) para um projeto novo ou existente que ainda não tem esses arquivos."
---

# Iniciar os ritos num projeto

Os ritos em si estão na skill `ritos:ritos`. Esta skill só monta os arquivos.

## Passos

1. **Olhar antes de escrever.** Listar o que o projeto já tem (`CLAUDE.md`, `HANDOFF.md`, `SETUP.md`, `docs/`, `.claude/`, `git config --get core.hooksPath`). **Nunca sobrescrever** arquivo existente: se já existe, propor o que acrescentar.
2. **Perguntar só o que não dá para descobrir** (uma pergunta por vez, poucas): quem é o diretor (nome para "decisão do <nome>"), o que é o projeto em 2 linhas, e quais pastas são código (sugerir pelo que existe).
3. **Dizer em 2 a 4 frases o que vai criar** e esperar o "ok" do diretor (são mais de 3 arquivos).
4. Criar, a partir dos esqueletos abaixo:
   - `.claude/ritos.json` com `codigo` (as pastas de código) e, se o projeto tiver regras próprias de documentação, `ritos_projeto`;
   - `CLAUDE.md`, `HANDOFF.md`, `SETUP.md`, `docs/historico.md` (primeira linha: a data e "ritos iniciados"), `docs/pendencias.md`.
   - Pasta nova (`docs/arquivo/`, `docs/<parte>/`) só com o primeiro arquivo.
5. **Ligar e conferir as travas:** a trava de commit liga no próximo início de sessão. Dizer ao diretor para abrir uma sessão nova e conferir que o HANDOFF aparece no contexto e que `git config --get core.hooksPath` aponta para a pasta `githooks` do plugin. Se o projeto já usa outra ferramenta de hooks do git (husky, pre-commit), avisar que o plugin assume o `core.hooksPath` e chama os hooks dela depois da trava (o caminho anterior fica em `git config ritos.hooksPathAnterior`).
6. Relatar o que foi criado, o que foi e o que não foi verificado. Commit só quando o diretor pedir.

## Esqueletos

**`CLAUDE.md`:**
```
# <Projeto>
<o que é, tecnologia, fase atual em 2 linhas>
Contexto da sessão anterior: HANDOFF.md (o hook de início já o entrega). Ambiente: SETUP.md.

## Modo de trabalho
- <diretor> dirige (decide, aprova, testa); o Claude executa (código, testes, documentação).
- Seguimos os ritos do plugin `ritos` (skill ritos:ritos): cada pergunta tem um documento e cada fato mora num lugar só.
- Antes de mudar: 2–4 frases. Depois: verificar e dizer o que foi e o que não foi verificado.
- Perguntar só decisões que são do diretor. Datas absolutas (DD/MM/AAAA).
- Commit/push só quando o diretor pedir; nunca `--no-verify`.

## Regras do produto
## Organização de pastas
## Documentos
<lista com o papel de cada um>. Em conflito: <ordem de prioridade, ex.: produto no ar > HANDOFF > demais>.
```

**`HANDOFF.md`:**
```
# Handoff — estado atual
> Só o estado atual (DD/MM/AAAA). História: docs/historico.md. O que falta: docs/pendencias.md.
## Retomar aqui
<até 5 linhas por parte> / git (inclusive o que fica fora de propósito) / testes / sessões em andamento / avisos
## O produto hoje
## Decisões em aberto (do diretor)
## Regras de operação
## Decisões fechadas (não reabrir sem pedir)
## Documentos
```

**`SETUP.md`:**
```
# Setup — como o ambiente está montado
> Cada escolha técnica com o motivo e a data. Nome de segredo sim, valor nunca.
## Máquina e ferramentas
## Servidor e contas externas
## Escolhas técnicas
```

**`docs/historico.md`:**
```
# Histórico — por que está assim
> Só acrescenta no fim. Uma ou duas linhas por marco (modelo na skill ritos:ritos, seção 8).

- DD/MM/AAAA · Ritos de documentação iniciados (plugin ritos). Commit "<título>".
```

**`docs/pendencias.md`:**
```
# Pendências — tudo o que falta
> Revisada em DD/MM/AAAA. Só o que ainda não foi feito; o feito está no historico.md.
## 1. Curto prazo
## 2. Próximo passo
## 3. Por parte
## Ideias sem compromisso
## Decisões em aberto
## Dívidas técnicas
```
