#!/bin/sh
# Acha um Python 3 que funciona e roda ritos.py com os argumentos recebidos.
# Sem Python: avisa no stderr e deixa passar (trava com defeito não para o trabalho).
# O teste "-c ''" descarta o atalho da Microsoft Store, que existe no PATH mas não roda.
AQUI=$(cd "$(dirname "$0")" && pwd)
for p in python3 python py; do
  if command -v "$p" >/dev/null 2>&1 && "$p" -c "" </dev/null >/dev/null 2>&1; then
    exec "$p" "$AQUI/ritos.py" "$@"
  fi
done
echo "ritos: Python 3 não encontrado no PATH; a trava \"$1\" não conferiu nada." >&2
exit 0
