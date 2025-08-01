# weather_server.py  – returns temperature *and* conditions

from fastmcp import FastMCP
import requests

# ── Weather-code → description table ───────────────────────────────────────
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

# ── Instantiate the MCP server ─────────────────────────────────────────────
mcp = FastMCP("WeatherServer")

# ── Register tools ─────────────────────────────────────────────────────────
@mcp.tool
def get_weather(lat: float, lon: float) -> dict:
    """
    Current conditions via Open-Meteo.

        {
            "temperature": °C,
            "code":        int,   # Open-Meteo weathercode
            "conditions":  str    # human-readable description
        }
    """
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&current_weather=true"
    )
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    cw   = resp.json()["current_weather"]

    code = cw["weathercode"]
    return {
        "temperature": cw["temperature"],
        "code":        code,
        "conditions":  WEATHER_CODES.get(code, "Unknown"),
    }


@mcp.tool
def convert_c_to_f(c: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return c * 9 / 5 + 32


# ── Run the server ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    # JSON-RPC on /mcp/  (streaming also auto-published on /streamable-http)
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8000,
        path="/mcp/",
    )
