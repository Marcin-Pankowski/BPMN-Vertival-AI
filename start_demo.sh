#!/usr/bin/env bash
# Startet Laya-Dienst (Port 8000) und Kogito-Prozessdienst (Port 8080), wartet, bis beide bereit sind,
# und führt run_demo_cases.py aus. Die Dienste laufen danach weiter (Dashboard im Browser) bis Strg+C.
#
#   ./start_demo.sh                      # Demo-Fälle starten, offene Prüfungen bleiben stehen
#   ./start_demo.sh --decide approve     # Argumente gehen an run_demo_cases.py
#   BUILD=1 ./start_demo.sh              # vorher neu bauen (mvn package, inkl. Tests)
#   NO_CASES=1 ./start_demo.sh           # nur Dienste starten, keine Demo-Fälle
#
# Fehlt .venv, legt das Skript sie aus requirements.txt an. Fehlt Modell v2, lädt es das ZIP aus dem GitHub Release "modelle".
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOGS="$ROOT/logs"
JAR="$ROOT/kyc-prozess/target/quarkus-app/quarkus-run.jar"
mkdir -p "$LOGS"

for port in 8000 8080; do
  if lsof -ti tcp:$port >/dev/null 2>&1; then
    echo "Port $port ist schon belegt. Laufenden Dienst beenden oder: lsof -ti tcp:$port | xargs kill" >&2
    exit 1
  fi
done

MODEL="$ROOT/modelle/laya-multilingual-kyc-v2/model.safetensors"
MODEL_ZIP_URL="https://github.com/Marcin-Pankowski/BPMN-Vertival-AI/releases/download/modelle/laya-multilingual-kyc-v2.zip"
if [[ ! -f "$MODEL" ]]; then
  echo "Lade Modell v2 aus dem GitHub Release (ca. 600 MB, einmalig) …"
  curl -fL --progress-bar -o "$ROOT/modelle-v2.zip" "$MODEL_ZIP_URL"
  unzip -q -o "$ROOT/modelle-v2.zip" -d "$ROOT"
  rm -f "$ROOT/modelle-v2.zip"
fi

if [[ ! -x "$ROOT/.venv/bin/uvicorn" ]]; then
  PY="$(command -v python3.12 || command -v python3)"
  echo "Lege Python-Umgebung .venv mit $("$PY" --version) an (einmalig, lädt PyTorch, einige Minuten) …"
  "$PY" -m venv "$ROOT/.venv"
  "$ROOT/.venv/bin/pip" install -q --upgrade pip
  "$ROOT/.venv/bin/pip" install -q -r "$ROOT/requirements.txt"
fi

if [[ "${BUILD:-0}" == "1" || ! -f "$JAR" ]]; then
  echo "Baue Prozessdienst …"
  (cd "$ROOT/kyc-prozess" && mvn -q package)
fi

PIDS=()
cleanup() {
  echo; echo "Beende Dienste …"
  for pid in "${PIDS[@]}"; do kill "$pid" 2>/dev/null || true; done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starte Laya-Dienst (Log: logs/laya.log) …"
(cd "$ROOT/laya_kyc" && exec "$ROOT/.venv/bin/uvicorn" laya_service:app --port 8000) >"$LOGS/laya.log" 2>&1 &
PIDS+=($!)

echo "Starte Prozessdienst (Log: logs/kogito.log) …"
(cd "$ROOT/kyc-prozess" && exec java -jar "$JAR") >"$LOGS/kogito.log" 2>&1 &
PIDS+=($!)

wait_for() {  # name url log
  printf "Warte auf %s " "$1"
  for _ in $(seq 1 180); do
    if curl -sf "$2" >/dev/null; then echo "✓"; return 0; fi
    for pid in "${PIDS[@]}"; do
      if ! kill -0 "$pid" 2>/dev/null; then echo "✗ abgebrochen, siehe $3"; tail -20 "$3"; exit 1; fi
    done
    printf "."; sleep 1
  done
  echo "✗ Zeitüberschreitung, siehe $3"; exit 1
}
wait_for "Laya" http://localhost:8000/health "$LOGS/laya.log"
wait_for "Kogito" http://localhost:8080/q/health/ready "$LOGS/kogito.log"

if [[ "${NO_CASES:-0}" != "1" ]]; then
  echo
  python3 "$ROOT/kyc-prozess/run_demo_cases.py" "$@"
fi

echo
echo "Weboberfläche: http://localhost:8080   (Dashboard: http://localhost:8080/#dashboard)"
echo "Dienste laufen weiter. Beenden mit Strg+C."
open http://localhost:8080/#dashboard 2>/dev/null || true
wait
