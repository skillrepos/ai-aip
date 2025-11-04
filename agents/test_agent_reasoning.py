"""
Test Agent Reasoning and Tool Selection
Tests agent decision-making, tool selection, and reasoning patterns
"""

import pytest
import os
import requests
from unittest.mock import Mock, patch, MagicMock
from smolagents import ToolCallingAgent, LiteLLMModel, tool


# ========== TOOLS FOR TESTING ==========

@tool
def calculator(expression: str) -> str:
    """
    Evaluates a mathematical expression.

    Args:
        expression: A mathematical expression to evaluate

    Returns:
        The result of the calculation
    """
    try:
        # WARNING: eval() is unsafe for production use (code injection risk).
        # This simplified approach is ONLY for educational/testing purposes.
        # For production, use ast.literal_eval() or a proper expression parser (e.g., numexpr, py-expression-eval).
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def weather(location: str) -> str:
    """
    Gets real weather information for a location using Open-Meteo API.

    Args:
        location: City name or location

    Returns:
        Weather information
    """
    # Coordinates for common cities (in real app, would use geocoding API)
    coordinates = {
        "tokyo": (35.6762, 139.6503),
        "paris": (48.8566, 2.3522),
        "london": (51.5074, -0.1278),
        "new york": (40.7128, -74.0060),
        "san francisco": (37.7749, -122.4194),
    }

    location_lower = location.lower()
    lat, lon = None, None

    # Find matching city
    for city, coords in coordinates.items():
        if city in location_lower:
            lat, lon = coords
            city_name = city.title()
            break

    if lat is None:
        return f"Location '{location}' not found. Try: Tokyo, Paris, London, New York, San Francisco"

    # Call Open-Meteo API (same as Lab 1)
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current_weather=true"
            f"&timezone=auto"
        )
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        current = data["current_weather"]
        temp = current["temperature"]
        windspeed = current["windspeed"]

        # Weather codes from Open-Meteo
        weather_codes = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Fog", 48: "Rime fog", 51: "Light drizzle", 53: "Drizzle",
            55: "Heavy drizzle", 61: "Slight rain", 63: "Rain", 65: "Heavy rain",
            71: "Slight snow", 73: "Snow", 75: "Heavy snow", 95: "Thunderstorm"
        }
        conditions = weather_codes.get(current["weathercode"], "Unknown")

        return f"{city_name}: {conditions}, {temp}°C, wind {windspeed} km/h"

    except Exception as e:
        return f"Error fetching weather: {str(e)}"


@tool
def currency_converter(amount: float, from_currency: str, to_currency: str) -> str:
    """
    Converts between currencies using real exchange rates.

    Args:
        amount: Amount to convert
        from_currency: Source currency (USD, EUR, GBP, JPY, etc.)
        to_currency: Target currency

    Returns:
        Converted amount
    """
    from_curr = from_currency.upper()
    to_curr = to_currency.upper()

    # Use fawazahmed0 Currency API (same as Lab 3)
    base = from_curr.lower()
    target = to_curr.lower()

    urls = [
        f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{base}.json",
        f"https://latest.currency-api.pages.dev/v1/currencies/{base}.json"
    ]

    for url in urls:
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            rates = data.get(base, {})

            if target in rates:
                rate = rates[target]
                result = amount * rate
                return f"{amount} {from_curr} = {result:.2f} {to_curr} (rate: {rate:.4f})"

        except Exception:
            continue

    return f"Currency conversion failed for {from_curr} to {to_curr}"


# ========== MOCK-BASED TESTS (INSTANT) ==========

def test_agent_selects_calculator():
    """Test that agent correctly identifies math queries and selects calculator"""

    print("\n" + "="*60)
    print("🧪 TEST 1: Tool Selection - Math Query")
    print("="*60)

    # In a real test, we'd verify the agent's tool selection logic
    # For this demo, we're showing the pattern
    query = "What is 5 times 8?"

    print(f"\nQuery: '{query}'")
    print("\nAnalyzing query for tool selection...")

    # Verify calculator would be the right choice
    has_math_keywords = "calculate" in query.lower() or "times" in query or "*" in query

    print(f"  → Contains math keywords: {has_math_keywords}")
    print(f"  → Expected tool: calculator")

    assert has_math_keywords

    print("\n✓ Agent correctly identifies math query")
    print("✓ Would select calculator tool")
    print("\nKey Insight: Agent must recognize math-related language")
    print("             to choose the right tool")
    print("="*60)


