"""
Secure Enterprise HR Benefits Agent
Implements defense-in-depth security controls against prompt injection.
Merge from ../extra/secure_agent.txt to complete all 5 security layers.
"""

import os
import warnings
from smolagents import ToolCallingAgent, LiteLLMModel, tool
import re
import json
import datetime

# Suppress Pydantic serialization warnings from litellm/Ollama response parsing
warnings.filterwarnings("ignore", message="Pydantic serializer warnings")

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")


# --- Model provider: Groq if AGENT_PROVIDER=groq and GROQ_API_KEY are exported, else local Ollama ---
# (Same toggle as Labs 3, 4, and 7. The security defenses below are deterministic, so they
#  work on any model; Groq just makes the agent faster and its tool use more reliable.)
def build_model():
    provider = os.environ.get("AGENT_PROVIDER", "").strip().lower()
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    if provider == "groq" and groq_key:
        name = os.environ.get("AGENT_MODEL", "llama-3.1-8b-instant").strip()
        if not name.startswith("groq/"):
            name = "groq/" + name
        print(f"[MODEL] provider=groq  model={name}")
        return LiteLLMModel(model_id=name, api_key=groq_key, temperature=0.0)
    print(f"[MODEL] provider=ollama  model=ollama/{OLLAMA_MODEL}")
    return LiteLLMModel(model_id=f"ollama/{OLLAMA_MODEL}", api_base="http://localhost:11434")


# ========== SIMULATED EMPLOYEE DATABASE ==========

EMPLOYEES = {
    "E1001": {"name": "Alice Johnson", "department": "Engineering", "salary": 95000, "pto_balance": 15, "benefits": "Gold Plan: Medical, Dental, Vision, 401k match 6%"},
    "E1002": {"name": "Bob Smith", "department": "Marketing", "salary": 82000, "pto_balance": 8, "benefits": "Silver Plan: Medical, Dental, 401k match 4%"},
    "E1003": {"name": "Carol Davis", "department": "Engineering", "salary": 105000, "pto_balance": 22, "benefits": "Gold Plan: Medical, Dental, Vision, 401k match 6%"},
}

# ========== SECURITY LAYER 1: SECURITY LOGGING ==========

def log_security_event(event_type, details):
    """Log security events for audit trail."""
    # GAP 1: Implement timestamped JSON security logging
    pass


# ========== SECURITY LAYER 2: SECURE TOOLS (LEAST PRIVILEGE) ==========

@tool
def lookup_benefits(employee_id: str) -> str:
    """
    Look up benefits information for an employee by their ID.

    Args:
        employee_id: The employee ID (e.g., E1001)

    Returns:
        Benefits information for the employee
    """
    emp = EMPLOYEES.get(employee_id.upper())
    if emp:
        return f"Employee: {emp['name']} | Department: {emp['department']} | Benefits: {emp['benefits']}"
    return f"Employee {employee_id} not found."


@tool
def check_pto_balance(employee_id: str) -> str:
    """
    Check the PTO (paid time off) balance for an employee.

    Args:
        employee_id: The employee ID (e.g., E1001)

    Returns:
        PTO balance information
    """
    emp = EMPLOYEES.get(employee_id.upper())
    if emp:
        return f"Employee: {emp['name']} | PTO Balance: {emp['pto_balance']} days remaining"
    return f"Employee {employee_id} not found."


# ========== SECURITY LAYER 3: INPUT VALIDATION ==========

def validate_input(user_input):
    """Validate user input for goal hijacking attempts."""
    # GAP 2: Implement regex hijacking pattern detection
    return True, "Input validated"


# ========== SECURITY LAYER 4: HARDENED SYSTEM PROMPT ==========

# GAP 3: Replace with a hardened system prompt containing explicit security rules
SYSTEM_PROMPT = "You are OmniTech's HR Benefits Assistant."


# ========== SECURITY LAYER 5: OUTPUT VALIDATION ==========

def validate_output(response):
    """Validate agent output for dangerous action indicators."""
    # GAP 4: Implement output validation with dangerous action pattern matching
    return True, "Output validated"


# ========== MAIN ==========

def main():
    print("\nOmniTech HR Benefits Assistant (Secure)")
    print("Type 'quit' to exit.\n")

    print("[INFO] Note: Small models may struggle with tool arguments")
    print()

    try:
        llm = build_model()

        # LEAST PRIVILEGE: Only read-only benefits and PTO tools
        agent = ToolCallingAgent(
            tools=[lookup_benefits, check_pto_balance],
            model=llm,
            instructions=SYSTEM_PROMPT,
            max_steps=3,  # Limit steps to prevent hanging on final response
        )
    except Exception as e:
        print(f"[ERROR] Failed to initialize agent: {e}")
        return

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye.")
            break
        if not user_input:
            continue

        # GAP 5: Integrate input validation, output validation, and security logging
        #         into the chat loop (currently calls agent.run() directly)
        try:
            response = agent.run(user_input)
            print(f"Assistant: {response}\n")
        except Exception as e:
            print(f"Assistant: Sorry, I encountered an error: {e}\n")


if __name__ == "__main__":
    main()
