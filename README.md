# ritos

Plugin do Claude Code com os ritos de documentação para projetos em que **uma pessoa dirige** (decide, aprova, testa) e **um agente de IA executa** (código, testes, documentação). Nasceu no KingdomEmpire e no AtomicHub (outubro e novembro de 2026).

## O que vem no plugin

| Peça | O que faz |
|---|---|
| skill `ritos:ritos` | Os ritos em si: um documento por pergunta, fonte única, marcos e gatilhos, tamanho do HANDOFF, sessões em paralelo, aviso de risco de perda, modelos de commit e de histórico. |
| skill `ritos:iniciar` | Monta o kit mínimo num projeto: `.claude/ritos.json`, `CLAUDE.md`, `HANDOFF.md`, `SETUP.md`, `docs/historico.md`, `docs/pendencias.md`. |
| hook de início de sessão | Entrega o HANDOFF (até 80 linhas; acima disso corta e avisa), o `git status` e os últimos commits; avisa arquivo sem commit; liga a trava de commit sem desligar os hooks que o projeto já tinha. |
| hook antes do resumo | Pede ao resumo da conversa uma seção "Ainda só na conversa" com o que ainda não foi escrito. |
| hook de fim de turno | Avisa os arquivos desta sessão sem commit (inclusive mudados pelo terminal) e cobra, uma vez, histórico ou HANDOFF quando há código mudado; lembra, uma vez por sessão, de registrar decisão tomada só no chat. |
| trava de commit (git) | Recusa commit sem "Por quê:" e "Verificado:", com código sem a linha do histórico (ou `Sem histórico: <motivo>`), ou com o histórico mudado fora do fim (ou `Histórico editado: <motivo>`). |

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
  "pendencias": "docs/pendencias.md",
  "ritos_projeto": "docs/ritos-documentacao.md",
  "handoff_max_linhas": 80,
  "lembrar_decisoes": true
}
```

- `codigo`: pastas que contam como código. Vazio: tudo que não é `.md` fora de `docs/` e `.claude/`.
- `ritos_projeto`: o documento com o que é só deste projeto; aparece nas mensagens das travas.
- `handoff_max_linhas`: quantas linhas do HANDOFF entram no contexto a cada sessão (é o principal custo fixo em tokens). `0` desliga o teto.
- `lembrar_decisoes`: `false` desliga o lembrete de decisão tomada só no chat.

## Custo em tokens

Só o início de sessão põe texto fixo no contexto: o HANDOFF (com teto), até 30 linhas de `git status` e 5 commits, uns 2 a 4 mil tokens com o HANDOFF em 80 linhas. O fim de turno só fala quando cobra, no máximo uma vez por conjunto de arquivos e uma vez por sessão para decisão. A trava de commit roda no git, fora da conversa.

## Requisitos e limites

- Python 3 no PATH (`python3`, `python` ou `py`) e git. Sem Python, as travas avisam e deixam passar.
- A trava de commit assume o `core.hooksPath` e chama, depois dela, os hooks que já existiam (`.git/hooks`, husky, `.githooks`); o caminho anterior fica em `git config ritos.hooksPathAnterior`.
- Antes de desinstalar: `sh <pasta do plugin>/scripts/rodar.sh desligar` em cada projeto, para devolver o `core.hooksPath`, e apagar o `.claude/ritos.json`.
- A trava confere que o documento mudou, não que o texto está certo; o lembrete de decisão é por palavra, não por sentido; arquivo mudado por outra sessão ao mesmo tempo também conta como "desta sessão". Erro interno deixa passar.
