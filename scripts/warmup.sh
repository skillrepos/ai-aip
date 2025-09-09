#!/usr/bin/env bash
set -euo pipefail

# --- Config (override via env or flags) ---
MODEL_LIST=${MODEL_LIST:-"llama3.2:latest"}     # comma-separated if multiple
EMBED_MODEL=${EMBED_MODEL:-""}                  # e.g. "nomic-embed-text:latest"
PROMPT_FILE=${PROMPT_FILE:-"extra/curr_conv_agent.txt"}
REPS=${REPS:-3}                                 # number of warmup iterations
CONCURRENCY=${CONCURRENCY:-2}                   # parallel requests to fill caches
USE_JSON=${USE_JSON:-"auto"}                    # auto|true|false  -> json format warmup
OLLAMA_HOST=${OLLAMA_HOST:-"http://127.0.0.1:11434"}

# Flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    --models)        MODEL_LIST="$2"; shift 2;;
    --embed-model)   EMBED_MODEL="${2:-}"; shift 2;;
    --prompt-file)   PROMPT_FILE="$2"; shift 2;;
    --reps)          REPS="$2"; shift 2;;
    --concurrency)   CONCURRENCY="$2"; shift 2;;
    --json)          USE_JSON="true"; shift 1;;
    --no-json)       USE_JSON="false"; shift 1;;
    --host)          OLLAMA_HOST="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 2;;
  esac
done

echo "[warmup] OLLAMA_HOST=${OLLAMA_HOST}"
echo "[warmup] MODELS=${MODEL_LIST}  EMBED_MODEL=${EMBED_MODEL:-none}"
echo "[warmup] PROMPT_FILE=${PROMPT_FILE}  REPS=${REPS}  CONCURRENCY=${CONCURRENCY}  JSON=${USE_JSON}"

# --- Ensure Ollama server is running ---
check_ollama() {
  curl -sS "${OLLAMA_HOST}/api/tags" >/dev/null 2>&1
}

if ! check_ollama; then
  echo "[warmup] starting ollama serve ..."
  # Run in background if not already running
  nohup ollama serve >/tmp/ollama-serve.log 2>&1 &
  # Wait for readiness
  for i in {1..60}; do
    if check_ollama; then
      echo "[warmup] ollama is ready"
      break
    fi
    sleep 1
  done
  if ! check_ollama; then
    echo "[warmup] ERROR: ollama did not become ready on ${OLLAMA_HOST}" >&2
    exit 1
  fi
else
  echo "[warmup] ollama is already running"
fi

# --- Pull models if needed ---
IFS=',' read -r -a MODELS <<< "${MODEL_LIST}"
for m in "${MODELS[@]}"; do
  if ! ollama list | awk '{print $1}' | grep -q "^${m}$"; then
    echo "[warmup] pulling ${m} ..."
    ollama pull "${m}"
  else
    echo "[warmup] model present: ${m}"
  fi
done

if [[ -n "${EMBED_MODEL}" ]]; then
  if ! ollama list | awk '{print $1}' | grep -q "^${EMBED_MODEL}$"; then
    echo "[warmup] pulling embed model ${EMBED_MODEL} ..."
    ollama pull "${EMBED_MODEL}"
  else
    echo "[warmup] embed model present: ${EMBED_MODEL}"
  fi
fi

# --- Delegate warmups to Python (JSON path + standard path + embeddings) ---
PYTHON=${PYTHON:-python3}
exec "${PYTHON}" "$(dirname "$0")/warmup_model.py" \
  --host "${OLLAMA_HOST}" \
  --models "${MODEL_LIST}" \
  ${EMBED_MODEL:+--embed-model "${EMBED_MODEL}"} \
  --prompt-file "${PROMPT_FILE}" \
  --reps "${REPS}" \
  --concurrency "${CONCURRENCY}" \
  --json "${USE_JSON}"
