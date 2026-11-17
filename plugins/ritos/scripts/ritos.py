"""Travas dos ritos de documentação (skill ritos:ritos, "Travas automáticas").

Um script só, chamado de três lugares:
  sessao      -> hook SessionStart do Claude Code (hooks/hooks.json do plugin)
  fim         -> hook Stop do Claude Code
  commit-msg  -> hook de commit do git (githooks/commit-msg do plugin)

Só age em projeto que tem .claude/ritos.json (o projeto pede os ritos).
Sem esse arquivo, sai calado: o plugin instalado não mexe em pasta alheia.

Regra de ouro: na dúvida, deixa passar. Uma trava com defeito não pode
parar o trabalho; por isso todo erro inesperado sai sem bloquear.
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
    # Onde mora o que é só deste projeto (aparece nas mensagens das travas).
    "ritos_projeto": "",
}


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


# ---------------------------------------------------------------- sessao

def ligar_trava_commit(raiz):
    """Aponta core.hooksPath para os hooks do plugin. Devolve um aviso ou None.

    O caminho do plugin muda a cada versão instalada, por isso é conferido em
    todo início de sessão. Não toma o lugar de hooks de outra ferramenta.
    """
    atual = git(raiz, "config", "--get", "core.hooksPath").strip()
    if atual == HOOKS_GIT:
        return None
    nosso = atual in ("", ".githooks") or re.search(r"/ritos/.*/githooks$", atual)
    if not nosso:
        return (
            f"Trava de commit dos ritos NÃO ligada: core.hooksPath já aponta para "
            f"\"{atual}\" (outra ferramenta). Os commits não são conferidos."
        )
    git(raiz, "config", "core.hooksPath", HOOKS_GIT)
    return "Trava de commit ligada (core.hooksPath aponta para o plugin ritos)."


def sessao():
    dados = entrada()
    raiz = achar_raiz(dados)
    cfg = ler_config(raiz)
    if cfg is None:
        return
    origem = dados.get("source", "startup")
    partes = []

    aviso_trava = ligar_trava_commit(raiz)
    if aviso_trava:
        partes.append(aviso_trava)

    try:
        with open(os.path.join(raiz, cfg["handoff"]), encoding="utf-8") as f:
            partes.append(f"{cfg['handoff']} (lido automaticamente pelo hook de início):\n" + f.read())
    except OSError:
        partes.append(f"⚠️ {cfg['handoff']} não encontrado (a skill ritos:iniciar monta o kit mínimo).")

    pendentes = mudancas(raiz)
    aviso = None
    if pendentes:
        lista = "\n".join("  " + p for p in pendentes[:30])
        partes.append(
            f"git: {len(pendentes)} arquivo(s) sem commit (podem ser de outra sessão; "
            f"não reverter):\n{lista}"
        )
        aviso = f"⚠️ Risco de perda: {len(pendentes)} arquivo(s) sem commit na pasta."
    partes.append("Últimos commits:\n" + git(raiz, "log", "-5", "--format=  %h %s"))
    partes.append(f"Ritos de documentação: {onde_ler(cfg)}.")

    if origem == "compact":
        partes.append(
            "A conversa acabou de ser resumida. Antes de seguir: decisão, número, link "
            "ou combinado que só estava na conversa vai para o documento certo (ritos, "
            "\"Marcos e gatilhos\"); se não der agora, escreva \"⚠️ Risco de perda:\" no relato."
        )

    resposta = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n\n".join(partes),
        }
    }
    if aviso:
        resposta["systemMessage"] = aviso
    saida(resposta)


# ------------------------------------------------------------------- fim

def editados_na_sessao(raiz, transcript):
    """Arquivos que esta sessão mexeu pelas ferramentas Edit/Write."""
    editados = set()
    if not transcript or not os.path.exists(transcript):
        return editados
    raiz = os.path.normcase(raiz)
    with open(transcript, encoding="utf-8", errors="replace") as f:
        for linha in f:
            if '"tool_use"' not in linha:
                continue
            try:
                d = json.loads(linha)
            except ValueError:
                continue
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


def estado(sessao_id):
    pasta = os.path.join(tempfile.gettempdir(), "ritos-plugin")
    os.makedirs(pasta, exist_ok=True)
    return os.path.join(pasta, re.sub(r"[^\w-]", "_", sessao_id or "sem-id") + ".json")


def fim():
    dados = entrada()
    raiz = achar_raiz(dados)
    cfg = ler_config(raiz)
    if cfg is None:
        return
    pendentes = mudancas(raiz)
    pendentes_norm = {os.path.normcase(p): p for p in pendentes}
    meus = sorted(
        pendentes_norm[os.path.normcase(e)]
        for e in editados_na_sessao(raiz, dados.get("transcript_path"))
        if os.path.normcase(e) in pendentes_norm
    )
    resposta = {}

    if meus:
        mostrar = ", ".join(meus[:6]) + (f" e mais {len(meus) - 6}" if len(meus) > 6 else "")
        resposta["systemMessage"] = (
            f"⚠️ Risco de perda: {len(meus)} arquivo(s) desta sessão sem commit: {mostrar}."
        )

    codigo = [p for p in meus if eh_codigo(cfg, p)]
    docs_tocados = any(p in (cfg["historico"], cfg["handoff"]) for p in pendentes)
    if codigo and not docs_tocados and not dados.get("stop_hook_active"):
        # Cobra uma vez por conjunto de arquivos, não a cada turno.
        marca = hashlib.sha1("\n".join(codigo).encode()).hexdigest()
        arq = estado(dados.get("session_id"))
        try:
            with open(arq, encoding="utf-8") as f:
                ja_cobrado = json.load(f).get("cobrado", [])
        except (OSError, ValueError):
            ja_cobrado = []
        if marca not in ja_cobrado:
            with open(arq, "w", encoding="utf-8") as f:
                json.dump({"cobrado": (ja_cobrado + [marca])[-50:]}, f)
            resposta["decision"] = "block"
            resposta["reason"] = (
                "Trava dos ritos: esta sessão mudou código sem commit ("
                + ", ".join(codigo[:5])
                + f") e nem {cfg['historico']} nem {cfg['handoff']} mudaram. Se isso fechou "
                f"um marco ({onde_ler(cfg)}, \"Marcos e gatilhos\"), atualize os documentos "
                "agora. Se ainda não é marco, diga isso em uma linha no relato e siga. "
                "Lembre que o commit só passa com a linha no histórico ou com "
                "\"Sem histórico: <motivo>\"."
            )

    if resposta:
        saida(resposta)


# ------------------------------------------------------------ commit-msg

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

    for rotulo in ("Por quê:", "Verificado:"):
        if not re.search(r"(?mi)^" + re.escape(rotulo), texto):
            erros.append(f"falta a linha \"{rotulo}\" (formato em \"Modelos\" da skill ritos:ritos)")

    codigo = [p for p in staged if eh_codigo(cfg, p)]
    historico = cfg["historico"]
    if codigo and historico not in staged and not re.search(r"(?mi)^Sem histórico:\s*\S", texto):
        erros.append(
            "o commit mexe em código ("
            + ", ".join(codigo[:4])
            + (" ..." if len(codigo) > 4 else "")
            + f") e não leva {historico}. Inclua a linha do histórico ou, se não "
            "é marco, escreva na mensagem \"Sem histórico: <motivo>\""
        )

    if erros:
        sys.stderr.reconfigure(encoding="utf-8")
        print(f"Commit recusado pela trava dos ritos ({onde_ler(cfg)}):", file=sys.stderr)
        for e in erros:
            print("  - " + e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if modo == "sessao":
            sessao()
        elif modo == "fim":
            fim()
        elif modo == "commit-msg":
            sys.exit(commit_msg(sys.argv[2]))
    except SystemExit:
        raise
    except Exception as erro:  # trava com defeito não para o trabalho
        sys.stderr.reconfigure(encoding="utf-8")
        print(f"ritos.py {modo}: erro interno, deixei passar ({erro})", file=sys.stderr)
        sys.exit(0)
