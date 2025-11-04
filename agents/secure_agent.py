"""
Secure Goal Agent - Complete Implementation
Demonstrates multi-layer security controls to protect agent goals
"""

import re
import json
import logging
from datetime import datetime
from enum import Enum
from smolagents import ToolCallingAgent, LiteLLMModel, tool

# Use 1B model for faster demonstration
MODEL = "ollama/llama3.2:latest"


# ========== SECURITY LOGGING SETUP ==========
# TODO: Add security event types, logger configuration


# ========== INPUT VALIDATION LAYER ==========
# TODO: Add validate_input() function


# ========== OUTPUT SANITIZATION ==========
# TODO: Add sanitize_output() function


# ========== RATE LIMITING ==========
# TODO: Add RateLimiter class


# ========== SANDBOXED CODE EXECUTION ==========
# TODO: Add execute_with_sandbox() function


# ========== SECURE TOOLS WITH VALIDATION ==========

@tool
def secure_calculator(expression: str) -> str:
    """
    Safely evaluates mathematical expressions.

    Args:
        expression: A mathematical expression (numbers and operators only)

    Returns:
        The result of the calculation
    """
    # TODO: Add rate limiting check
    # TODO: Add input validation
    # TODO: Add safe evaluation using ast module

    return "Calculator tool not yet implemented"


@tool
def currency_converter(amount: float, from_currency: str, to_currency: str) -> str:
    """
    Converts currency (simulated with fixed rates).

    Args:
        amount: Amount to convert
        from_currency: Source currency code (USD, EUR, GBP, JPY)
        to_currency: Target currency code

    Returns:
        Converted amount
    """
    # TODO: Add rate limiting check
    # TODO: Add currency validation (allowlist)
    # TODO: Add amount validation

    return "Currency converter not yet implemented"


# ========== SECURE AGENT CONFIGURATION ==========

# Initialize LLM
llm = LiteLLMModel(
    model_id="ollama/llama3.2",
    api_base="http://localhost:11434"
)

# TODO: Add security-focused system prompt


def run_secure_agent():
    """Main loop for secure agent with all protections enabled"""

    # TODO: Create agent with least privilege (limited tools)
    agent = ToolCallingAgent(
        tools=[secure_calculator, currency_converter],
        model=llm,
    )

    print("=" * 60)
    print("SECURE AGENT - Template (security not yet implemented)")
    print("=" * 60)
    print("\nType 'exit' to quit\n")

    while True:
        user_input = input("Query> ").strip()

        if user_input.lower() == 'exit':
            break

        if not user_input:
            continue

        # TODO: Add input validation before processing

        try:
            response = agent.run(user_input)

            # TODO: Add output sanitization before displaying

            print(f"\nAgent: {response}\n")

        except Exception as e:
            print(f"Error: {str(e)}\n")


if __name__ == "__main__":
    run_secure_agent()
