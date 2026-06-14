import subprocess
import tempfile
import os

from autogen import AssistantAgent

# ── Ollama config ──────────────────────────────────────────────
llm_config = {
    "config_list": [
        {
            "model": "llama3.2",
            "base_url": "http://localhost:11434/v1",
            "api_type": "ollama",
        }
    ],
    "temperature": 0.0,
}

# ── Agents ─────────────────────────────────────────────────────

# ── Code Cleanup ───────────────────────────────────────────────
def clean_code_block(code: str) -> str:
    lines = code.strip().splitlines()
    if lines and lines[0].strip().startswith("```"):
        return "\n".join(lines[1:-1])
    return code.strip()

# ── Runtime simulation ─────────────────────────────────────────

# ── Main loop ──────────────────────────────────────────────────
def main():
    print("Type a code request or 'exit' to quit.\n")

    while True:
        task = input("Request ➤ ").strip()
        if task.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        # Step 1: Generate initial code

        # Step 2: Simulate runtime of original

        # Step 3: Critique

        # Step 4: Fix and re-test if needed

if __name__ == "__main__":
    main()
