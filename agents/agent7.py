import pandas as pd
import json
import litellm

# ── Model config ──
MODEL = "ollama/llama3.2"

# ── Color helpers ──
BLUE = "\033[94m"    # User
BRIGHT_GREEN = "\033[92m"  # Action
BRIGHT_RED = "\033[91m"   # Thought
BOLD_CYAN = "\033[1;96m"   # Agent
RESET = "\033[0m"

# ── Tool: Load office data ──
def load_office_data() -> dict:
    df = pd.read_csv("../data/offices.csv")
    return df.to_dict(orient="list")

# ── Tool: Analyze using canonical query strings ──
def analyze_offices(data: dict, query: str, memory: list) -> str:
    df = pd.DataFrame(data)
    q = query.strip().lower()

    if q == "average_revenue":
        avg = df["revenue_million"].mean()
        return f"Average revenue is ${avg:.2f} million."

    if q == "most_employees":
        idx = df["employees"].idxmax()
        return f"{df.loc[idx, 'city']} has the most employees: {df.loc[idx, 'employees']}."

    if q.startswith("opened_after_"):
        try:
            year = int(q.split("_")[-1])
            filtered = df[df["opened_year"] > year]
            if filtered.empty:
                return f"No offices opened after {year}."
            return "Offices opened after " + str(year) + ": " + ", ".join(filtered["city"])
        except:
            return "Invalid year in query."

    if q == "highest_revenue_per_employee":
        df["rev_per_emp"] = df["revenue_million"] / df["employees"]
        idx = df["rev_per_emp"].idxmax()
        return f"{df.loc[idx, 'city']} has the highest revenue per employee: ${df.loc[idx, 'rev_per_emp']:.2f}M."

    if q == "compare_new_york":
        ny = df[df["city"].str.lower() == "new york"]
        if ny.empty:
            return "New York not found in data."
        return f"New York: {ny.iloc[0]['employees']} employees, ${ny.iloc[0]['revenue_million']}M revenue."

    return "No matching data found for that canonical query."

# ── LLM Planner: normalize query into canonical form ──
def llm_decide_next_action(user_query: str, memory: list, data_loaded: bool) -> str:
    history = "\n".join([f"User: {m['user']}\nAgent: {m['agent']}" for m in memory])
    prompt = f"""
You are a helpful AI assistant for analyzing office data.

Your job is to plan tool calls based on user requests.

Tools available:
- load_data(): loads the office CSV data.
- analyze_offices(data, query, memory): analyzes the loaded data using one of the following query strings:

Canonical query options:
  - average_revenue
  - most_employees
  - opened_after_<year>   (e.g. opened_after_2014)
  - highest_revenue_per_employee
  - compare_new_york

Respond ONLY in this JSON format:
{{
  "thought": "why you chose the tool",
  "action": "load_data" | "analyze_offices",
  "args": {{
    "query": "<one of the above canonical queries>"
  }}
}}

Conversation so far:
{history}

The user asks: "{user_query}"
You {"already have" if data_loaded else "do not have"} the data loaded.
"""

    response = litellm.completion(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response["choices"][0]["message"]["content"]

# ── Main agent loop ──
def main():
    data_loaded = False
    data = None
    memory = []

    print("Office Data Agent is ready — type a question or 'exit' to quit.\n")

    while True:
        user_query = input(f"{BLUE}\nUser ➔ {RESET}").strip()
        if user_query.lower() in ["exit", "quit"]:
            print("Goodbye.")
            break

        current_query = user_query

        while True:
            llm_response = llm_decide_next_action(current_query, memory, data_loaded)

            try:
                plan = json.loads(llm_response)
            except json.JSONDecodeError:
                print(f"{BOLD_CYAN}\nAgent ➔ Sorry, I couldn't understand the plan.{RESET}")
                break

            print(f"\n{BRIGHT_RED}Thought: {plan['thought']}{RESET}")
            action = plan["action"]

            if action == "load_data":
                data = load_office_data()
                data_loaded = True
                print(f"{BRIGHT_GREEN}Action: Data loaded.{RESET}")
                continue  # re-loop and re-plan

            elif action == "analyze_offices":
                current_query = plan["args"].get("query", "")
                result = analyze_offices(data, current_query, memory)
                print(f"\n{BOLD_CYAN}Agent ➔ {result}{RESET}")
                memory.append({"user": user_query, "agent": result})
                break

            else:
                print(f"{BOLD_CYAN}\nAgent ➔ Unknown action.{RESET}")
                break

if __name__ == "__main__":
    main()
