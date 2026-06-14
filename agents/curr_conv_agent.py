import os
import json
import re
import requests
from smolagents import CodeAgent, LiteLLMModel, tool

# -----------------------------------------------------------------------------
# MEMORY PERSISTENCE (with history)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# SMOLAGENTS TOOLS
# -----------------------------------------------------------------------------

# tool to get rates from a URL


# tool to do basic calculations


# -----------------------------------------------------------------------------
# AGENT CONFIGURATION
# -----------------------------------------------------------------------------
# >>>>> MERGE NOTE (Lab 3 model provider): build_model() lets this lab run on the
# stronger hosted Groq model for better code-writing/tool selection, while still
# defaulting to local Ollama. If AGENT_PROVIDER=groq AND GROQ_API_KEY are set we
# use Groq; if either is unset we transparently fall back to local Ollama.
def build_model():
    """Return the LLM the CodeAgent reasons with.

    Default: local Ollama (llama3.2). Set AGENT_PROVIDER=groq and GROQ_API_KEY to
    use the hosted Groq model instead (stronger reasoning). Optionally override
    the model name with AGENT_MODEL. Unset vars -> local Ollama fallback.
    """
    provider = os.environ.get("AGENT_PROVIDER", "").lower()
    groq_key = os.environ.get("GROQ_API_KEY")
    if provider == "groq" and groq_key:
        model_name = os.environ.get("AGENT_MODEL", "llama-3.1-8b-instant")
        if not model_name.startswith("groq/"):
            model_name = "groq/" + model_name
        print(f"[MODEL] provider=groq  model={model_name}")
        return LiteLLMModel(model_id=model_name, api_key=groq_key, temperature=0.0)
    print("[MODEL] provider=ollama  model=ollama_chat/llama3.2  "
          "(set AGENT_PROVIDER=groq and GROQ_API_KEY to use hosted Groq)")
    return LiteLLMModel(
        model_id="ollama_chat/llama3.2",
        api_base="http://localhost:11434",
        num_ctx=4096,
        temperature=0.0,  # deterministic tool use
    )

model = build_model()


# -----------------------------------------------------------------------------
# QUERY PARSING + FILLING from MEMORY
# -----------------------------------------------------------------------------

def parse_and_fill(query: str):
    """
    Parse user input and fill missing pieces from memory.
    Supports:
      1. "Convert 100 USD to EUR"              → amt, src, tgt
      2. "400 JPY" or "Convert 400 JPY"         → amt, new src, reuse last_to
      3. "Convert 400 to GBP"                  → amt, reuse last_from, new tgt
      4. "200" or "Convert 200"                 → amt only, reuse both last_from & last_to
    Updates memory on success.
    """
    q = query.strip()
    amt = frm = to = None
 

    if not (amt and frm and to):
        raise ValueError(
            "Could not parse query. Examples:\n"
            "  • Convert 100 USD to EUR\n"
            "  • 400 JPY\n"
            "  • Convert 400 to GBP\n"
            "  • 200"
        )

    # Persist the new context
    memory.update({"last_amount": amt, "last_from": frm, "last_to": to})
    save_memory(memory)
    return amt, frm, to

# -----------------------------------------------------------------------------
# INTERACTIVE LOOP + HISTORY DISPLAY
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    banner = (
        "Currency Converter Agent with Memory & History\n"
        "(type 'exit' to quit, 'history' to show past conversions)\n"
    )
    print(banner)

    while True:
        user_input = input("Enter conversion query: ").strip()
        low = user_input.lower()

        # Handle special commands - exit and history


        # Normal convert request
        
        try:
            amt, frm, to = parse_and_fill(user_input)
            prompt = f"Convert {amt} {frm} to {to}"

            # Run the agent (LLM will call fetch_live_rate & calculate)
         

            # Store and persist this interaction

            # Friendly output
            print(f"{amt} {frm} is approximately {float(result):.2f} {to}.\n")

        except Exception as e:
            print(f"Error: {e}\n")
