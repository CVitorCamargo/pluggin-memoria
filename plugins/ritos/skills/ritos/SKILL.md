---
name: ritos
description: "Ritos de documentação para projetos em que uma pessoa (o diretor) decide, aprova e testa e um agente de IA executa. Use ao fechar um marco (publicou, terminou etapa, decisão do diretor, erro, fim de sessão ou resumo da conversa), ao atualizar HANDOFF, histórico, pendências ou SETUP, ao escrever um commit, ao registrar decisão ou erro, quando o diretor pedir para atualizar as documentações, ou quando uma trava dos ritos (hook de início, fim de turno ou commit) cobrar algo."
---

# Ritos de documentação

> Parte geral, que vale para qualquer projeto. O que é só de um projeto (pastas dos apps, sessões, conteúdo público, ordem de prioridade em conflito) fica no `ritos_projeto` apontado em `.claude/ritos.json` e no `CLAUDE.md` dele. Nasceu no KingdomEmpire (desde 03/10/2026) e no AtomicHub (31/10/2026, revisado em 04/11/2026 e 05/11/2026).

## A ideia em uma frase

Cada pergunta tem **um** lugar certo para a resposta: "como trabalhamos?" no `CLAUDE.md`, "onde paramos?" no `HANDOFF.md`, "o que falta?" no `pendencias.md`, "por que está assim?" no `historico.md`, "como o ambiente está montado?" no `SETUP.md`, "o que mudou no código?" no **commit**. Nenhum documento responde a duas dessas.

**Fonte única:** cada fato mora num lugar só; os outros documentos **apontam** para ele, não copiam. Documento desatualizado quase sempre é cópia.

## 1. Os documentos

| Arquivo | Responde | Regra de escrita |
|---|---|---|
| `CLAUDE.md` (raiz) | Como trabalhamos | Instruções permanentes: papéis, regras, pastas, lista de documentos e ordem de prioridade em conflito. Curto: regra, não história. |
| `CLAUDE.md` de cada app/pasta | Como mexer nesta parte | Peças, como rodar, testar e publicar. O `SETUP.md` fica só com o que é comum. |
| `HANDOFF.md` | Onde paramos | **Só o estado atual**, com limite de tamanho (seção 3). Abre com "Retomar aqui": estado de cada parte e **um** próximo passo, git (inclusive o que fica fora de propósito), testes, sessões em andamento e avisos. "Decisões fechadas" só com as que valem para o projeto todo. |
| commit | O que mudou | **Descritivo** (modelo na seção 8): o que, por quê, o que foi verificado e o que não foi. |
| `docs/historico.md` | Por que está assim | Diário cronológico, **só acrescenta no fim**, **uma ou duas linhas por marco**. O "como foi feito" fica no commit. |
| `docs/pendencias.md` | O que falta | Só o que **ainda não** foi feito, por horizonte, mais **decisões em aberto do diretor** e dívidas técnicas. Data da última revisão completa no topo. |
| `SETUP.md` | Como o ambiente está montado | Máquina, servidor, versões, ferramentas, contas externas e **cada escolha técnica com motivo e data**. Nome de segredo sim, valor nunca. |
| `docs/arquivo/` | O que foi superado | Nunca apagar: arquivar com a data no nome (`handoff-ate-AAAA-MM-DD.md`). |

**Do domínio, conforme o projeto pede:** regras de negócio em seções numeradas (quem pediu, quem validou, quando); plano por etapas com "como o diretor testa"; contrato de API; casos testados; visão e design escritos como **hipóteses**; pesquisa com **[V] verificado** ou **[I] inferido** e a fonte; brainstorm separado em "decidido", "proposta do agente" e "em aberto".

**Memória do agente** (fora do git, só nesta máquina): só lições sobre o comportamento do agente; **nada que o projeto precise para continuar**. Regra de trabalho vai **também** para o `CLAUDE.md`.

## 2. Marcos e gatilhos

É **marco** quando acontece qualquer um destes:
1. Algo foi **publicado** (deploy, migração, conteúdo no ar).
2. Uma **etapa do plano** terminou, mesmo sem publicar.
3. O diretor tomou uma **decisão que fecha uma discussão**.
4. Aconteceu um **erro ou incidente**.
5. A **sessão vai terminar** (ou a conversa vai ser resumida).

Commit não é marco: a documentação fica pronta antes e vai no mesmo commit.

| Aconteceu | Atualizar |
|---|---|
| Publicou algo | linha no `historico`; `HANDOFF` (estado da parte); `pendencias` (sai o feito, entra o que sobrou); doc da parte se a regra ou a API mudou |
| Etapa do plano terminou | o mesmo de "publicou", mais a linha de atualização do plano |
| Comando, peça ou cuidado de uma parte mudou | o `CLAUDE.md` daquela parte |
| Diretor decidiu algo | o doc da discussão, com "(decisão do <diretor>, DD/MM/AAAA)"; sai de "Decisões em aberto"; se fecha o assunto de vez, entra em "Decisões fechadas" do `HANDOFF` |
| Regra de negócio nova ou mudada | regras de negócio, com quem pediu e quem validou; nada de código antes da validação |
| Ideia ou pedido para depois | só `pendencias`, no grupo certo |
| Servidor, versão, ferramenta, DNS, porta ou **nome** de segredo mudou | `SETUP` |
| Regra nova de como trabalhamos | `CLAUDE.md`; se for comportamento do agente, também a memória |
| Erro ou incidente | `historico`, com a regra que nasceu dele (seção 6, "Registro de erro") |
| Consulta sem mudança | nada, a não ser que apareça um achado, que vai para `pendencias` |
| Fim de sessão | `HANDOFF` ("Retomar aqui") |
| Documento inchou ou foi substituído | versão antiga para `docs/arquivo/` com a data no nome |

