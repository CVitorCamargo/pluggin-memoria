# Incluído pelos hooks desta pasta (não é um hook).
# core.hooksPath aponta para esta pasta, e isso faria o git ignorar os hooks que o
# projeto já tinha. Por isso cada hook daqui chama o hook de mesmo nome do lugar
# anterior: o core.hooksPath que existia antes (guardado em ritos.hooksPathAnterior)
# ou, se não havia nenhum, a pasta padrão .git/hooks.
encaminhar() {
  nome=$1
  shift
  base=$(git config --get ritos.hooksPathAnterior)
  [ -z "$base" ] && base="$(git rev-parse --git-common-dir)/hooks"
  alvo="$base/$nome"
  if [ -f "$alvo" ] && [ -x "$alvo" ]; then
    exec "$alvo" "$@"
  fi
  exit 0
}
