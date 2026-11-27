# weather-agent with TAO – AI-driven tool selection + interactive loop + full tracing

import json
import requests
import textwrap
import time
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

    # Retry up to 3 times
    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            daily = r.json()["daily"]
            return {
                "high":       daily["temperature_2m_max"][0],
                "low":        daily["temperature_2m_min"][0],
                "conditions": WEATHER_CODES.get(daily["weathercode"][0], "Unknown"),
            }
        except (requests.Timeout, requests.ConnectionError) as e:
            if attempt == max_retries - 1:
                raise  # Re-raise on final attempt
            print(f"  ⚠️  Retry {attempt + 1}/{max_retries - 1} after timeout...")
            time.sleep(2)  # Wait 2 seconds before retrying

# ── 3. Tool registry ────────────────────────────────────────────────────────


# ── 4. LLM client ───────────────────────────────────────────────────────────
llm = ChatOllama(model="llama3.2", temperature=0.0)

# ── 5. System prompt ────────────────────────────────────────────────────────
SYSTEM = textwrap.dedent("""
You are a weather agent with one tool:

""").strip()

# ── 6. TAO run helper ───────────────────────────────────────────────────────
def run(question: str) -> str:
   

    print("\n--- Thought → Action → Observation loop ---\n")

    max_iterations = 5  # Safety limit
    for i in range(max_iterations):
 

        # Check if AI is done
        if "Final:" in response:
            # Extract and return the final answer
            final = response.split("Final:")[1].strip()
            return final

        # Parse and execute the tool call
        if "Action:" in response and "Args:" in response:
            try:
                # Extract action and args
                action_line = response.split("Action:")[1].split("\n")[0].strip()
                args_text = response.split("Args:")[1].split("\n")[0].strip()

                # Get the tool function

                if tool_func is None:
                    print(f"⚠️  Unknown tool: '{tool_name}'\n")
                    print(f"Available tools: {list(TOOLS.keys())}\n")
                    break

                # Parse arguments and call the tool

                print(f"Observation: {observation}\n")

                # Add to conversation history

            except json.JSONDecodeError as e:
                print(f"⚠️  Failed to parse Args as JSON: {e}\n")
                print(f"Args text was: {args_text}\n")
                break
            except Exception as e:
                print(f"⚠️  Error executing tool: {e}\n")
                break
        else:
            print("⚠️  AI response missing Action/Args format\n")
            print(f"Expected format:\nThought: ...\nAction: <tool_name>\nArgs: <json>\n")
            print(f"Got:\n{response[:200]}...\n")
            break

    return "Sorry, I couldn't complete the task."

# ── 7. Interactive loop ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Weather-forecast agent (type 'exit' to quit)\n")
    while True:
        loc = input("Location (or 'exit'): ").strip()
        if loc.lower() == "exit":
            print("Goodbye!")
            break

        # Build the question for the agent
        query = f"What is the predicted weather today for {loc}?"

        try:
            answer = run(query)
            print(f"\n✓ {answer}\n")
        except Exception as e:
            print(f"⚠️  Error: {e}\n")