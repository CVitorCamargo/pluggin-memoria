# ritos

Plugin do Claude Code com os ritos de documentação para projetos em que **uma pessoa dirige** (decide, aprova, testa) e **um agente de IA executa** (código, testes, documentação). Nasceu no KingdomEmpire e no AtomicHub (outubro e novembro de 2026).

## O que vem no plugin

| Peça | O que faz |
|---|---|
| skill `ritos:ritos` | Os ritos em si: um documento por pergunta, fonte única, marcos e gatilhos, tamanho do HANDOFF, sessões em paralelo, aviso de risco de perda, modelos de commit e de histórico. |
| skill `ritos:iniciar` | Monta o kit mínimo num projeto: `.claude/ritos.json`, `CLAUDE.md`, `HANDOFF.md`, `SETUP.md`, `docs/historico.md`, `docs/pendencias.md`. |
| hook de início de sessão | Entrega o HANDOFF, o `git status` e os últimos commits; avisa arquivo sem commit; liga a trava de commit. |
| hook de fim de turno | Avisa os arquivos desta sessão sem commit e cobra, uma vez, histórico ou HANDOFF quando há código mudado. |
| trava de commit (git) | Recusa commit sem "Por quê:" e "Verificado:", ou com código sem a linha do histórico (ou `Sem histórico: <motivo>`). |

As travas **só agem em projeto que tem `.claude/ritos.json`**. Nas outras pastas o plugin não faz nada.

## Instalar

O repositório é a "loja" (marketplace) e o plugin ao mesmo tempo. Num projeto, para valer para quem abrir a pasta:

```
claude plugin marketplace add CVitorCamargo/pluggin-memoria --scope project
claude plugin install ritos@ritos --scope project
```

Depois, criar `.claude/ritos.json` (ou pedir ao Claude a skill `ritos:iniciar`) e abrir uma sessão nova.

## Configurar (`.claude/ritos.json`)

```json
{
  "codigo": ["projects/", "infra/"],
  "historico": "docs/historico.md",
  "handoff": "HANDOFF.md",
  "ritos_projeto": "docs/ritos-documentacao.md"
}
```

- `codigo`: pastas que contam como código. Vazio: tudo que não é `.md` fora de `docs/` e `.claude/`.
- `ritos_projeto`: o documento com o que é só deste projeto; aparece nas mensagens das travas.

## Requisitos e limites

- Python 3 no PATH como `python` e git.
- A trava de commit usa `core.hooksPath`. Se o projeto já usa outra ferramenta de hooks do git (husky, pre-commit), ela não liga e o início de sessão avisa.
- O fim de turno não vê arquivo mudado por comando no terminal; a trava confere que o documento mudou, não que o texto está certo. Erro interno deixa passar.