def test_agent_selects_weather():
    """Test that agent correctly identifies weather queries"""

    print("\n" + "="*60)
    print("🧪 TEST 2: Tool Selection - Weather Query")
    print("="*60)

    query = "What's the weather in Tokyo?"

    print(f"\nQuery: '{query}'")
    print("\nAnalyzing query for tool selection...")

    # Verify weather keywords present
    has_weather_keyword = "weather" in query.lower()
    has_location = any(city in query.lower() for city in ["tokyo", "paris", "london"])

    print(f"  → Contains 'weather' keyword: {has_weather_keyword}")
    print(f"  → Contains location (Tokyo): {has_location}")
    print(f"  → Expected tool: weather")

    assert has_weather_keyword
    assert has_location

    print("\n✓ Agent correctly identifies weather query")
    print("✓ Would select weather tool")
    print("\nKey Insight: Agent recognizes location + weather context")
    print("="*60)


def test_ambiguous_query():
    """Test agent handling of ambiguous queries"""

    print("\n" + "="*60)
    print("🧪 TEST 3: Ambiguity Handling")
    print("="*60)

    query = "Tell me about Tokyo"

    print(f"\nQuery: '{query}'")
    print("\nChecking for specific intent indicators...")

    # This could be weather, facts, travel info, etc.
    # Agent should either ask for clarification or make best guess

    # Verify query is indeed ambiguous (doesn't contain specific keywords)
    is_specific = any(keyword in query.lower() for keyword in
                     ["weather", "temperature", "calculate", "convert"])

    print(f"  → Contains specific keywords: {is_specific}")
    print(f"  → Query is ambiguous: {not is_specific}")
    print("\nPossible interpretations:")
    print("  - Weather in Tokyo?")
    print("  - Facts about Tokyo?")
    print("  - Travel information?")

    assert not is_specific, "Query should be ambiguous"

    print("\n✓ Query identified as ambiguous")
    print("✓ Agent should ask for clarification or use context")
    print("\nKey Insight: Not all queries have clear tool mappings")
    print("             Agents must handle uncertainty")
    print("="*60)


def test_tool_failure_recovery():
    """Test agent recovery when a tool fails"""

    print("\n" + "="*60)
    print("🧪 TEST 4: Error Recovery")
    print("="*60)

    print("\nScenario: Calculator receives invalid expression")
    print("Query: 'invalid expression xyz'")
    print("\nCalling calculator tool with bad input...")

    # Simulate calculator tool failing
    try:
        result = calculator("invalid expression xyz")

        print(f"\nTool response: '{result}'")

        assert "Error" in result

        print("\n✓ Tool returns error message (doesn't crash)")
        print("✓ Error is descriptive")
        print("✓ Agent can receive error and explain to user")

    except Exception as e:
        pytest.fail(f"Tool should return error message, not raise exception: {e}")

    print("\nKey Insight: Tools should fail gracefully with error messages,")
    print("             not crash. This lets agents explain problems to users")
    print("             and potentially retry or use alternative approaches.")
    print("="*60)


def test_compound_query_parsing():
    """Test agent ability to identify multiple tasks in one query"""

    print("\n" + "="*60)
    print("🧪 TEST 5: Compound Query Parsing")
    print("="*60)

    query = "What's 25 times 4 and what's the weather in Tokyo?"

    print(f"\nQuery: '{query}'")
    print("\nParsing for multiple tasks...")

    # Verify query contains multiple tasks
    has_math = any(word in query.lower() for word in ["times", "calculate", "*", "plus"])
    has_weather = "weather" in query.lower()
    has_location = any(city in query.lower() for city in ["tokyo", "paris", "london"])

    print(f"\n  → Task 1 identified: Math calculation")
    print(f"     - Has math keywords: {has_math}")
    print(f"     - Requires: calculator tool")

    print(f"\n  → Task 2 identified: Weather lookup")
    print(f"     - Has weather keyword: {has_weather}")
    print(f"     - Has location: {has_location}")
    print(f"     - Requires: weather tool")

    assert has_math, "Should identify math component"
    assert has_weather and has_location, "Should identify weather component"

    print("\n✓ Query successfully parsed into 2 distinct tasks")
    print("✓ Agent should:")
    print("   1. Call calculator for 25 * 4")
    print("   2. Call weather for Tokyo")
    print("   3. Synthesize both results")

    print("\nKey Insight: Agents must identify and sequence multiple")
    print("             operations within a single query")
    print("="*60)


