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

# Set for current terminal
export AGENT_PROVIDER=groq
export GROQ_API_KEY="$KEY"

# Set for all future terminals (avoid duplicates)
grep -q "^export AGENT_PROVIDER=" ~/.bashrc 2>/dev/null && \
  sed -i 's/^export AGENT_PROVIDER=.*/export AGENT_PROVIDER=groq/' ~/.bashrc || \
  echo 'export AGENT_PROVIDER=groq' >> ~/.bashrc

grep -q "^export GROQ_API_KEY=" ~/.bashrc 2>/dev/null && \
  sed -i "s/^export GROQ_API_KEY=.*/export GROQ_API_KEY=$KEY/" ~/.bashrc || \
  echo "export GROQ_API_KEY=$KEY" >> ~/.bashrc

echo "Done! AGENT_PROVIDER and GROQ_API_KEY are set."