#!/usr/bin/env bash
# Health check for the Groq setup used by Labs 3 and 4.
# Usage:  bash scripts/check-groq.sh
set -uo pipefail

# The model each lab uses, and what to try if it is not available.
# Lab 3 has no hosted stand-in: the other Groq models cannot drive a smolagents
# CodeAgent. The lab falls back to the local model by itself, so there is nothing
# to export - hence no alternates listed here.
LAB3_MODEL="${LAB3_MODEL:-qwen/qwen3.6-27b}"      # Lab 3 - smolagents CodeAgent
LAB3_ALTERNATES=""
LAB3_NOTE="      Nothing to do - Lab 3 detects this and uses the local model instead."
LAB4_MODEL="${LAB4_MODEL:-openai/gpt-oss-120b}"   # Lab 4 - native tool calling
LAB4_ALTERNATES="openai/gpt-oss-20b"
LAB4_NOTE="      No hosted alternative responded. Run the lab without Groq instead:
          unset AGENT_PROVIDER
      It will use the local model - slower, but it works."

echo "AGENT_PROVIDER = ${AGENT_PROVIDER:-<unset>}"
if [ -z "${GROQ_API_KEY:-}" ]; then
  echo "GROQ_API_KEY   = MISSING"
  echo
  echo "Run 'source scripts/setup-key.sh' first (README steps 4 and 5)."
  exit 1
fi
echo "GROQ_API_KEY   = set (${#GROQ_API_KEY} chars)"
echo

echo "Models your key can reach right now:"
curl -sS https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" \
| python3 -c '
import sys, json
try:
    data = json.load(sys.stdin).get("data", [])
except Exception:
    print("  could not read the model list - check your key"); sys.exit(1)
for m in sorted(d["id"] for d in data):
    print("  " + m)
' || { echo "  request failed - check network or key"; exit 1; }
echo

ping_model() {
  local m="$1" code
  code=$(curl -sS -o /dev/null -w '%{http_code}' \
    https://api.groq.com/openai/v1/chat/completions \
    -H "Authorization: Bearer $GROQ_API_KEY" -H "Content-Type: application/json" \
    -d "{\"model\":\"$m\",\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}],\"max_tokens\":5}")
  [ "$code" = "200" ]
}

# Report on one lab's model, and if it is gone, name a replacement that was
# just verified to answer.
check_lab() {
  local lab="$1" primary="$2" alternates="$3" note="$4"
  if ping_model "$primary"; then
    echo "OK    Lab $lab  ->  $primary"
    return
  fi
  echo "FAIL  Lab $lab  ->  $primary is not available on your key"
  for alt in $alternates; do
    if ping_model "$alt"; then
      echo "      Use this instead, then re-run the lab:"
      echo "          export AGENT_MODEL=$alt"
      return
    fi
  done
  echo "$note"
}

check_lab 3 "$LAB3_MODEL" "$LAB3_ALTERNATES" "$LAB3_NOTE"
check_lab 4 "$LAB4_MODEL" "$LAB4_ALTERNATES" "$LAB4_NOTE"
