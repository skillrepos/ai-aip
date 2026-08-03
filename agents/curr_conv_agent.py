import os
import json
import re
import time
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
# RATE-LIMIT BACKOFF (given code - already merged for you)
# -----------------------------------------------------------------------------
# Groq's free tier caps this model at 8,000 tokens per minute. A CodeAgent re-sends
# the whole conversation on every step, so one ordinary multi-step run can reach
# that ceiling by itself and die partway through with a RateLimitError.
#
# The cap is a rolling one-minute window and Groq's reply tells us exactly how long
# to wait ("Please try again in 19.2075s"), so the cure is simply to wait and
# re-issue the SAME request. We retry inside the model wrapper rather than around
# agent.run() on purpose: this way the agent keeps the steps it already completed,
# instead of starting over and spending those tokens a second time.

RATE_LIMIT_WAITS = 5           # how many times we're willing to wait it out
DEFAULT_WAIT_SECONDS = 20.0    # used only if the reply doesn't name a wait time


def is_rate_limit_error(err):
    """True for a provider throttle - as opposed to a real failure worth surfacing."""
    if type(err).__name__ == "RateLimitError":
        return True
    text = str(err).lower()
    return "rate_limit_exceeded" in text or "ratelimiterror" in text


def is_daily_limit(err):
    """Per-day quotas don't clear in a minute, so waiting on them is pointless."""
    text = str(err).lower()
    return "per day" in text or "(tpd)" in text or "(rpd)" in text


def seconds_to_wait(err):
    """Pull the wait time Groq suggests out of its own error message."""
    found = re.search(r"try again in ([\d.]+)\s*s", str(err), re.IGNORECASE)
    return float(found.group(1)) + 1.0 if found else DEFAULT_WAIT_SECONDS


class RateLimitRetryModel(LiteLLMModel):
    """A LiteLLMModel that waits out a rate limit instead of failing the run."""

    def generate(self, *args, **kwargs):
        for attempt in range(RATE_LIMIT_WAITS + 1):
            try:
                return super().generate(*args, **kwargs)
            except Exception as err:
                out_of_tries = attempt == RATE_LIMIT_WAITS
                if out_of_tries or is_daily_limit(err) or not is_rate_limit_error(err):
                    raise
                wait = seconds_to_wait(err)
                print(f"[RATE LIMIT] Free-tier tokens-per-minute cap reached. "
                      f"Waiting {wait:.0f}s, then retrying this step "
                      f"({attempt + 1} of {RATE_LIMIT_WAITS}).")
                time.sleep(wait)

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
    provider = os.environ.get("AGENT_PROVIDER", "").strip().lower()
    groq_key = (os.environ.get("GROQ_API_KEY") or "").strip()
    if provider == "groq" and groq_key:
        model_name = os.environ.get("AGENT_MODEL", "qwen/qwen3.6-27b").strip()
        if not model_name.startswith("groq/"):
            model_name = "groq/" + model_name
        print(f"[MODEL] provider=groq  model={model_name}")
        return RateLimitRetryModel(model_id=model_name, api_key=groq_key, temperature=0.0)
    print(f"[MODEL] provider=ollama  model=ollama_chat/llama3.2  "
          f"(AGENT_PROVIDER={provider!r}, GROQ_API_KEY={'set' if groq_key else 'NOT set'}; "
          f"to use Groq you must EXPORT both: export AGENT_PROVIDER=groq; export GROQ_API_KEY=...)")
    return RateLimitRetryModel(
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