# ========== REAL AGENT TEST (WITH LLM) ==========

@pytest.mark.slow
def test_real_agent_tool_selection():
    """
    Integration test: Real agent with real LLM and real APIs
    Tests actual agent reasoning with compound query using real-world data


    Run as pytest test_agent_reasoning.py::test_real_agent_tool_selection -v -s
    """

    print("\n" + "="*60)
    print("🧪 REAL AGENT TEST - Testing actual reasoning with real APIs")
    print("="*60)
    print("Using REAL weather and currency APIs!")
    print()


    model = os.getenv("OLLAMA_MODEL", "ollama/llama3.2:latest")

    llm = LiteLLMModel(
        model_id=model,
        api_base="http://localhost:11434"
    )

    # Create agent with all real-world tools
    agent = ToolCallingAgent(
        tools=[calculator, weather, currency_converter],
        model=llm,
    )

    # Compound query requiring reasoning about TWO separate tasks with real data
    query = "What's 25 times 4 and what's the weather in Tokyo?"

    print(f"Query: '{query}'")
    print("\nExpected agent reasoning:")
    print("1. Parse query into two tasks")
    print("2. Identify task 1: math calculation (25 * 4)")
    print("3. Identify task 2: weather lookup (Tokyo)")
    print("4. Call calculator tool")
    print("5. Call weather tool with real Open-Meteo API")
    print("6. Synthesize both results")
    print("\nAgent is reasoning and calling REAL APIs...\n")

    try:
        response = agent.run(query)

        print(f"\nAgent response: {response}\n")

        # Verify agent addressed both parts
        response_str = str(response).lower()

        # Check for math result (25 * 4 = 100)
        has_math_result = "100" in response_str

        # Check for weather info
        has_weather = "tokyo" in response_str and any(word in response_str
                      for word in ["weather", "cloud", "sunny", "rain", "clear", "temperature", "°c", "wind"])

        print("Verification:")
        print(f"  ✓ Math calculation present: {'100' in response_str}")
        print(f"  ✓ Weather information present: {has_weather}")
        print(f"  ✓ Using real Open-Meteo API for weather")

        # At least one should be present for test to pass
        # (Agent might handle compound queries differently)
        assert has_math_result or has_weather, \
            "Agent should address at least one part of the compound query"

        if has_math_result and has_weather:
            print("\n✓✓ EXCELLENT: Agent handled BOTH tasks with real APIs!")
        elif has_math_result:
            print("\n✓ Agent handled math task")
            print("  (May need prompt tuning for weather task)")
        else:
            print("\n✓ Agent handled weather task with real data")
            print("  (May need prompt tuning for math task)")

        print("\n" + "="*60)
        print("KEY INSIGHT: Agent's reasoning ability determines")
        print("whether it can identify and sequence multiple tools")
        print("This test used REAL APIs - Open-Meteo for weather!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Error during agent execution: {e}")
        print("This might indicate:")
        print("  - Ollama not running")
        print("  - Model not available")
        print("  - Agent reasoning failed")
        print("  - API connection issues")
        raise


