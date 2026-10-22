#!/bin/bash

# Setup script for Groq API key configuration

if [ -n "$1" ]; then
  KEY="$1"
else
  read -rp "Enter your Groq API key: " KEY
fi

if [ -z "$KEY" ]; then
  echo "Error: No key provided. Exiting."
  exit 1
fi

# Remember whether the key already arrived from the environment (for example a
# Codespace secret) before this script sets it for the current terminal.
PREEXISTING_KEY="${GROQ_API_KEY:-}"

# Set for current terminal
export AGENT_PROVIDER=groq
export GROQ_API_KEY="$KEY"

# Set for all future terminals (avoid duplicates)
grep -q "^export AGENT_PROVIDER=" ~/.bashrc 2>/dev/null && \
  sed -i 's/^export AGENT_PROVIDER=.*/export AGENT_PROVIDER=groq/' ~/.bashrc || \
  echo 'export AGENT_PROVIDER=groq' >> ~/.bashrc

if grep -q "^export GROQ_API_KEY=" ~/.bashrc 2>/dev/null; then
  # A previous run of this script wrote the key here - replace it (key rotation).
  sed -i "s/^export GROQ_API_KEY=.*/export GROQ_API_KEY=$KEY/" ~/.bashrc
elif [ -n "$PREEXISTING_KEY" ]; then
  # The key already comes from the environment itself (for example a Codespace
  # secret). Don't copy it into ~/.bashrc, where a stale copy would silently
  # shadow a rotated secret in every future terminal.
  echo "Note: GROQ_API_KEY already comes from your environment, so it was not"
  echo "written to ~/.bashrc. It is set for this terminal."
else
  echo "export GROQ_API_KEY=$KEY" >> ~/.bashrc
fi

echo "Done! AGENT_PROVIDER and GROQ_API_KEY are set."