#!/usr/bin/env bash
set -euo pipefail

# ---- Ensure prerequisites ----
install_zstd() {
  if command -v zstd >/dev/null 2>&1; then
    echo "zstd already installed"
    return
  fi

  echo "Installing zstd..."

  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y zstd curl ca-certificates
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y zstd curl ca-certificates
  elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y zstd curl ca-certificates
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --noconfirm zstd curl ca-certificates
  else
    echo "ERROR: Unsupported package manager. Install 'zstd' manually and rerun."
    exit 1
  fi
}

install_zstd

# ---- Install Ollama ----
echo "Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# Confirm binary is available
if ! command -v ollama >/dev/null 2>&1; then
  echo "ERROR: ollama is still not on PATH after install."
  echo "Try: ls -l /usr/local/bin/ollama && echo \$PATH"
  exit 1
fi

# ---- Start server ----
ollama serve >/tmp/ollama-serve.log 2>&1 &
pid=$!

# Wait for Ollama API to be reachable (default localhost:11434)
for _ in {1..300}; do
  if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    break
  fi
  sleep 0.1
done

# Sanity check
if ! curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "ERROR: ollama server did not start. Log:"
  tail -n 200 /tmp/ollama-serve.log || true
  kill "$pid" >/dev/null 2>&1 || true
  exit 1
fi

# ---- Pull model(s) ----
ollama pull llama3.2
ollama list

# ---- Stop server ----
kill "$pid" >/dev/null 2>&1 || true
wait "$pid" 2>/dev/null || true
