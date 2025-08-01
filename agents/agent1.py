# weather-agent with TAO – day-forecast + interactive loop + full tracing

import json
import requests
import textwrap
from langchain_ollama import ChatOllama

# ── 1. Open-Meteo weather-code lookup ──────────────────────────────────────
WEATHER_CODES = {
    0:  "Clear sky",                     1:  "Mainly clear",
    2:  "Partly cloudy",                 3:  "Overcast",
    45: "Fog",                           48: "Depositing rime fog",
    51: "Light drizzle",                 53: "Moderate drizzle",
    55: "Dense drizzle",                 56: "Light freezing drizzle",
    57: "Dense freezing drizzle",        61: "Slight rain",
    63: "Moderate rain",                 65: "Heavy rain",
    66: "Light freezing rain",           67: "Heavy freezing rain",
    71: "Slight snow fall",              73: "Moderate snow fall",
    75: "Heavy snow fall",               77: "Snow grains",
    80: "Slight rain showers",           81: "Moderate rain showers",
    82: "Violent rain showers",          85: "Slight snow showers",
    86: "Heavy snow showers",            95: "Thunderstorm",
    96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}

# ── 2. Tools ───────────────────────────────────────────────────────────────
def get_weather(lat: float, lon: float) -> dict:
    """
    Return today's forecast:
        { "high": °C, "low": °C, "conditions": str }
    """
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&daily=weathercode,temperature_2m_max,temperature_2m_min"
        "&forecast_days=1&timezone=auto"
    )
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    daily = r.json()["daily"]
    return {
        "high":       daily["temperature_2m_max"][0],
        "low":        daily["temperature_2m_min"][0],
        "conditions": WEATHER_CODES.get(daily["weathercode"][0], "Unknown"),
    }

def convert_c_to_f(c: float) -> float:
    return c * 9 / 5 + 32

# ── 3. LLM client ───────────────────────────────────────────────────────────
llm = ChatOllama(model="llama3.2", temperature=0.0)

# ── 4. System prompt ────────────────────────────────────────────────────────
SYSTEM = textwrap.dedent("""
You are an agent with two tools:

get_weather(lat:float, lon:float)
    → {"high": float, "low": float, "conditions": str}

convert_c_to_f(c:float) → float

When you plan, emit exactly:
Summary: summary of your finding and country of the city
Thought: <your thought>
Action: <tool name>
Args: {"lat":X,"lon":Y}   or   {"c":Z}

Do NOT output anything else.
""").strip()

# ── 5. TAO run helper ───────────────────────────────────────────────────────
def run(question: str) -> str:
    """Execute the two-step TAO dance once, printing the trace, returning the answer."""
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user",   "content": question},
    ]

    print("\n--- Thought → Action → Observation → Final ---\n")

    # LLM chooses coordinates
    reply1 = llm.invoke(messages)
    plan1  = reply1.content.strip()
    print(f"plan1\n: {plan1}" + "\n")

    coords = json.loads(plan1.split("Args:")[1].strip())
    obs1   = get_weather(**coords)
    print(f"Observation: {obs1}\n")

    # LLM decides to convert °C → °F
    messages += [
        {"role": "assistant", "content": plan1},
        {"role": "user",      "content": f"Observation: {obs1}"}
    ]
    reply2 = llm.invoke(messages)
    plan2  = reply2.content.strip()
    print(plan2 + "\n")

    # Convert both temps
    high_f = convert_c_to_f(obs1["high"])
    low_f  = convert_c_to_f(obs1["low"])
    obs2   = {"high_f": high_f, "low_f": low_f}
    print(f"Observation: {obs2}\n")

    # Assemble final answer
    final = (
        f"Today will be **{obs1['conditions']}** with a high of "
        f"**{high_f:.1f} °F** and a low of **{low_f:.1f} °F**."
    )
    print(f"Final: {final}\n")
    return final

# ── 6. Interactive loop ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Weather-forecast agent (type 'exit' to quit)\n")
    while True:
        loc = input("Location (or 'exit'): ").strip()
        if loc.lower() == "exit":
            print("Goodbye!")
            break

        # Build the question for the agent
        query = (
            f"What is the predicted weather today for {loc}? "
            "Include conditions plus high/low in °F."
        )

        try:
            run(query)          # prints the entire trace internally
        except Exception as e:
            print(f"⚠️  Error: {e}\n")
