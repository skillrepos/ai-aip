#!/usr/bin/env python3
"""
Lab 2: TAO Agent with FastMCP Weather Server
────────────────────────────────────────────────────────────────────
A TRUE agentic implementation where the LLM dynamically selects which
tools to call and when to stop. This demonstrates:


Prerequisites: FastMCP weather server must be running on localhost:8000
"""

import asyncio
import json
import re
import textwrap
from typing import Optional, Dict, Any

from fastmcp import Client
from fastmcp.exceptions import ToolError
from langchain_ollama import ChatOllama

# ╔══════════════════════════════════════════════════════════════════╗
# ║ 1.  System prompt TEMPLATE                                       ║
# ╚══════════════════════════════════════════════════════════════════╝
SYSTEM_TEMPLATE = textwrap.dedent("""
You are a weather information agent.


IMPORTANT: When the observations already answer the user's question, stop calling
tools and respond with:
Thought: <why you are done>
Action: DONE
Args: {{}}

Rules:
- NEVER invent argument values (coordinates, IDs, codes). If you do not have a
  value yet, first call the tool that produces it.
- NEVER pass a tool's own output back into that same tool.
- Call each tool only once unless a genuinely new value needs it.
- As soon as the observations answer the question, reply with Action: DONE.

For each step where you need to call a tool, respond with EXACTLY three lines:

Thought: <your reasoning about what to do next>
Action: <exact tool name: {tool_names}, or DONE>
Args: <valid JSON arguments for the tool>

Examples (these show the FORMAT - use real values for the actual request):
{tool_examples}

Do NOT add extra text. Do NOT explain after your three lines.
""").strip()

# Regex patterns for parsing LLM responses
ACTION_RE = re.compile(r"Action:\s*(\w+)", re.IGNORECASE)
ARGS_RE = re.compile(r"Args:\s*(\{.*?\})(?:\s|$)", re.S | re.IGNORECASE)

# ╔══════════════════════════════════════════════════════════════════╗
# ║ 2.  Turn DISCOVERED MCP tools into prompt text                   ║
# ╚══════════════════════════════════════════════════════════════════╝

_SAMPLE_VALUES = {"string": '"example"', "number": "0.0",
                  "integer": "0", "boolean": "true"}


def _params(tool) -> dict:
    """Return the {name: schema} argument properties of an MCP tool."""
    schema = getattr(tool, "input_schema", None) or {}
    return schema.get("properties", {}) or {}


def _sample(prop: dict) -> str:
    """A placeholder value of the right JSON type, for the examples."""
    return _SAMPLE_VALUES.get(prop.get("type"), '"value"')


def format_tool_catalogue(tools) -> str:
    """Render discovered MCP tools as the tool list for the system prompt."""
    blocks = []
    for tool in tools:
        params = _params(tool)
        signature = ", ".join(f"{n}: {p.get('type', 'any')}" for n, p in params.items())
        block = [f"{tool.name}({signature})"]
        description = (tool.description or "").strip()
        if description:
            block.append(f"    {description.splitlines()[0]}")
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)


def _needs_lookup(tool) -> list[str]:
    """Names of this tool's numeric arguments - values only another tool can supply."""
    return [n for n, p in _params(tool).items() if p.get("type") in ("number", "integer")]


def format_tool_examples(tools) -> str:
    """Build one worked Thought/Action/Args example per discovered tool.

    Tools whose arguments are all text come first; tools that take numbers come
    after, because those numbers have to come from an earlier Observation. The
    order is derived from the schemas, so no tool is named here.
    """
    examples = []
    for tool in sorted(tools, key=lambda t: bool(_needs_lookup(t))):
        args = ", ".join(f'"{n}": {_sample(p)}' for n, p in _params(tool).items())
        needs = _needs_lookup(tool)
        thought = (f"I need to use {tool.name} - its {', '.join(needs)} must be copied "
                   f"from an earlier Observation" if needs
                   else f"I need to use {tool.name}")
        examples.append(f"Thought: {thought}\n"
                        f"Action: {tool.name}\n"
                        f"Args: {{{args}}}")
    return "\n\n".join(examples)



# ╔══════════════════════════════════════════════════════════════════╗
# ║ 3.  Robust unwrap helper                                         ║
# ╚══════════════════════════════════════════════════════════════════╝
# FastMCP wraps tool results in various formats depending on version.
# This helper extracts the actual Python value from any wrapper format.
def unwrap(obj):
    """Extract plain Python value from FastMCP wrapper objects."""
    if hasattr(obj, "structured_content") and obj.structured_content:
        return unwrap(obj.structured_content)
    if hasattr(obj, "data") and obj.data:
        return unwrap(obj.data)
    if hasattr(obj, "text"):
        try:
            return json.loads(obj.text)
        except Exception:
            return obj.text
    if hasattr(obj, "value"):
        return obj.value
    if isinstance(obj, list) and len(obj) == 1:
        return unwrap(obj[0])
    if isinstance(obj, dict):
        numeric_vals = [v for v in obj.values() if isinstance(v, (int, float))]
        if len(numeric_vals) == 1:
            return numeric_vals[0]
    return obj