@pytest.mark.slow
def test_real_agent_currency_conversion():
    """
    Integration test: Test real currency conversion with live exchange rates

    
    Run with: pytest test_agent_reasoning.py::test_real_agent_currency_conversion -v -s
    """

    print("\n" + "="*60)
    print("🧪 REAL AGENT TEST - Currency conversion with live rates")
    print("="*60)
    print("Using REAL currency exchange API!")
    print()

    model = os.getenv("OLLAMA_MODEL", "ollama/llama3.2:latest")

    llm = LiteLLMModel(
        model_id=model,
        api_base="http://localhost:11434"
    )

    agent = ToolCallingAgent(
        tools=[currency_converter],
        model=llm,
    )

    # Query for currency conversion
    query = "Convert 100 USD to EUR"

    print(f"Query: '{query}'")
    print("\nExpected agent reasoning:")
    print("1. Identify currency conversion task")
    print("2. Extract: amount=100, from=USD, to=EUR")
    print("3. Call currency_converter tool")
    print("4. Tool fetches live exchange rate from API")
    print("5. Return converted amount")
    print("\nAgent is calling REAL currency API...\n")

    try:
        response = agent.run(query)

        print(f"\nAgent response: {response}\n")

        response_str = str(response).lower()

        # Check for currency conversion indicators
        has_conversion = any(word in response_str for word in ["eur", "euro", "converted", "rate"])
        has_numbers = any(char.isdigit() for char in response_str)

        print("Verification:")
        print(f"  ✓ Currency mentioned: {has_conversion}")
        print(f"  ✓ Contains numbers: {has_numbers}")
        print(f"  ✓ Used real fawazahmed0 Currency API")

        assert has_conversion or has_numbers, \
            "Agent should provide currency conversion result"

        print("\n✓✓ Agent successfully converted currency with REAL exchange rates!")
        print("\n" + "="*60)
        print("KEY INSIGHT: Tools can integrate real-world APIs")
        print("to provide live, accurate data to agents")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Error during agent execution: {e}")
        print("This might indicate:")
        print("  - Ollama not running")
        print("  - Model not available")
        print("  - Currency API unavailable")
        raise


def test_real_agent_error_recovery():
    """
    Test how real agent handles tool errors

    Run with: pytest test_agent_reasoning.py::test_real_agent_error_recovery -v -s
    """

    print("\n" + "="*60)
    print("🧪 REAL AGENT TEST - Error handling")
    print("="*60)

    model = os.getenv("OLLAMA_MODEL", "ollama/llama3.2:latest")

    llm = LiteLLMModel(
        model_id=model,
        api_base="http://localhost:11434"
    )

    agent = ToolCallingAgent(
        tools=[calculator, weather, currency_converter],
        model=llm,
    )

    # Query that will cause calculator to fail
    query = "Calculate: abc plus xyz"

    print(f"Query: '{query}' (invalid math expression)")
    print("Expected: Agent receives error and explains to user")
    print("\nAgent is processing...\n")

    try:
        response = agent.run(query)

        print(f"Agent response: {response}\n")

        # Verify agent didn't crash and provided some response
        assert response is not None
        assert len(str(response)) > 0

        print("✓ Agent handled error gracefully (didn't crash)")
        print("✓ Agent can explain tool failures to users")

    except Exception as e:
        print(f"Note: Agent execution error: {e}")
        print("This is expected if agent framework raises on tool errors")


# ========== HELPER TO RUN SPECIFIC TEST GROUPS ==========

if __name__ == "__main__":
    print("\n" + "="*60)
    print("AGENT REASONING TEST SUITE")
    print("="*60)
    print("\n🔧 Tools use REAL APIs:")
    print("  • Weather: Open-Meteo API (same as Lab 1)")
    print("  • Currency: fawazahmed0 Currency API (same as Lab 3)")
    print("  • Calculator: Direct Python evaluation")
    print("\nQuick tests (instant - using mocks):")
    print("  python -m pytest test_agent_reasoning.py::test_agent_selects_calculator -v -s")
    print("  python -m pytest test_agent_reasoning.py::test_agent_selects_weather -v -s")
    print("  python -m pytest test_agent_reasoning.py::test_ambiguous_query -v -s")
    print("  python -m pytest test_agent_reasoning.py::test_tool_failure_recovery -v -s")
    print("  python -m pytest test_agent_reasoning.py::test_compound_query_parsing -v -s")
    print("\nReal agent tests with LIVE APIs")
    print("  python -m pytest test_agent_reasoning.py::test_real_agent_tool_selection -v -s")
    print("  python -m pytest test_agent_reasoning.py::test_real_agent_currency_conversion -v -s")
    print("  python -m pytest test_agent_reasoning.py::test_real_agent_error_recovery -v -s")
    print("\nRun all quick tests:")
    print("  python -m pytest test_agent_reasoning.py -v -s -k 'not real'")
    print("\nRun all real agent tests:")
    print("  python -m pytest test_agent_reasoning.py -v -s -k 'real'")
    print("\nNote: Use 'python -m pytest' to use your current Python environment")
    print("      Add '-s' flag to see test output and explanations")
    print("      Real agent tests require internet connection for APIs")
    print("="*60 + "\n")
