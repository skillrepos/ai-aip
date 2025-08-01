import subprocess
import tempfile
import os

from autogen import AssistantAgent

# ── Ollama config ──────────────────────────────────────────────
llm_config = {
    "config_list": [
        {
            "model": "llama3.2",
            "base_url": "http://localhost:11434/v1",
            "api_type": "ollama",
        }
    ],
    "temperature": 0.0,
}

# ── Agents ─────────────────────────────────────────────────────
code_writer = AssistantAgent(
    name="code_writer",
    llm_config=llm_config,
    system_message="You write Python code. Output ONLY code, no explanations.",
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
    system_message="You fix Python code based on critique. Return ONLY fixed code.",
)

# ── Code Cleanup ───────────────────────────────────────────────
def clean_code_block(code: str) -> str:
    lines = code.strip().splitlines()
    if lines and lines[0].strip().startswith("```"):
        return "\n".join(lines[1:-1])
    return code.strip()

# ── Runtime simulation ─────────────────────────────────────────
def simulate_runtime_feedback(code: str) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        result = subprocess.run(
            ["python", temp_path],
            capture_output=True,
            text=True,
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

# ── Main loop ──────────────────────────────────────────────────
def main():
    print("Type a code request or 'exit' to quit.\n")

    while True:
        task = input("Request ➤ ").strip()
        if task.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        # Step 1: Generate initial code
        messages = [{"role": "user", "content": task}]
        print("\nGenerating code...")
        code = code_writer.generate_reply(messages)["content"]
        print("\n--- Code ---\n", code)

        # Step 2: Simulate runtime of original
        print("\nSimulating runtime behavior...")
        cleaned_code = clean_code_block(code)
        runtime_feedback = simulate_runtime_feedback(cleaned_code)
        print("\n--- Runtime Feedback ---\n", runtime_feedback)

        # Step 3: Critique
        print("\nCritiquing code...")
        critique_input = (
            f"Original request:\n{task}\n\n"
            f"Generated code:\n{code}\n\n"
            f"Runtime behavior:\n{runtime_feedback}"
        )
        critique = critic.generate_reply([{"role": "user", "content": critique_input}])["content"]
        print("\n--- Critique ---\n", critique)

        # Step 4: Fix and re-test if needed
        if critique.strip().lower().startswith("fail"):
            print("\nFixing code...")
            fix_input = (
                f"Original request:\n{task}\n\n"
                f"Original code:\n{code}\n\n"
                f"Critique:\n{critique}"
            )
            fixed_code = fixer.generate_reply([{"role": "user", "content": fix_input}])["content"]
            print("\n--- Fixed Code ---\n", fixed_code)

            print("\nSimulating runtime of fixed code...")
            cleaned_fixed_code = clean_code_block(fixed_code)
            fix_runtime_feedback = simulate_runtime_feedback(cleaned_fixed_code)
            print("\n--- Fixed Runtime Feedback ---\n", fix_runtime_feedback)
        else:
            print("\nOriginal code passed review.\n")

if __name__ == "__main__":
    main()
