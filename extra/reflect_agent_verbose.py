import subprocess
import tempfile
import os
import time
import sys

from autogen import AssistantAgent

# ── Simulated streaming print with color ──

def stream_print(text, delay=0.01):
    print("Model response:")
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def print_prompt(label, prompt):
    print(f"\033[94m[{label}] Sending prompt:\033[0m")
    print(f"\033[94m{prompt}\033[0m")

def print_status(message):
    print(f"\033[92m{message}\033[0m")

def print_sysmsg(agent_name, msg):
    print(f"\033[91m[{agent_name}] System message:\033[0m")
    print(f"\033[91m{msg}\033[0m")

# ── Ollama config ──
llm_config = {
    "config_list": [
        {
            "model": "llama3.2",
            "base_url": "http://localhost:11434/v1",
            "api_type": "ollama",
            "stream": True,
        }
    ],
    "temperature": 0.0,
}

# ── Agents ──
code_writer = AssistantAgent(
    name="code_writer",
    llm_config=llm_config,
    system_message=(
        "You write Python code. Output ONLY code, no explanations.\n"
        "The code is run non-interactively, so never call input() and never read\n"
        "from a file - use hardcoded example values and print the results."
    ),
)

critic = AssistantAgent(
    name="critic",
    llm_config=llm_config,
    system_message=(
        "You are a Python code reviewer.\n"
        "Check whether the code runs correctly AND fulfills the request.\n"
        "You are also given runtime feedback.\n"
        "Respond with:\n"
        "- 'PASS' if it meets the request\n"
        "- or 'FAIL: <brief reason>' if it does not."
    ),
)

fixer = AssistantAgent(
    name="fixer",
    llm_config=llm_config,
    system_message=(
        "You fix Python code based on critique. Return ONLY fixed code.\n"
        "The code is run non-interactively, so never call input() - use hardcoded\n"
        "example values and print the results."
    ),
)

# ── Code Cleanup ──

def clean_code_block(code: str) -> str:
    lines = code.strip().splitlines()
    if lines and lines[0].strip().startswith("```"):
        return "\n".join(lines[1:-1])
    return code.strip()

# ── Runtime simulation ──

def simulate_runtime_feedback(code: str) -> str:
    print_sysmsg("simulator", "Running user-generated Python code and capturing output.")
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        result = subprocess.run(
            ["python", temp_path],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,   # no terminal: interactive code fails fast
            timeout=10
        )
        output = result.stdout.strip()
        errors = result.stderr.strip()

        if result.returncode != 0:
            return f"Runtime error occurred:\n{errors}"
        elif output:
            return f"Executed successfully.\nOutput:\n{output}"
        else:
            return "Executed successfully with no output."
    except Exception as e:
        return f"Execution failed or timed out: {str(e)}"
    finally:
        os.remove(temp_path)

# ── Main loop ──

def main():
    print("Reflective Agent (Ollama) — type a code request or 'exit' to quit.\n")

    while True:
        task = input("Request ➔ ").strip()
        if task.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        # Step 1: Generate initial code
        messages = [{"role": "user", "content": task}]
        print_sysmsg("code_writer", code_writer.system_message)
        print_prompt("code_writer", messages[0]["content"])
        print_status("[code_writer] Generating code...")
        code = code_writer.generate_reply(messages)["content"]
        print("\n--- Code ---\n")
        stream_print(code)

        # Step 2: Simulate runtime of original
        print_status("[simulator] Running original code...")
        cleaned_code = clean_code_block(code)
        runtime_feedback = simulate_runtime_feedback(cleaned_code)
        print("\n--- Runtime Feedback ---\n")
        print(runtime_feedback)

        # Step 3: Critique
        critique_input = (
            f"Original request:\n{task}\n\n"
            f"Generated code:\n{code}\n\n"
            f"Runtime behavior:\n{runtime_feedback}"
        )
        print_sysmsg("critic", critic.system_message)
        print_prompt("critic", critique_input)
        print_status("[critic] Reviewing code...")
        critique = critic.generate_reply([{"role": "user", "content": critique_input}])["content"]
        print("\n--- Critique ---\n")
        stream_print(critique)

        # Step 4: Fix and re-test if needed
        if critique.strip().lower().startswith("fail"):
            fix_input = (
                f"Original request:\n{task}\n\n"
                f"Original code:\n{code}\n\n"
                f"Critique:\n{critique}"
            )
            print_sysmsg("fixer", fixer.system_message)
            print_prompt("fixer", fix_input)
            print_status("[fixer] Fixing code...")
            fixed_code = fixer.generate_reply([{"role": "user", "content": fix_input}])["content"]
            print("\n--- Fixed Code ---\n")
            stream_print(fixed_code)

            print_status("[simulator] Running fixed code...")
            cleaned_fixed_code = clean_code_block(fixed_code)
            fix_runtime_feedback = simulate_runtime_feedback(cleaned_fixed_code)
            print("\n--- Fixed Runtime Feedback ---\n")
            print(fix_runtime_feedback)
        else:
            print_status("[status] Original code passed review.\n")

if __name__ == "__main__":
    main()
