import subprocess
import tempfile
import os

from autogen import AssistantAgent

# ── Model provider (Groq if AGENT_PROVIDER=groq + GROQ_API_KEY set; else local Ollama) ──
# >>>>> MERGE NOTE (Lab 6 model provider): build_llm_config() lets the
# writer/critic/fixer reflection loop run on the stronger hosted Groq model for
# more reliable critiques and fixes, while still defaulting to local Ollama. If
# AGENT_PROVIDER=groq AND GROQ_API_KEY are set we use Groq; if either is unset we
# transparently fall back to local Ollama.
def build_llm_config():
    """Return the AutoGen llm_config the agents reason with.

    Default: local Ollama (llama3.2). Set AGENT_PROVIDER=groq and GROQ_API_KEY to
    use the hosted Groq model instead (stronger reasoning). Optionally override
    the model name with AGENT_MODEL. Unset vars -> local Ollama fallback.
    """
    provider = os.environ.get("AGENT_PROVIDER", "").lower()
    groq_key = os.environ.get("GROQ_API_KEY")
    if provider == "groq" and groq_key:
        model_name = os.environ.get("AGENT_MODEL", "llama-3.1-8b-instant")
        print(f"[MODEL] provider=groq  model={model_name}")
        return {
            "config_list": [
                {
                    "model": model_name,
                    "base_url": "https://api.groq.com/openai/v1",
                    "api_key": groq_key,
                    "api_type": "openai",
                }
            ],
            "temperature": 0.0,
        }
    print("[MODEL] provider=ollama  model=llama3.2  "
          "(set AGENT_PROVIDER=groq and GROQ_API_KEY to use hosted Groq)")
    return {
        "config_list": [
            {
                "model": "llama3.2",
                "base_url": "http://localhost:11434/v1",
                "api_type": "ollama",
            }
        ],
        "temperature": 0.0,
    }

llm_config = build_llm_config()

# ── Agents ─────────────────────────────────────────────────────

# ── Code Cleanup ───────────────────────────────────────────────
def clean_code_block(code: str) -> str:
    lines = code.strip().splitlines()
    if lines and lines[0].strip().startswith("```"):
        return "\n".join(lines[1:-1])
    return code.strip()

def reply_text(reply):
    """AutoGen generate_reply() returns a dict on some providers (Ollama) and a
    plain string on others (OpenAI-compatible, e.g. Groq). Normalize to text."""
    if isinstance(reply, dict):
        return reply.get("content", "")
    return reply if reply is not None else ""

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
