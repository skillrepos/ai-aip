#!/usr/bin/env bash
# Quick health check for the Groq setup used by Labs 3 and 4.
# Usage:  bash scripts/check-groq.sh
set -uo pipefail

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

# The two models the labs default to.
for MODEL in "qwen/qwen3.6-27b" "openai/gpt-oss-120b"; do
  CODE=$(curl -sS -o /tmp/_groqchk -w '%{http_code}' \
    https://api.groq.com/openai/v1/chat/completions \
    -H "Authorization: Bearer $GROQ_API_KEY" -H "Content-Type: application/json" \
    -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}],\"max_tokens\":5}")
  if [ "$CODE" = "200" ]; then
    echo "OK    $MODEL responds"
  else
    echo "FAIL  $MODEL -> HTTP $CODE"
    head -c 200 /tmp/_groqchk; echo
    echo "      If the model no longer exists, pick one from the list above and run:"
    echo "      export AGENT_MODEL=<model-id>"
  fi
done
