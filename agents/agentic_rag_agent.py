#!/usr/bin/env python3
"""
Lab 4 - Agentic RAG (TRUE, model-driven via native tool-calling)  [SKELETON]
============================================================================
This is the SKELETON. In the lab you'll diff/merge against the completed
reference (../extra/agentic_rag_agent.txt) and merge in FOUR sections, each
marked below with a ">>>>> MERGE SECTION N" banner:
  1. The tools the agent can call (+ a RAG grounding helper)
  2. The tool schemas (what enables native tool-calling) + the system prompt
  3. The self-check / validation gate
  4. The agent loop (model decides -> calls tools -> observes -> validates)

When it runs, lines tagged [AGENT], [RAG], [GROUND], [SELF-CHECK] show the
agent's decisions, retrievals, grounding checks, retries, and validation live.

Model provider: default local Ollama (llama3.2). For TRUE, reliable agentic
RAG, create a free key at console.groq.com and run:
    export AGENT_PROVIDER=groq
    export GROQ_API_KEY=<your-key>
"""

import os
import re
import json
import math
import requests
from openai import OpenAI
import chromadb
import pdfplumber
from chromadb.utils import embedding_functions

_E = chr(27)
GREEN, CYAN, YELLOW, RED, BLUE, BOLD, RESET = (
    _E + "[92m", _E + "[96m", _E + "[93m", _E + "[91m", _E + "[94m", _E + "[1m", _E + "[0m")

STARTING_LOC_FILE = "user_starting_location.json"
DEFAULT_LOCATION = {"city": "Raleigh, NC", "lat": 35.7796, "lon": -78.6382}

# --- Model provider toggle (default local Ollama; AGENT_PROVIDER=groq for Groq) ---
PROVIDER = os.environ.get("AGENT_PROVIDER", "ollama").strip().lower()
GROQ_KEY = (os.environ.get("GROQ_API_KEY") or "").strip()
USE_GROQ = (PROVIDER == "groq" and GROQ_KEY)
if PROVIDER == "groq" and not GROQ_KEY:
    print(f"{BOLD}{RED}[AGENT] AGENT_PROVIDER=groq but GROQ_API_KEY is NOT set in this "
          f"environment (did you EXPORT it?). Falling back to local Ollama.{RESET}")
if USE_GROQ:
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_KEY)
    MODEL = os.environ.get("AGENT_MODEL", "llama-3.1-8b-instant").strip()
else:
    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    MODEL = os.environ.get("AGENT_MODEL", "llama3.2").strip()
print(f"{BOLD}{CYAN}[AGENT] provider={'groq' if USE_GROQ else 'ollama'}  model={MODEL}{RESET}")


# --- Given helpers (already in the skeleton): live geocoding + distance math ---
def geocode_location(q):
    try:
        r = requests.get(
            f"https://nominatim.openstreetmap.org/search?q={q}&format=json",
            headers={"User-Agent": "TravelAssistant/1.0"}, timeout=15)
        g = r.json()
        if g:
            return float(g[0]["lat"]), float(g[0]["lon"])
    except Exception as e:
        print(f"{RED}[geocode] error: {e}{RESET}")
    return None, None


def haversine_miles(a, b, c, d):
    R = 3958.8
    dlat, dlon = math.radians(c - a), math.radians(d - b)
    h = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(a)) * math.cos(math.radians(c)) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# >>>>> MERGE SECTION 1: THE TOOLS THE AGENT CAN CALL (+ grounding helper) <<<<<
#   MERGE IN: search_documents (RAG retrieval, re-callable with a better query),
#   _resolve_place (RAG GROUNDING CHECK - office name -> real city, or not_found),
#   distance_to, city_facts, and the DISPATCH map (tool name -> function).
#   Each tool prints a [RAG]/[GROUND] debug line so you can watch it work.
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# TODO (merge): tool_search_documents, _resolve_place, tool_distance_to,
#               tool_city_facts, and DISPATCH
DISPATCH = {}
# >>>>> END MERGE SECTION 1 <<<<<


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# >>>>> MERGE SECTION 2: TOOL SCHEMAS (enable native tool-calling) + SYSTEM <<<<<
#   MERGE IN: TOOLS_SCHEMA (the JSON function schemas passed via tools=..., which
#   is what makes the model emit reliable structured tool calls) and SYSTEM (tell
#   the model to retrieve first, decompose multi-part questions, only answer when
#   grounded, else decline).
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
TOOLS_SCHEMA = []          # TODO (merge): the 3 function schemas
SYSTEM = "TODO (merge)"    # TODO (merge): the system prompt
# >>>>> END MERGE SECTION 2 <<<<<


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# >>>>> MERGE SECTION 3: SELF-CHECK / VALIDATION GATE <<<<<
#   MERGE IN: validate_answer - an LLM "critic" that checks the draft answer is
#   grounded in the retrieved snippets; returns {"complete": bool, "missing": str}.
#   This gate decides whether the agent may finish or must keep going.
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def validate_answer(user_query, answer, state):
    # TODO (merge): build the validator prompt and return {"complete":..,"missing":..}
    return {"complete": True, "missing": ""}
# >>>>> END MERGE SECTION 3 <<<<<


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# >>>>> MERGE SECTION 4: THE AGENT LOOP (the model drives this) <<<<<
#   MERGE IN: run_agent - each turn the MODEL decides: call tools (then we run
#   them via DISPATCH, feed results back, and loop) or give a final answer (then
#   we run the SELF-CHECK; if not grounded, tell it what's missing and loop;
#   else print the FINAL ANSWER). max_steps is the safety cap.
#   It prints [AGENT] decision / [observation] / [SELF-CHECK] lines as it runs.
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def run_agent(user_query, start, max_steps=12, max_revalidations=2):
    # TODO (merge): implement the model-driven tool-calling loop with the
    # FINISH -> validate -> retry gate described above.
    pass
# >>>>> END MERGE SECTION 4 <<<<<


# --- Given (already in the skeleton): starting-location helpers ---
def load_starting_location():
    if os.path.exists(STARTING_LOC_FILE):
        try:
            with open(STARTING_LOC_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_LOCATION


def set_starting_location_interactively():
    cur = load_starting_location()
    print(f"{CYAN}Current starting location: {cur['city']}{RESET}")
    if input("Change your starting location? (y/n): ").strip().lower() == "y":
        c = input("Enter new starting city: ").strip()
        lat, lon = geocode_location(c)
        if lat is not None:
            cur = {"city": c, "lat": lat, "lon": lon}
            with open(STARTING_LOC_FILE, "w") as f:
                json.dump(cur, f)
    return cur


# --- Given (already in the skeleton): index the office PDF into ChromaDB ---
print("Loading and indexing PDF into ChromaDB...")
pdf_text = ""
with pdfplumber.open("../data/offices.pdf") as pdf:
    for page in pdf.pages:
        pdf_text += (page.extract_text() or "") + chr(10)
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(
    name="office_docs_agentic",
    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2"))
docs = [ln.strip() for ln in pdf_text.split(chr(10)) if len(ln.strip()) > 20]
collection.add(documents=docs, ids=[f"doc_{i}" for i in range(len(docs))])
print(f"{GREEN}Indexed {len(docs)} office documents.{RESET}")


if __name__ == "__main__":
    start = set_starting_location_interactively()
    print("Agentic Travel Assistant ready! (Type 'exit' to quit)")
    print("Try: 'Tell me about HQ'  or  'Which is closer to me, HQ or the Eastern office?'")
    while True:
        q = input(f"{BOLD}User:{RESET} ").strip()
        if q.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        run_agent(q, start)
