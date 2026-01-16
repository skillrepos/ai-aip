#!/usr/bin/env python3
"""
Lab 2: FastMCP Weather Server
────────────────────────────────────────────────────────────────────────
A robust FastMCP server that provides weather and geocoding services via HTTP.

Tools Provided
--------------
1. get_weather(lat, lon) → dict with temperature °C, WMO code, conditions
2. convert_c_to_f(c) → float (temperature in °F)
3. geocode_location(name) → dict with latitude, longitude, location name

Key Features
------------
* **Robust Retry Logic**: All API calls retry up to 3 times with exponential
  backoff (1.5s, 2.25s) on transient errors (429, 5xx)
* **Fresh Connections**: Each retry creates a new session to avoid connection
  pool issues that can cause persistent failures
* **Graceful Error Handling**: Returns error dict instead of raising exceptions,
  allowing clients to continue processing
* **HTTP Transport**: Runs on localhost:8000/mcp/ using FastAPI + Uvicorn

Architecture
------------
This server centralizes all external API calls to Open-Meteo, providing a
clean separation between agents (orchestration) and API access (this server).
"""

from __future__ import annotations

# ── stdlib ──────────────────────────────────────────────────────────
import time
from typing import Final

# ── 3rd-party ───────────────────────────────────────────────────────
import requests
from fastmcp import FastMCP

# ╔══════════════════════════════════════════════════════════════════╗
# ║ 1.  Weather-code lookup table (WMO standard codes)               ║
# ╚══════════════════════════════════════════════════════════════════╝
# Open-Meteo returns WMO weather codes - this maps them to descriptions.
# WMO (World Meteorological Organization) codes are used by many weather APIs.
WEATHER_CODES: Final[dict[int, str]] = {
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

# ╔══════════════════════════════════════════════════════════════════╗
# ║ 2.  Retry configuration for API resilience                       ║
# ╚══════════════════════════════════════════════════════════════════╝
# Shared retry settings for all external API calls
MAX_RETRIES    = 3       # Total attempts (1 original + 2 retries)
BACKOFF_FACTOR = 1.5     # Exponential backoff: 1.5s, 2.25s, 3.375s
TRANSIENT_CODES = {429, 500, 502, 503, 504}  # HTTP codes worth retrying

# ╔══════════════════════════════════════════════════════════════════╗
# ║ 3.  MCP Server initialization and tool definitions               ║
# ╚══════════════════════════════════════════════════════════════════╝
mcp = FastMCP("WeatherServer")

# ─── Weather Tool ────────────────────────────────────────────────────

@mcp.tool
def get_weather(lat: float, lon: float) -> dict:
    """
    Fetch **current weather** from Open-Meteo and return a concise dict.

    Retry policy
    ------------
    * Up to MAX_RETRIES total attempts with fresh connections.
    * Retries on network errors **or** HTTP 429/5xx.
    * Exponential back-off (1.5 s, 2.25 s, …).
    * Each retry uses a new session to avoid connection pool issues.

    Parameters
    ----------
    lat, lon : float
        Geographic coordinates in decimal degrees.

    Returns
    -------
    dict
        {
            "temperature": <float °C>,
            "code":        <int WMO weathercode>,
            "conditions":  <friendly description>,
            "error":       <error message if request failed>
        }
    """
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&current_weather=true"
    )

    last_error = None

    # Retry loop with fresh connections
    for attempt in range(MAX_RETRIES):
        try:
            # Fresh session per attempt avoids connection pool reuse issues
            session = requests.Session()
            resp = session.get(url, timeout=15)
            session.close()

            # Handle rate limiting and server errors with retry
            if resp.status_code in TRANSIENT_CODES:
                last_error = f"HTTP {resp.status_code}"
                if attempt < MAX_RETRIES - 1:
                    time.sleep(BACKOFF_FACTOR ** attempt)
                    continue

            resp.raise_for_status()

            # Extract and return weather data
            cw = resp.json()["current_weather"]
            code = cw["weathercode"]
            return {
                "temperature": cw["temperature"],
                "code":        code,
                "conditions":  WEATHER_CODES.get(code, "Unknown"),
            }

        except requests.HTTPError as e:
            # HTTP errors (4xx, 5xx not already caught)
            last_error = f"HTTP {e.response.status_code}"
            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_FACTOR ** attempt)
                continue

        except requests.RequestException as e:
            # Network errors (timeout, connection refused, etc.)
            last_error = f"{type(e).__name__}"
            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_FACTOR ** attempt)
                continue

        except (KeyError, ValueError) as e:
            # Data format errors - don't retry, immediate failure
            return {
                "error": f"Received invalid data from weather service: {type(e).__name__}. Please try again later."
            }

    # All retries exhausted - return graceful error
    return {
        "error": f"Weather service failed after {MAX_RETRIES} attempts (last error: {last_error}). Please try again later."
    }