O diretor pode pedir a qualquer momento: "atualiza as documentações".

## 3. Tamanho do HANDOFF

- **Cada parte (app, sistema) ocupa no máximo 5 linhas** em "Retomar aqui": onde está, o que falta o diretor conferir e o próximo passo.
- Cópias de banco, versões anteriores, datas de cada publicação e "como foi feito" **não** são estado atual: vão para o histórico.
- A cada marco: **"isso ainda é estado atual?"**. Se não for, sai.
- Passou de umas 80 linhas ou virou diário: a versão inteira vai para `docs/arquivo/handoff-ate-AAAA-MM-DD.md` e o HANDOFF é reescrito curto.

## 4. Várias sessões ao mesmo tempo

Quando há uma sessão por parte e uma de orquestração:
- **Cada sessão cuida dos arquivos da sua parte.** Não mexe em código de outra.
- **Arquivos compartilhados** (`HANDOFF`, `historico`, `pendencias`, `CLAUDE.md`): reler antes de editar. No histórico, só acrescentar no fim e ler só as últimas linhas. No HANDOFF e nas pendências, mexer só no próprio bloco.
- **Não reverter** mudança que não é sua.
- **Commit:** cada sessão commita só os próprios arquivos (e trechos), com o "commita" do diretor **dado naquela sessão**.
- **A orquestração** abre as sessões, repassa decisões, cuida dos documentos gerais e revisa a documentação de todas. Não escreve código de parte que tem sessão própria. Regra nova de documentação: avisa as sessões em andamento.

## 5. Os ritos

**Começo de sessão:** os `CLAUDE.md` carregam sozinhos e o hook de início entrega o HANDOFF (seção 7). Ler o `SETUP.md` antes de mexer em configuração.

**Custo de contexto:** arquivo lido fica na conversa até o fim.
- Histórico: ler só o fim (20 a 30 linhas). Passou de umas 100 entradas: as antigas vão para `docs/arquivo/historico-ate-<data>.md`.
- HANDOFF: não reler o que o hook entregou; reler só antes de editar.
- Procurar com busca antes de abrir documento grande inteiro.
- Antes de recomendar arquivo ou função que uma memória cita, conferir se ainda existe.

**Antes de cada mudança:** dizer em **2 a 4 frases o que muda e por quê**. Mais de 3 arquivos: propor antes. Nada visual ou público entra sem aprovação do diretor.

**Depois de cada mudança:** verificar sozinho (compilação, testes e, se aparece no produto, executar e conferir na tela). O relato diz **o que foi verificado e o que não foi**. Nunca "deve funcionar".

**Registro de decisão:** toda decisão leva **quem e quando**: "(decisão do <diretor>, DD/MM/AAAA)"; proposta do agente: "(proposta do Claude, DD/MM/AAAA)". Decisão em aberto vai para `pendencias`, com o documento da discussão. Em conflito entre documentos, vale a ordem escrita no `CLAUDE.md` do projeto.

**Registro de erro:** todo erro (do agente ou do diretor) entra no histórico **com a regra que nasceu dele**. Regra de **operação** vai para "Regras de operação" do HANDOFF; de **comportamento do agente**, para a memória e o `CLAUDE.md`. O agente reconhece o próprio erro sem esperar ser descoberto.

**Relato de teste do diretor:** o diretor relata "o que tentei e o que vi". O agente registra em `pendencias` e, quando decidido, no histórico. **Nenhuma mudança nova antes de testar a anterior.**

**Pesquisa:** fonte em toda afirmação; [V] conferido na página, [I] dedução; o que não deu para conferir fica escrito como não conferido.

**Git:** commit e push **só quando o diretor pede**. A documentação vai no mesmo commit da mudança. O HANDOFF lista o que está **fora do git de propósito**.

**Revisão das pendências:** a data "Revisada em" muda só numa **revisão completa** (cada item conferido contra o estado real).

**Fim de cada turno:** o relato diz **o que não foi feito nem verificado**. Se sobra decisão para o diretor, uma pergunta só.

**Formato:** datas absolutas (DD/MM/AAAA), nunca "ontem". Português simples. Nomes de arquivo sem acento, em kebab-case.

## 6. Aviso de risco de perda

