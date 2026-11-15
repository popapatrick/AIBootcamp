#!/usr/bin/env bash
# Rulează toate verificările logicii (smoke-uri, teste, limite de reglaj, calibrare). Cod 0 = totul verde.
# Folosire (din rădăcina repo-ului): scripts/verifica_tot.sh
cd "$(dirname "$0")/.." || exit 1
PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
ESUAT=0
for m in backend.extract.test_extract backend.extract.test_cli_ai; do
  if EXTRACT_CLI= $PY -m "$m" >/dev/null 2>&1; then echo "OK   $m"; else echo "FAIL $m"; ESUAT=1; fi
done
EXTRACT_CLI=0 $PY -m backend.engine.verifica_reglaje --strict-distributie || ESUAT=1   # distribuția culorilor (doar rețea) trebuie să fie în țintă
if [ $ESUAT -eq 0 ]; then echo "TOT VERDE"; else echo "EXISTĂ ESECURI"; fi
exit $ESUAT
