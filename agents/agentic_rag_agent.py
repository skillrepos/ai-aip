#!/usr/bin/env python3
"""
Lab 4 - Agentic RAG (model-driven, via native tool-calling)

The MODEL drives the loop: using native tool-calling it decides which tools to
call, retrieves as needed, grounds office names to real cities, and a self-check
gate verifies the answer is grounded before finishing.

You build this file with the diff/merge step. FOUR sections are merged in, each
marked with a ">>>>> MERGE SECTION N" banner:
  1. Tools the agent can call (+ a grounding helper)
  2. Tool schemas (these enable native tool-calling) + the system prompt
  3. The self-check gate
  4. The agent loop

Watch the run: lines tagged [AGENT], [RAG], [GROUND], [SELF-CHECK] show what the
agent is doing at each step.

Model: defaults to local Ollama (llama3.2). For reliable agentic RAG use Groq:
    export AGENT_PROVIDER=groq
    export GROQ_API_KEY=<your-key>
"""

import os, re, json, math, requests
from openai import OpenAI
import chromadb, pdfplumber
from chromadb.utils import embedding_functions

DEFAULT_LOCATION = {"city": "Raleigh, NC", "lat": 35.7796, "lon": -78.6382}

# --- Model provider: Groq if AGENT_PROVIDER=groq and GROQ_API_KEY are exported, else local Ollama ---
USE_GROQ = os.environ.get("AGENT_PROVIDER", "").strip().lower() == "groq" and os.environ.get("GROQ_API_KEY", "").strip()
if USE_GROQ:
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ["GROQ_API_KEY"].strip())
    MODEL = os.environ.get("AGENT_MODEL", "llama-3.1-8b-instant").strip()
else:
    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    MODEL = os.environ.get("AGENT_MODEL", "llama3.2").strip()
print(f"[AGENT] provider={'groq' if USE_GROQ else 'ollama'}  model={MODEL}")


def geocode(city):
    """Look up (lat, lon) for a city name via OpenStreetMap."""
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search",
                         params={"q": city, "format": "json"},
                         headers={"User-Agent": "TravelAssistant/1.0"}, timeout=15).json()
        if r:
            return float(r[0]["lat"]), float(r[0]["lon"])
    except Exception as e:
        print(f"[geocode] error: {e}")
    return None, None


def haversine_miles(lat1, lon1, lat2, lon2):
    """Straight-line distance between two lat/lon points, in miles."""
    R = 3958.8
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    h = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))


# >>>>> MERGE SECTION 1: tools the agent can call (+ grounding helper) >>>>>
# TODO (merge): search_documents, ground_office, distance_to, city_facts, and DISPATCH
DISPATCH = {}
# >>>>> END MERGE SECTION 1 >>>>>


# >>>>> MERGE SECTION 2: tool schemas (enable native tool-calling) + system prompt >>>>>
# TODO (merge): TOOLS_SCHEMA (the JSON function schemas) and SYSTEM (the prompt)
TOOLS_SCHEMA = []
SYSTEM = "TODO (merge)"
# >>>>> END MERGE SECTION 2 >>>>>


# >>>>> MERGE SECTION 3: self-check gate >>>>>
# TODO (merge): return {"complete": bool, "missing": str} from a simple check
def validate_answer(answer, state):
    return {"complete": True, "missing": ""}
# >>>>> END MERGE SECTION 3 >>>>>


# >>>>> MERGE SECTION 4: the agent loop (the MODEL drives it) >>>>>
# TODO (merge): run_agent - the model decides each step (call tools, or final answer)
def run_agent(user_query, start, max_steps=8):
    pass
# >>>>> END MERGE SECTION 4 >>>>>


# --- Given: starting location + index the office PDF into ChromaDB ---
def get_start():
    loc = DEFAULT_LOCATION
    if os.path.exists("user_starting_location.json"):
        try:
            loc = json.load(open("user_starting_location.json"))
        except Exception:
            pass
    print(f"Starting location: {loc['city']}")
    if input("Change it? (y/n): ").strip().lower() == "y":
        city = input("New starting city: ").strip()
        lat, lon = geocode(city)
        if lat is not None:
            loc = {"city": city, "lat": lat, "lon": lon}
            json.dump(loc, open("user_starting_location.json", "w"))
    return loc


print("Indexing offices.pdf into ChromaDB...")
text = ""
with pdfplumber.open("../data/offices.pdf") as pdf:
    for page in pdf.pages:
        text += (page.extract_text() or "") + "\n"
collection = chromadb.Client().get_or_create_collection(
    name="office_docs_agentic",
    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2"))
docs = [line.strip() for line in text.split("\n") if len(line.strip()) > 20]
collection.add(documents=docs, ids=[f"doc_{i}" for i in range(len(docs))])
print(f"Indexed {len(docs)} office lines.\n")


if __name__ == "__main__":
    start = get_start()
    print("Agentic RAG assistant ready. Try: 'Tell me about HQ'   (type 'exit' to quit)")
    while True:
        q = input("\nUser: ").strip()
        if q.lower() in ("exit", "quit"):
            break
        run_agent(q, start)
