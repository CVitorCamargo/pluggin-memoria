"""Travas dos ritos de documentação (skill ritos:ritos, "Travas automáticas").

Um script só, chamado por scripts/rodar.sh (que acha o Python) de quatro lugares:
  sessao      -> hook SessionStart do Claude Code (hooks/hooks.json do plugin)
  resumo      -> hook PreCompact do Claude Code (instruções para o resumo)
  fim         -> hook Stop do Claude Code
  commit-msg  -> hook de commit do git (githooks/commit-msg do plugin)
E um comando manual:
  desligar    -> devolve o core.hooksPath ao que era antes do plugin

Só age em projeto que tem .claude/ritos.json (o projeto pede os ritos).
Sem esse arquivo, sai calado: o plugin instalado não mexe em pasta alheia.

Regra de ouro: na dúvida, deixa passar. Uma trava com defeito não pode
parar o trabalho; por isso todo erro inesperado sai sem bloquear.

Custo em tokens: só o início de sessão põe texto fixo no contexto (HANDOFF com
teto de linhas, git status com teto de 30 arquivos, 5 commits). O fim do turno
cobra no máximo uma vez por conjunto de arquivos e uma vez por sessão para
decisão de conversa. O commit roda fora da conversa.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

PLUGIN = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HOOKS_GIT = os.path.join(PLUGIN, "githooks").replace("\\", "/")
CONFIG = os.path.join(".claude", "ritos.json")

PADRAO = {
    # Pastas de código (prefixos). Vazio: tudo que não é .md fora de docs/ e .claude/.
    "codigo": [],
    "historico": "docs/historico.md",
    "handoff": "HANDOFF.md",
    "pendencias": "docs/pendencias.md",
    # Onde mora o que é só deste projeto (aparece nas mensagens das travas).
    "ritos_projeto": "",
    # Linhas do HANDOFF entregues no início da sessão; acima disso, corta e avisa.
    "handoff_max_linhas": 80,
    # Fim de turno lembra (uma vez por sessão) de registrar decisão tomada só no chat.
    "lembrar_decisoes": True,
}

# Palavras do diretor que costumam fechar uma decisão ou combinar uma regra.
SINAIS_DECISAO = (
    "decid", "aprov", "combinad", "fechad", "fica assim", "vamos com", "vamos de",
    "pode fazer", "pode seguir", "a regra", "de agora em diante", "daqui pra frente",
    "daqui para frente", "sempre que", "nunca mais", "não quero", "nao quero",
)

FOTO_MAX = 5000


def git(raiz, *args):
    r = subprocess.run(
        ["git", "-c", "core.quotepath=off", *args],
        cwd=raiz, capture_output=True,
    )
    return r.stdout.decode("utf-8", "replace")


def achar_raiz(dados=None):
    """Raiz do projeto: a do Claude Code, senão a do git na pasta atual."""
    base = os.environ.get("CLAUDE_PROJECT_DIR") or (dados or {}).get("cwd") or os.getcwd()
    topo = git(base, "rev-parse", "--show-toplevel").strip()
    return os.path.abspath(topo or base)


def ler_config(raiz):
    try:
        with open(os.path.join(raiz, CONFIG), encoding="utf-8") as f:
            proprio = json.load(f)
    except OSError:
        return None  # projeto não pediu os ritos
    except ValueError:
        proprio = {}  # arquivo com defeito: usa o padrão, não para o trabalho
    cfg = dict(PADRAO)
    cfg.update({k: v for k, v in proprio.items() if k in PADRAO})
    return cfg


def mudancas(raiz):
    """Arquivos com mudança ainda sem commit (inclui os novos)."""
    arquivos = []
    for linha in git(raiz, "status", "--porcelain", "--untracked-files=all").splitlines():
        if len(linha) < 4:
            continue
        caminho = linha[3:].strip().strip('"')
        if " -> " in caminho:
            caminho = caminho.split(" -> ", 1)[1]
        arquivos.append(caminho)
    return arquivos


def eh_codigo(cfg, caminho):
    if caminho.endswith(".md"):
        return False
    if cfg["codigo"]:
        return caminho.startswith(tuple(cfg["codigo"]))
    return not caminho.startswith(("docs/", ".claude/"))


def docs(cfg):
    return (cfg["historico"], cfg["handoff"], cfg["pendencias"])


def onde_ler(cfg):
    extra = f" e {cfg['ritos_projeto']}" if cfg["ritos_projeto"] else ""
    return f"skill ritos:ritos{extra}"


def saida(dados):
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(dados, ensure_ascii=False))


def entrada():
    try:
        return json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    except ValueError:
        return {}


# ------------------------------------------------- estado por sessão (temp)

def arq_estado(sessao_id):
    pasta = os.path.join(tempfile.gettempdir(), "ritos-plugin")
    os.makedirs(pasta, exist_ok=True)
    return os.path.join(pasta, re.sub(r"[^\w-]", "_", sessao_id or "sem-id") + ".json")


def ler_estado(sessao_id):
    try:
        with open(arq_estado(sessao_id), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def gravar_estado(sessao_id, est):
    with open(arq_estado(sessao_id), "w", encoding="utf-8") as f:
        json.dump(est, f)


def assinatura(raiz, caminho):
    """Tamanho e data de um arquivo; None se não existe (foi apagado)."""
    try:
        st = os.stat(os.path.join(raiz, caminho))
        return [st.st_size, st.st_mtime_ns]
    except OSError:
        return None


def foto(raiz, pendentes):
    """Estado dos arquivos sem commit, para saber depois o que mudou nesta sessão."""
    return {p: assinatura(raiz, p) for p in pendentes[:FOTO_MAX]}


# ---------------------------------------------------------------- sessao

def ligar_trava_commit(raiz):
    """Aponta core.hooksPath para os hooks do plugin. Devolve um aviso ou None.

    O caminho do plugin muda a cada versão instalada, por isso é conferido em
    todo início de sessão. O hooksPath que existia antes (husky, .githooks...)
    fica guardado em ritos.hooksPathAnterior, e os hooks do plugin chamam os de
    lá (githooks/_encaminhar.sh): nada do que o projeto já tinha deixa de rodar.
    """
    atual = git(raiz, "config", "--get", "core.hooksPath").strip()
    if atual == HOOKS_GIT:
        return None
    versao_antiga = re.search(r"/ritos/.*/githooks$", atual)
    if atual and not versao_antiga:
        git(raiz, "config", "ritos.hooksPathAnterior", atual)
    git(raiz, "config", "core.hooksPath", HOOKS_GIT)
    if versao_antiga:
        return None  # só a versão do plugin mudou
    de_onde = f"\"{atual}\"" if atual else ".git/hooks"
    return (
        f"Trava de commit ligada (core.hooksPath aponta para o plugin ritos; "
        f"os hooks que já existiam em {de_onde} continuam rodando)."
    )


def handoff_com_teto(cfg, texto):
    """Devolve (texto a entregar, aviso ou None)."""
    linhas = texto.splitlines()
    teto = int(cfg["handoff_max_linhas"] or 0)
    if teto <= 0 or len(linhas) <= teto:
        return texto, None
    cortadas = len(linhas) - teto
    aviso = (
        f"{cfg['handoff']} tem {len(linhas)} linhas (teto {teto}): só as primeiras "
        f"{teto} foram lidas. Arquive a versão inteira em docs/arquivo/"
        f"handoff-ate-AAAA-MM-DD.md e reescreva curto (ritos, seção 3)."
    )
    corpo = "\n".join(linhas[:teto]) + f"\n[... {cortadas} linha(s) não lidas. {aviso}]"
    return corpo, aviso


def sessao():
    dados = entrada()
    raiz = achar_raiz(dados)
    cfg = ler_config(raiz)
    if cfg is None:
        return
    origem = dados.get("source", "startup")
    partes = []
    avisos = []

    aviso_trava = ligar_trava_commit(raiz)
    if aviso_trava:
        partes.append(aviso_trava)

    try:
        with open(os.path.join(raiz, cfg["handoff"]), encoding="utf-8") as f:
            corpo, aviso_tam = handoff_com_teto(cfg, f.read())
        partes.append(f"{cfg['handoff']} (lido automaticamente pelo hook de início):\n" + corpo)
        if aviso_tam:
            avisos.append("⚠️ " + aviso_tam)
    except OSError:
        partes.append(f"⚠️ {cfg['handoff']} não encontrado (a skill ritos:iniciar monta o kit mínimo).")

    pendentes = mudancas(raiz)
    if pendentes:
        lista = "\n".join("  " + p for p in pendentes[:30])
        mais = f"\n  ... e mais {len(pendentes) - 30}" if len(pendentes) > 30 else ""
        partes.append(
            f"git: {len(pendentes)} arquivo(s) sem commit (podem ser de outra sessão; "
            f"não reverter):\n{lista}{mais}"
        )
        avisos.append(f"⚠️ Risco de perda: {len(pendentes)} arquivo(s) sem commit na pasta.")
    partes.append("Últimos commits:\n" + git(raiz, "log", "-5", "--format=  %h %s"))
    partes.append(f"Ritos de documentação: {onde_ler(cfg)}.")

    if origem == "compact":
        partes.append(
            "A conversa acabou de ser resumida. Antes de seguir: o que o resumo marcou "
            "como \"Ainda só na conversa\" vai para o documento certo (ritos, \"Marcos e "
            "gatilhos\"); se não der agora, escreva \"⚠️ Risco de perda:\" no relato."
        )

    # Foto do que já estava sem commit, para o fim do turno separar o que esta
    # sessão mudou (inclusive por comando no terminal). Só na 1ª vez da sessão.
    sid = dados.get("session_id")
    est = ler_estado(sid)
    if "foto" not in est:
        est["foto"] = foto(raiz, pendentes)
        gravar_estado(sid, est)

    resposta = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n\n".join(partes),
        }
    }
    if avisos:
        resposta["systemMessage"] = " ".join(avisos)
    saida(resposta)


# ---------------------------------------------------------------- resumo

def resumo():
    """PreCompact: o que sai no stdout vira instrução para o resumo da conversa."""
    dados = entrada()
    raiz = achar_raiz(dados)
    cfg = ler_config(raiz)
    if cfg is None:
        return
    sys.stdout.reconfigure(encoding="utf-8")
    print(
        "Ritos de documentação: termine o resumo com uma seção \"Ainda só na conversa\" "
        "listando, literalmente e com data DD/MM/AAAA, toda decisão do diretor, número, "
        "link ou combinado desta conversa que ainda não foi escrito em "
        f"{', '.join(docs(cfg))} ou no CLAUDE.md. Se não houver nada, escreva "
        "\"Ainda só na conversa: nada\"."
    )


# ------------------------------------------------------------------- fim

def ler_transcript(transcript):
    """Gera os objetos JSON de cada linha do transcript."""
    if not transcript or not os.path.exists(transcript):
        return
    with open(transcript, encoding="utf-8", errors="replace") as f:
        for linha in f:
            try:
                yield json.loads(linha)
            except ValueError:
                continue


def editados_na_sessao(raiz, transcript):
    """Arquivos que esta sessão mexeu pelas ferramentas Edit/Write."""
    editados = set()
    raiz = os.path.normcase(raiz)
    for d in ler_transcript(transcript):
        conteudo = (d.get("message") or {}).get("content") or []
        for c in conteudo if isinstance(conteudo, list) else []:
            if not isinstance(c, dict) or c.get("type") != "tool_use":
                continue
            if c.get("name") not in ("Edit", "Write", "NotebookEdit"):
                continue
            entrada_ = c.get("input") or {}
            caminho = entrada_.get("file_path") or entrada_.get("notebook_path")
            if not caminho:
                continue
            caminho = os.path.normcase(os.path.abspath(caminho))
            if caminho.startswith(raiz + os.sep):
                editados.add(caminho[len(raiz) + 1:].replace("\\", "/"))
    return editados


def falas_do_diretor(transcript):
    """Texto digitado pelo diretor (sem resultado de ferramenta nem aviso do sistema)."""
    for d in ler_transcript(transcript):
        if d.get("type") != "user" or d.get("isMeta"):
            continue
        conteudo = (d.get("message") or {}).get("content")
        if isinstance(conteudo, str):
            textos = [conteudo]
        elif isinstance(conteudo, list):
            textos = [c.get("text", "") for c in conteudo
                      if isinstance(c, dict) and c.get("type") == "text"]
        else:
            continue
        for t in textos:
            t = re.sub(r"<([\w-]+)>.*?</\1>", "", t, flags=re.S).strip()
            if t:
                yield t


def teve_decisao(transcript):
    for t in falas_do_diretor(transcript):
        baixo = t.lower()
        if any(s in baixo for s in SINAIS_DECISAO):
            return True
    return False


def mudados_desde_inicio(raiz, foto_inicio, pendentes):
    """Arquivos sem commit que não estavam assim no início ou mudaram desde então."""
    if foto_inicio is None:
        return set()
    return {
        p for p in pendentes
        if p not in foto_inicio or foto_inicio[p] != assinatura(raiz, p)
    }


def fim():
    dados = entrada()
    raiz = achar_raiz(dados)
    cfg = ler_config(raiz)
    if cfg is None:
        return
    sid = dados.get("session_id")
    transcript = dados.get("transcript_path")
    est = ler_estado(sid)

    pendentes = mudancas(raiz)
    pendentes_norm = {os.path.normcase(p): p for p in pendentes}
    meus = {
        pendentes_norm[os.path.normcase(e)]
        for e in editados_na_sessao(raiz, transcript)
        if os.path.normcase(e) in pendentes_norm
    }
    meus |= mudados_desde_inicio(raiz, est.get("foto"), pendentes)
    meus = sorted(meus)

    resposta = {}
    motivos = []

    if meus:
        mostrar = ", ".join(meus[:6]) + (f" e mais {len(meus) - 6}" if len(meus) > 6 else "")
        resposta["systemMessage"] = (
            f"⚠️ Risco de perda: {len(meus)} arquivo(s) mudado(s) nesta sessão sem commit: {mostrar}."
        )

    if not dados.get("stop_hook_active"):
        codigo = [p for p in meus if eh_codigo(cfg, p)]
        docs_tocados = any(p in docs(cfg)[:2] for p in pendentes)
        if codigo and not docs_tocados:
            # Cobra uma vez por conjunto de arquivos, não a cada turno.
            marca = hashlib.sha1("\n".join(codigo).encode()).hexdigest()
            cobrado = est.get("cobrado", [])
            if marca not in cobrado:
                est["cobrado"] = (cobrado + [marca])[-50:]
                motivos.append(
                    "esta sessão mudou código sem commit ("
                    + ", ".join(codigo[:5])
                    + f") e nem {cfg['historico']} nem {cfg['handoff']} mudaram. Se isso "
                    f"fechou um marco ({onde_ler(cfg)}, \"Marcos e gatilhos\"), atualize os "
                    "documentos agora; se ainda não é marco, diga isso em uma linha no relato. "
                    "O commit só passa com a linha no histórico ou com \"Sem histórico: <motivo>\""
                )

        # Decisão tomada só na conversa: lembra uma vez por sessão, e só se o
        # diretor usou palavra de decisão e nenhum documento mudou nesta sessão.
        docs_da_sessao = any(p in docs(cfg) for p in meus)
        if (cfg["lembrar_decisoes"] and not est.get("decisao_lembrada")
                and not docs_da_sessao and teve_decisao(transcript)):
            est["decisao_lembrada"] = True
            motivos.append(
                "o diretor parece ter decidido ou combinado algo nesta conversa e nenhum "
                f"documento ({', '.join(docs(cfg))}, CLAUDE.md) mudou. Se há decisão, regra "
                "ou número que só está no chat, registre no documento certo; se não há, "
                "responda só \"nada a registrar\""
            )

    if motivos:
        gravar_estado(sid, est)
        resposta["decision"] = "block"
        resposta["reason"] = "Trava dos ritos: " + ". Além disso, ".join(motivos) + "."

    if resposta:
        saida(resposta)


# ------------------------------------------------------------ commit-msg

def historico_so_no_fim(raiz, historico):
    """True se a mudança preparada no histórico só acrescenta linhas no fim."""
    diff = git(raiz, "diff", "--cached", "-U0", "--no-color", "--", historico)
    if not diff.strip():
        return True
    anterior = git(raiz, "show", f"HEAD:{historico}")
    total = len(anterior.splitlines())
    trechos = []
    for linha in diff.splitlines():
        m = re.match(r"@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@", linha)
        if m:
            trechos.append({"ini": int(m.group(1)), "qtd": int(m.group(2) or 1),
                            "sai": [], "entra": []})
        elif trechos and linha.startswith("-") and not linha.startswith("---"):
            trechos[-1]["sai"].append(linha[1:].rstrip())
        elif trechos and linha.startswith("+") and not linha.startswith("+++"):
            trechos[-1]["entra"].append(linha[1:].rstrip())
    for t in trechos:
        if t["qtd"] == 0 and t["ini"] == total:
            continue  # acrescentou no fim
        # Última linha sem quebra no fim: o git mostra ela saindo e voltando igual.
        if (t["qtd"] == 1 and t["ini"] == total and t["entra"]
                and t["sai"] == t["entra"][:1]):
            continue
        return False
    return True


def commit_msg(arquivo):
    raiz = achar_raiz()
    cfg = ler_config(raiz)
    if cfg is None:
        return 0
    with open(arquivo, encoding="utf-8", errors="replace") as f:
        texto = "\n".join(l for l in f.read().splitlines() if not l.startswith("#"))
    if not texto.strip():
        return 0  # o próprio git recusa mensagem vazia
    primeira = texto.strip().splitlines()[0]
    if primeira.startswith(("Merge ", "Revert ", "fixup!", "squash!")):
        return 0

    staged = [l for l in git(raiz, "diff", "--cached", "--name-only").splitlines() if l]
    erros = []

    for rotulo, padrao in (("Por quê:", r"Por qu[eê]:"), ("Verificado:", r"Verificado:")):
        if not re.search(r"(?mi)^" + padrao, texto):
            erros.append(f"falta a linha \"{rotulo}\" (formato em \"Modelos\" da skill ritos:ritos)")

    codigo = [p for p in staged if eh_codigo(cfg, p)]
    historico = cfg["historico"]
    if codigo and historico not in staged and not re.search(r"(?mi)^Sem hist[oó]rico:\s*\S", texto):
        erros.append(
            "o commit mexe em código ("
            + ", ".join(codigo[:4])
            + (" ..." if len(codigo) > 4 else "")
            + f") e não leva {historico}. Inclua a linha do histórico ou, se não "
            "é marco, escreva na mensagem \"Sem histórico: <motivo>\""
        )

    if (historico in staged and not historico_so_no_fim(raiz, historico)
            and not re.search(r"(?mi)^Hist[oó]rico editado:\s*\S", texto)):
        erros.append(
            f"{historico} só acrescenta no fim, e este commit muda ou apaga linhas antigas. "
            "Se a correção é de propósito, escreva na mensagem \"Histórico editado: <motivo>\""
        )

    if erros:
        sys.stderr.reconfigure(encoding="utf-8")
        print(f"Commit recusado pela trava dos ritos ({onde_ler(cfg)}):", file=sys.stderr)
        for e in erros:
            print("  - " + e, file=sys.stderr)
        return 1
    return 0


# -------------------------------------------------------------- desligar

def desligar():
    """Devolve o core.hooksPath ao que era antes do plugin (rodar antes de desinstalar)."""
    sys.stdout.reconfigure(encoding="utf-8")
    raiz = achar_raiz()
    atual = git(raiz, "config", "--get", "core.hooksPath").strip()
    if not re.search(r"/ritos/.*/githooks$", atual) and atual != HOOKS_GIT:
        print("core.hooksPath não aponta para o plugin ritos; nada a fazer.")
        return
    anterior = git(raiz, "config", "--get", "ritos.hooksPathAnterior").strip()
    if anterior:
        git(raiz, "config", "core.hooksPath", anterior)
        git(raiz, "config", "--unset", "ritos.hooksPathAnterior")
        print(f"core.hooksPath voltou para \"{anterior}\".")
    else:
        git(raiz, "config", "--unset", "core.hooksPath")
        print("core.hooksPath removido; o git volta a usar .git/hooks.")
    print("Tire o .claude/ritos.json do projeto, ou o próximo início de sessão liga de novo.")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if modo == "sessao":
            sessao()
        elif modo == "resumo":
            resumo()
        elif modo == "fim":
            fim()
        elif modo == "commit-msg":
            sys.exit(commit_msg(sys.argv[2]))
        elif modo == "desligar":
            desligar()
    except SystemExit:
        raise
    except Exception as erro:  # trava com defeito não para o trabalho
        sys.stderr.reconfigure(encoding="utf-8")
        print(f"ritos.py {modo}: erro interno, deixei passar ({erro})", file=sys.stderr)
        sys.exit(0)