Escrever **"⚠️ Risco de perda:"** no relato, com o que e o que fazer, sempre que algo pode se perder:
- **mudança sem commit** quando a sessão vai terminar, ou de outra sessão parada há mais de um marco;
- **fato só na conversa ou só na memória do agente** (decisão, número, link, combinado), principalmente antes de a conversa ser resumida;
- **documentos que se contradizem**, ou um que cita arquivo, função ou etapa que não existe mais;
- **arquivo compartilhado alterado por outra sessão** entre a leitura e a edição;
- **algo que só existe no servidor** (cópias de banco, segredos, configuração feita à mão) sem registro ou sem cópia fora dele;
- **entrada do histórico sem o que foi verificado**, ou commit que não diz o porquê.

O aviso não espera o diretor perguntar e não some até ser resolvido ou o diretor aceitar o risco (registrado com data).

## 7. Travas automáticas

Regra escrita não basta: a que custa caro vira trava mecânica. Este plugin liga quatro, **só em projeto com `.claude/ritos.json`**:
- **Início de sessão** (também depois de resumo): o HANDOFF (até `handoff_max_linhas`, padrão 80; acima disso corta e avisa para arquivar), o `git status` e os últimos commits entram no contexto; arquivo sem commit vira "⚠️ Risco de perda" para o diretor. Liga a trava de commit: `core.hooksPath` aponta para o plugin, e os hooks que o projeto já tinha (`.git/hooks`, husky, `.githooks`) continuam rodando, chamados pelo plugin.
- **Antes de resumir a conversa:** pede ao resumo uma seção "Ainda só na conversa" com decisão, número, link ou combinado ainda não escrito. Depois do resumo, o início de sessão manda registrar o que ela listou.
- **Fim do turno:** lista os arquivos mudados nesta sessão e sem commit (por Edit/Write **e** por comando no terminal, comparando com a foto do início). Se há código entre eles e nem o histórico nem o HANDOFF mudaram, o agente volta **uma vez** para atualizar ou dizer que não é marco. Se o diretor usou palavra de decisão ("decidi", "aprovado", "fica assim"...) e nenhum documento mudou, volta **uma vez por sessão** para registrar ou responder "nada a registrar" (`lembrar_decisoes: false` desliga).
- **Commit:** recusado sem "Por quê:" ou "Verificado:", com código sem o histórico, ou com o histórico mudado fora do fim. Quando não é marco: `Sem histórico: <motivo>`; correção de propósito no histórico: `Histórico editado: <motivo>`. Merge, revert e fixup passam. **Nunca contornar com `--no-verify`.**
- Limites: a trava confere que o documento mudou, não que o texto está certo; o lembrete de decisão é por palavra, não por sentido; arquivo mudado por outra sessão ao mesmo tempo também conta como "desta sessão". Erro interno e falta de Python deixam passar, com aviso.

`.claude/ritos.json` (todos os campos são opcionais):
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
`codigo` vazio: conta como código tudo que não é `.md` fora de `docs/` e `.claude/`.

Para tirar o plugin de um projeto: `sh <pasta do plugin>/scripts/rodar.sh desligar` (devolve o `core.hooksPath` ao que era) e apagar o `.claude/ritos.json`.

## 8. Modelos

**Commit:**
```
<Parte>: <o que, em poucas palavras>

O que: <o que mudou, do ponto de vista de quem usa>.
Por quê: <regra ou pedido> (decisão do <diretor>, DD/MM/AAAA).
Verificado: <testes n/n, telas conferidas, publicado>.
Não verificado: <...>.
Sem histórico: <motivo>   (só quando não é marco)
```

**Entrada do `historico.md`** (cita o commit pelo título, porque vai no mesmo commit e ainda não tem hash):
```
- DD/MM/AAAA · <Parte>: <o que> (decisão do <diretor>). Por quê: <regra ou pedido>. Verificado: <...>; não verificado: <...>. Incidente: <o que e a regra que nasceu, ou "nenhum">. Commit "<título>".
```

Esqueletos de `CLAUDE.md`, `HANDOFF.md` e `pendencias.md`: skill `ritos:iniciar`.

## 9. O que já falhou (e o que isso ensina)

- **HANDOFF inchado** (duas vezes: 415 linhas de blocos por data; depois um bloco virou diário). **Lição:** 5 linhas por parte e "isso ainda é estado atual?" a cada marco.
- **"A cada marco" sem definir marco:** o `CLAUDE.md` ficou dizendo "próximo passo é o login" com o login no ar havia dias. **Lição:** marco definido e tabela de gatilhos.
- **Design para trás:** números do escopo que o protótipo já tinha mudado. **Lição:** quando a realidade derruba uma hipótese, marcar na hora ("superado em DD/MM, ver histórico").
- **Regra escrita quebrada 3 vezes** até virar bloqueio automático. **Lição:** regra cara vira trava mecânica.
- **A mesma regra pedida duas vezes:** estava só na memória do agente. **Lição:** regra de trabalho vai também para o `CLAUDE.md`.
- **Post que soou escrito por IA:** o agente escreveu o rascunho no molde que as redes reconhecem e deixou de fora a história real. **Lição:** em conteúdo com a voz do diretor, o agente prepara o estudo (história, números conferidos, ângulos, o que não dizer) e o diretor escreve.