# ─── Temperature Conversion Tool ─────────────────────────────────────

@mcp.tool
def convert_c_to_f(c: float) -> float:
    """Simple Celsius → Fahrenheit conversion."""
    return c * 9 / 5 + 32


# ─── Geocoding Tool ──────────────────────────────────────────────────

@mcp.tool
def geocode_location(name: str) -> dict:
    """
    Geocode a location name to latitude/longitude coordinates using Open-Meteo's geocoding API.

    Retry policy
    ------------
    * Up to MAX_RETRIES total attempts with fresh connections.
    * Retries on network errors **or** HTTP 429/5xx.
    * Exponential back-off (1.5 s, 2.25 s, …).
    * Each retry uses a new session to avoid connection pool issues.

    Parameters
    ----------
    name : str
        Location name (e.g., "San Francisco", "Paris, France", "London, UK")

    Returns
    -------
    dict
        {
            "latitude": <float>,
            "longitude": <float>,
            "name": <matched location name>,
            "error": <error message if request failed>
        }
    """
    url = "https://geocoding-api.open-meteo.com/v1/search"
    last_error = None

    # Retry loop with fresh connections
    for attempt in range(MAX_RETRIES):
        try:
            # Fresh session per attempt avoids connection pool reuse issues
            session = requests.Session()
            resp = session.get(url, params={"name": name, "count": 1}, timeout=15)
            session.close()

            # Handle rate limiting and server errors with retry
            if resp.status_code in TRANSIENT_CODES:
                last_error = f"HTTP {resp.status_code}"
                if attempt < MAX_RETRIES - 1:
                    time.sleep(BACKOFF_FACTOR ** attempt)
                    continue

            resp.raise_for_status()

            # Parse and return geocoding results
            data = resp.json()
            if data.get("results"):
                hit = data["results"][0]
                return {
                    "latitude": hit["latitude"],
                    "longitude": hit["longitude"],
                    "name": hit.get("name", name),
                }
            else:
                # No results found - not an error, just no match
                return {
                    "error": f"No location found for '{name}'. Try a different search term."
                }

        except requests.HTTPError as e:
            # HTTP errors (4xx, 5xx not already caught)
            last_error = f"HTTP {e.response.status_code}"
            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_FACTOR ** attempt)
                continue

        except requests.RequestException as e:
            # Network errors (timeout, connection refused, etc.)
            last_error = f"{type(e).__name__}"
            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_FACTOR ** attempt)
                continue

        except (KeyError, ValueError) as e:
            # Data format errors - don't retry, immediate failure
            return {
                "error": f"Received invalid data from geocoding service: {type(e).__name__}. Please try again later."
            }

    # All retries exhausted - return graceful error
    return {
        "error": f"Geocoding service failed after {MAX_RETRIES} attempts (last error: {last_error}). Please try again later."
    }

# ╔══════════════════════════════════════════════════════════════════╗
# ║ 4.  Server startup                                                ║
# ╚══════════════════════════════════════════════════════════════════╝
if __name__ == "__main__":
    # Start HTTP server using FastAPI + Uvicorn
    # Clients connect to: http://127.0.0.1:8000/mcp/
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8000,
        path="/mcp/",
    )