# ╔══════════════════════════════════════════════════════════════════╗
# ║ 4.  LLM-based city extractor                                     ║
# ╚══════════════════════════════════════════════════════════════════╝
# Uses a separate LLM call to extract city names from natural language.
# This handles inputs like "What's the weather in Paris?" → "Paris"
extract_llm = ChatOllama(model="llama3.2", temperature=0.0)

def extract_city(prompt: str) -> Optional[str]:
    """Extract city name from natural language using LLM."""
    ask = (
        "Return ONLY the city name mentioned here (no country or state). "
        "If none, reply exactly 'NONE'.\n\n"
        + prompt
    )
    reply = extract_llm.invoke(ask).content.strip()
    return None if reply.upper() == "NONE" else reply

# ╔══════════════════════════════════════════════════════════════════╗
# ║ 5.  Dynamic TAO loop with LLM-controlled tool selection          ║
# ╚══════════════════════════════════════════════════════════════════╝
    llm = ChatOllama(model="llama3.2", temperature=0.0)

    async with Client("http://127.0.0.1:8000/mcp/") as mcp:


        print("\n" + "="*60)
        print("Dynamic TAO Agent - LLM Controls Tool Selection")
        print("="*60 + "\n")

        # What the agent has learned so far: (tool name, result) per call.
        # Deliberately NOT a fixed set of weather fields - the agent does not
        # know in advance which tools the server will advertise.
        gathered = []

        for step in range(1, max_steps + 1):
            print(f"[Step {step}]")


            # Small models sometimes plan several steps at once. Keep only the
            # FIRST Thought/Action/Args triple - the loop will ask again next turn.
            triples = response.split("Thought:")
            if len(triples) > 2:
                response = "Thought:" + triples[1].rstrip()
            print(response)

            else:
                print("\n❌ Error: Could not parse Action from LLM response")
                return


                if not gathered:
                    print("\nFinal Answer:\n  No tools were called, so there is nothing to report.")
                    return

                # Turn the collected results into one plain-English sentence. The
                # summariser sees ONLY the question and what the tools returned, so
                # this works for whatever tools the server happens to advertise.
                results = "\n".join(
                    f"{name} -> {json.dumps(value) if isinstance(value, dict) else value}"
                    for name, value in gathered)
                answer = llm.invoke(
                    f"Question: {question}\n\nTool results:\n{results}\n\n"
                    "Write ONE sentence answering the question. Include EVERY value "
                    "the tools returned that helps answer it - for a weather question "
                    "that means the conditions AND the temperature, not just one of "
                    "them. Use ONLY the numbers and words shown above, copied exactly - "
                    "never calculate anything yourself. Ignore any field named code. "
                    "A field name ending in _c is degrees Celsius.").content.strip()

                print("\nFinal Answer:")
                print(f"  {answer}")
                print(f"\n  (tools used: {', '.join(dict.fromkeys(n for n, _ in gathered))})")
                return

            # Only tools the server actually advertised can be called
            if action not in tool_names:
                print(f"\n⚠️  '{action}' was not discovered from the server; asking the LLM to retry")
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content":
                                 f"Observation: '{action}' is not an available tool. "
                                 f"Valid tools: {', '.join(sorted(tool_names))}, or DONE."})
                continue

            # Parse arguments
            args_match = ARGS_RE.search(response)
            if not args_match:
                print(f"\n❌ Error: Could not parse Args from LLM response")
                return

            try:
                args = json.loads(args_match.group(1))
            except json.JSONDecodeError as e:
                print(f"\n❌ Error: Invalid JSON in Args: {e}")
                return


            except ToolError as e:
                print(f"❌ MCP Error: {e}\n")
                # Add error to conversation and let LLM try to recover
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": f"Observation: Error calling {action} - {e}"})
                continue
            except Exception as e:
                print(f"❌ Unexpected Error: {type(e).__name__}: {e}\n")
                return

            # Handle tool-specific errors (e.g., geocoding failures)
            if isinstance(result, dict) and "error" in result:
                print(f"⚠️  Tool returned error: {result['error']}\n")
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": f"Observation: {result}"})
                continue

        # Max steps reached
        print(f"\n⚠️  Reached maximum steps ({max_steps}) without completion")
        print("Partial information gathered:")
        for name, value in gathered:
            print(f"  {name} -> {value}")

# ╔══════════════════════════════════════════════════════════════════╗
# ║ 6.  Interactive REPL                                             ║
# ╚══════════════════════════════════════════════════════════════════╝
if __name__ == "__main__":
    print("="*60)
    print("Dynamic Weather TAO Agent")
    print("="*60)
    print("\nThis agent uses LLM-controlled tool selection.")
    print("The LLM decides which tools to call and when to stop.\n")
    print("Type 'exit' to quit\n")

    while True:
        raw_prompt = input("Ask about the weather: ").strip()
        if raw_prompt.lower() == "exit":
            break

        city = extract_city(raw_prompt)
        if not city or len(city) < 3:
            print("❌ No city detected; please try again.\n")
            continue

        print(f"\n🔍 Detected city: {city}")
        asyncio.run(run_dynamic(city, raw_prompt))
        print()
