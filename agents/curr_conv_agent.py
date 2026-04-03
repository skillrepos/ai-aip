import os
import json
import re
import requests
from smolagents import CodeAgent, LiteLLMModel, tool

# -----------------------------------------------------------------------------
# MEMORY PERSISTENCE (with history)
# -----------------------------------------------------------------------------
MEMORY_FILE = "currency_memory.json"

def load_memory():
    """Load memory from disk, initializing history if missing."""
    if os.path.exists(MEMORY_FILE):
        mem = json.load(open(MEMORY_FILE))
        # Ensure history key exists
        if "history" not in mem:
            mem["history"] = []
        return mem
    # Default memory structure
    return {"last_amount": None, "last_from": None, "last_to": None, "history": []}

def save_memory(mem):
    """Persist memory (including history) back to disk."""
    with open(MEMORY_FILE, "w") as f:
        json.dump(mem, f)

memory = load_memory()

# -----------------------------------------------------------------------------
# SMOLAGENTS TOOLS
# -----------------------------------------------------------------------------

# tool to get rates from a URL
@tool
def fetch_live_rate(from_currency: str, to_currency: str) -> float:
    """
    Retrieve a live exchange rate from the fawazahmed0 Exchange API.

    Args:
        from_currency (str): 3-letter source code, e.g. "USD"
        to_currency   (str): 3-letter target code, e.g. "EUR"

    Returns:
        float: Target units per one source unit.

    Raises:
        RuntimeError: if the rate cannot be fetched.
    """
    base = from_currency.lower()
    target = to_currency.lower()
    urls = [
        f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest"
        f"/v1/currencies/{base}.json",
        f"https://latest.currency-api.pages.dev"
        f"/v1/currencies/{base}.json"
    ]
    for url in urls:
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            rates = data.get(base, {})
            if target in rates:
                return rates[target]
        except Exception:
            continue
    raise RuntimeError(f"Failed to fetch rate from {from_currency} to {to_currency}")


# tool to do basic calculations

@tool
def calculate(expression: str) -> float:
    """
    Evaluate a basic arithmetic expression safely.

    Args:
        expression (str): e.g. "100 * 0.85"

    Returns:
        float: numeric result.

    Raises:
        RuntimeError: if the expression is invalid.
    """
    try:
        return eval(expression, {"__builtins__": {}})
    except Exception as e:
        raise RuntimeError(f"Calculation error: {e}")

# -----------------------------------------------------------------------------
# AGENT CONFIGURATION
# -----------------------------------------------------------------------------

model = LiteLLMModel(
    model_id="ollama_chat/llama3.2",
    api_base="http://localhost:11434",
    num_ctx=4096,
    temperature=0.0,  # deterministic tool use
)

agent = CodeAgent(
    tools=[fetch_live_rate, calculate],
    model=model,
    add_base_tools=False
)

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

    # 1) Full form: amount + source + "to" + target
    m1 = re.match(r"(?:Convert\s+)?([\d.]+)\s*([A-Za-z]{3})\s+to\s+([A-Za-z]{3})$", q, re.IGNORECASE)
    if m1:
        amt, frm, to = m1.group(1), m1.group(2).upper(), m1.group(3).upper()
    else:
        # 2) Amount + source only
        m2 = re.match(r"(?:Convert\s+)?([\d.]+)\s*([A-Za-z]{3})$", q, re.IGNORECASE)
        if m2:
            amt, frm = m2.group(1), m2.group(2).upper()
            to = memory["last_to"]

        # 3) Amount + "to" + target only
        m3 = re.match(r"(?:Convert\s+)?([\d.]+)\s+to\s+([A-Za-z]{3})$", q, re.IGNORECASE)
        if m3:
            amt, to = m3.group(1), m3.group(2).upper()
            frm = memory["last_from"]

        # 4) Amount only
        m4 = re.match(r"(?:Convert\s+)?([\d.]+)$", q, re.IGNORECASE)
        if m4:
            amt = m4.group(1)
            frm = memory["last_from"]
            to  = memory["last_to"]

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

        if low in ("exit", "quit"):
            print("Goodbye!")
            break
        if low in ("history", "show history"):
            if not memory["history"]:
                print("No conversion history yet.\n")
            else:
                print("Conversion History:")
                for entry in memory["history"]:
                    print(f"  • {entry['query']} → {entry['result']:.2f}")
                print()
            continue

        # Normal convert request
        
        try:
            amt, frm, to = parse_and_fill(user_input)
            prompt = f"Convert {amt} {frm} to {to}"

            # Run the agent (LLM will call fetch_live_rate & calculate)
            result = agent.run(prompt)

            # Store and persist this interaction
            memory["history"].append({"query": user_input, "amount": amt,
                                      "from": frm, "to": to, "result": float(result)})
            save_memory(memory)

            # Friendly output
            print(f"{amt} {frm} is approximately {float(result):.2f} {to}.\n")

        except Exception as e:
            print(f"Error: {e}\n")
