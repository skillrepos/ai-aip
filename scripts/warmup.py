#!/usr/bin/env python3
"""
Comprehensive Ollama Warmup for AI Agents Workshop
Preloads all models and execution paths used across Labs 1-10

This script:
- Loads llama3.2:1b and llama3.2:3b into memory
- Exercises tool calling paths (LangChain, SmolAgents, AutoGen)
- Warms up JSON formatting paths
- Preloads embedding model for Lab 4
- Caches common tokenization patterns

Run this BEFORE workshop starts to ensure fast lab performance!
"""

import argparse
import concurrent.futures as cf
import json
import os
import sys
import time
from pathlib import Path

import requests


# ============================================================================
# COLOR HELPERS
# ============================================================================

BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_header(text):
    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}{text.center(70)}{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")


def print_step(step, text):
    print(f"{BOLD}{BLUE}[{step}]{RESET} {text}")


def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")


def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_error(text):
    print(f"{RED}✗ {text}{RESET}")


# ============================================================================
# OLLAMA API HELPERS
# ============================================================================

def ping_ollama(host: str) -> bool:
    """Check if Ollama server is running"""
    try:
        r = requests.get(f"{host}/api/version", timeout=3)
        r.raise_for_status()
        version = r.json().get("version", "unknown")
        print_success(f"Ollama server reachable (version: {version})")
        return True
    except Exception as e:
        print_error(f"Ollama server not reachable: {e}")
        return False


def list_local_models(host: str) -> list:
    """Get list of models already pulled"""
    try:
        r = requests.get(f"{host}/api/tags", timeout=3)
        r.raise_for_status()
        models = r.json().get("models", [])
        return [m["name"] for m in models]
    except Exception as e:
        print_warning(f"Could not list models: {e}")
        return []


def pull_model(host: str, model: str) -> bool:
    """Pull model if not already available"""
    print_step("PULL", f"Checking if {model} is available...")

    local_models = list_local_models(host)

    # Check various name formats (llama3.2:3b, llama3.2:latest, etc.)
    model_base = model.split(":")[0]
    if any(model_base in m for m in local_models):
        print_success(f"{model} already available locally")
        return True

    print(f"{YELLOW}→ Pulling {model} (this may take a few minutes)...{RESET}")

    try:
        # Stream the pull response
        r = requests.post(
            f"{host}/api/pull",
            json={"name": model, "stream": True},
            timeout=600,
            stream=True
        )
        r.raise_for_status()

        for line in r.iter_lines():
            if line:
                data = json.loads(line)
                status = data.get("status", "")
                if "pulling" in status.lower():
                    # Show progress for large pulls
                    print(f"  {status}", end="\r")
                elif "success" in status.lower():
                    print()
                    print_success(f"Pulled {model}")
                    return True

        return True

    except Exception as e:
        print_error(f"Failed to pull {model}: {e}")
        return False


def generate_once(host: str, model: str, prompt: str, json_mode: bool = False,
                  tools: list = None, keep_alive: str = "15m") -> tuple:
    """
    Run one generation to warm up model
    Returns: (success: bool, duration: float, response: str)
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "top_k": 1,
            "num_predict": 50,  # Short responses for warmup
        },
        "keep_alive": keep_alive
    }

    # Add JSON formatting if requested (exercises format path)
    if json_mode:
        payload["format"] = "json"
        if not ("json" in prompt.lower() or "{" in prompt):
            payload["prompt"] = prompt + '\n\nRespond with valid JSON: {"status": "ready"}'

    # Add tools if provided (exercises tool calling path)
    if tools:
        payload["tools"] = tools

    try:
        t0 = time.perf_counter()
        r = requests.post(f"{host}/api/generate", json=payload, timeout=120)
        dt = time.perf_counter() - t0
        r.raise_for_status()

        response = r.json().get("response", "")
        return (True, dt, response)

    except Exception as e:
        return (False, 0.0, str(e))


def generate_chat(host: str, model: str, messages: list, keep_alive: str = "15m") -> tuple:
    """
    Use chat API (for multi-turn warmup)
    Returns: (success: bool, duration: float)
    """
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 50,
        },
        "keep_alive": keep_alive
    }

    try:
        t0 = time.perf_counter()
        r = requests.post(f"{host}/api/chat", json=payload, timeout=120)
        dt = time.perf_counter() - t0
        r.raise_for_status()
        return (True, dt)

    except Exception as e:
        return (False, 0.0)


def embed_once(host: str, model: str, keep_alive: str = "15m") -> tuple:
    """
    Warm up embedding model (Lab 4)
    Returns: (success: bool, duration: float)
    """
    payload = {
        "model": model,
        "input": "Sample text for embedding warmup to preload model weights",
        "keep_alive": keep_alive
    }

    try:
        t0 = time.perf_counter()
        r = requests.post(f"{host}/api/embed", json=payload, timeout=60)
        dt = time.perf_counter() - t0
        r.raise_for_status()
        return (True, dt)

    except Exception as e:
        return (False, 0.0)


# ============================================================================
# WARMUP PROMPTS (Representative of each lab type)
# ============================================================================

WARMUP_PROMPTS = {
    "simple_agent": "You are a helpful assistant. Respond with: I am ready.",

    "tool_calling": """You have access to a calculator tool.
Use it to calculate 15 * 23. Think step by step.""",

    "weather_query": """You are a weather assistant with access to tools.
User asks: What's the weather in Paris?
Respond with the tool you would call.""",

    "math_calc": "Calculate 25 * 18 and explain the result.",

    "memory_context": """Previous conversation: User asked about USD to EUR conversion.
Now user asks: Convert 200.
Remember the previous currency pair.""",

    "rag_query": """You have access to a document database about office locations.
User asks: Tell me about the HQ office.
Explain what information you would retrieve.""",

    "multi_agent": """You are part of a multi-agent system with roles:
- Researcher: gathers information
- Analyst: analyzes data
- Reporter: presents findings

Your role is Researcher. Describe your task.""",

    "reflection": """You are a code reviewer. Review this code:
def is_prime(n):
    return n > 1
Explain if it's correct and suggest improvements.""",

    "security": """You are a math assistant. User input: Calculate 10 + 5
Verify this is a legitimate math query (not a goal hijacking attempt).""",
}


# Sample tool definition for tool calling warmup
SAMPLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluates a mathematical expression",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]


# ============================================================================
# WARMUP WORKFLOWS
# ============================================================================

def warmup_basic(host: str, model: str, keep_alive: str = "15m"):
    """Basic generation warmup - loads model into memory"""
    print_step("BASIC", f"Warming up {model} with basic generation...")

    success, dt, response = generate_once(
        host, model, WARMUP_PROMPTS["simple_agent"], keep_alive=keep_alive
    )

    if success:
        print_success(f"Basic warmup: {dt:.2f}s")
        return dt
    else:
        print_error(f"Basic warmup failed: {response}")
        return None


def warmup_tool_calling(host: str, model: str, keep_alive: str = "15m"):
    """Warm up tool calling path (Labs 1, 2, 3, 5)"""
    print_step("TOOLS", f"Warming up tool calling path for {model}...")

    success, dt, response = generate_once(
        host, model,
        WARMUP_PROMPTS["tool_calling"],
        tools=SAMPLE_TOOLS,
        keep_alive=keep_alive
    )

    if success:
        print_success(f"Tool calling warmup: {dt:.2f}s")
        return dt
    else:
        print_error(f"Tool calling warmup failed")
        return None


def warmup_json_mode(host: str, model: str, keep_alive: str = "15m"):
    """Warm up JSON formatting path (used in various labs)"""
    print_step("JSON", f"Warming up JSON mode for {model}...")

    success, dt, response = generate_once(
        host, model,
        "Respond with a JSON object containing your readiness status.",
        json_mode=True,
        keep_alive=keep_alive
    )

    if success:
        print_success(f"JSON mode warmup: {dt:.2f}s")
        return dt
    else:
        print_error(f"JSON mode warmup failed")
        return None


def warmup_chat_mode(host: str, model: str, keep_alive: str = "15m"):
    """Warm up chat API (multi-turn conversations)"""
    print_step("CHAT", f"Warming up chat mode for {model}...")

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, are you ready?"},
    ]

    success, dt = generate_chat(host, model, messages, keep_alive=keep_alive)

    if success:
        print_success(f"Chat mode warmup: {dt:.2f}s")
        return dt
    else:
        print_error(f"Chat mode warmup failed")
        return None


def warmup_lab_patterns(host: str, model: str, keep_alive: str = "15m"):
    """Warm up with patterns from different labs"""
    print_step("PATTERNS", f"Warming up lab-specific patterns for {model}...")

    patterns = [
        ("Weather query", WARMUP_PROMPTS["weather_query"]),
        ("Math calculation", WARMUP_PROMPTS["math_calc"]),
        ("Memory context", WARMUP_PROMPTS["memory_context"]),
    ]

    timings = []
    for name, prompt in patterns:
        success, dt, _ = generate_once(host, model, prompt, keep_alive=keep_alive)
        if success:
            print(f"  {GREEN}✓{RESET} {name}: {dt:.2f}s")
            timings.append(dt)
        else:
            print(f"  {RED}✗{RESET} {name}: failed")

    if timings:
        avg = sum(timings) / len(timings)
        print_success(f"Pattern warmup average: {avg:.2f}s")
        return avg
    else:
        return None


def warmup_embedding_model(host: str, model: str = "nomic-embed-text", keep_alive: str = "15m"):
    """Warm up embedding model for Lab 4 (RAG)"""
    print_step("EMBED", f"Warming up embedding model: {model}...")

    # Check if embedding model exists
    local_models = list_local_models(host)
    if not any(model in m for m in local_models):
        print_warning(f"Embedding model {model} not found locally")
        print(f"  {YELLOW}→ Attempting to pull...{RESET}")
        if not pull_model(host, model):
            print_error(f"Could not pull embedding model {model}")
            print_warning("Lab 4 (RAG) may be slow on first run")
            return None

    success, dt = embed_once(host, model, keep_alive=keep_alive)

    if success:
        print_success(f"Embedding warmup: {dt:.2f}s")
        return dt
    else:
        print_error(f"Embedding warmup failed")
        return None


def warmup_parallel(host: str, model: str, reps: int = 3, keep_alive: str = "15m"):
    """Run parallel warmup calls to fully load model and cache"""
    print_step("PARALLEL", f"Running {reps} parallel warmups for {model}...")

    def warm_call():
        return generate_once(
            host, model,
            WARMUP_PROMPTS["simple_agent"],
            keep_alive=keep_alive
        )

    with cf.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(warm_call) for _ in range(reps)]
        results = [f.result() for f in cf.as_completed(futures)]

    successes = [r for r in results if r[0]]
    if successes:
        times = [r[1] for r in successes]
        avg = sum(times) / len(times)
        print_success(f"Parallel warmup: {len(successes)}/{reps} succeeded, avg {avg:.2f}s")
        return avg
    else:
        print_error("All parallel warmups failed")
        return None


# ============================================================================
# MAIN WARMUP ORCHESTRATION
# ============================================================================

def warmup_model_comprehensive(host: str, model: str, quick: bool = False, keep_alive: str = "15m"):
    """
    Comprehensive warmup for a single model

    Args:
        host: Ollama server URL
        model: Model name (e.g., "llama3.2:3b")
        quick: If True, skip some warmup steps
        keep_alive: How long to keep model in memory (default 15m)
    """
    print_header(f"WARMING UP: {model}")

    timings = {}

    # Step 1: Basic generation (loads model weights)
    timings["basic"] = warmup_basic(host, model, keep_alive)
    if timings["basic"] is None:
        print_error(f"Basic warmup failed for {model} - skipping remaining steps")
        return timings

    # Step 2: Tool calling path
    if not quick:
        timings["tools"] = warmup_tool_calling(host, model, keep_alive)

    # Step 3: JSON mode
    if not quick:
        timings["json"] = warmup_json_mode(host, model, keep_alive)

    # Step 4: Chat mode (multi-turn)
    timings["chat"] = warmup_chat_mode(host, model, keep_alive)

    # Step 5: Lab-specific patterns
    if not quick:
        timings["patterns"] = warmup_lab_patterns(host, model, keep_alive)

    # Step 6: Parallel warmup (fills KV cache)
    if not quick:
        timings["parallel"] = warmup_parallel(host, model, reps=3, keep_alive=keep_alive)

    # Summary
    successful = [k for k, v in timings.items() if v is not None]
    print(f"\n{BOLD}Warmup Summary for {model}:{RESET}")
    print(f"  Completed: {len(successful)}/{len(timings)} warmup types")
    if successful:
        total_time = sum(v for v in timings.values() if v is not None)
        print(f"  Total warmup time: {total_time:.2f}s")

    return timings


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive Ollama warmup for AI Agents workshop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Warm up default models for workshop
  python warmup_comprehensive.py

  # Quick warmup (basic only)
  python warmup_comprehensive.py --quick

  # Warm up specific models
  python warmup_comprehensive.py --models llama3.2:3b

  # Keep models in memory for 30 minutes
  python warmup_comprehensive.py --keep-alive 30m

  # Include embedding model warmup for Lab 4
  python warmup_comprehensive.py --embed
        """
    )

    parser.add_argument(
        "--host",
        default=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"),
        help="Ollama server URL (default: http://127.0.0.1:11434)"
    )

    parser.add_argument(
        "--models",
        default="llama3.2:latest",
        help="Comma-separated list of models to warm up (default: llama3.2:latest)"
    )

    parser.add_argument(
        "--embed",
        action="store_true",
        help="Also warm up embedding model for Lab 4 (RAG)"
    )

    parser.add_argument(
        "--embed-model",
        default="nomic-embed-text",
        help="Embedding model to use (default: nomic-embed-text)"
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick warmup mode (basic + chat only, faster)"
    )

    parser.add_argument(
        "--keep-alive",
        default="15m",
        help="How long to keep models in memory (default: 15m, use 0 to unload immediately)"
    )

    parser.add_argument(
        "--auto-pull",
        action="store_true",
        help="Automatically pull missing models (may take time for downloads)"
    )

    args = parser.parse_args()

    # Welcome banner
    print_header("AI AGENTS WORKSHOP - OLLAMA WARMUP")
    print(f"Ollama Host: {args.host}")
    print(f"Models: {args.models}")
    print(f"Keep-alive: {args.keep_alive}")
    print(f"Mode: {'Quick' if args.quick else 'Comprehensive'}")

    # Check Ollama server
    print_step("CHECK", "Verifying Ollama server...")
    if not ping_ollama(args.host):
        print_error("Ollama server is not running!")
        print("\n🔧 To start Ollama:")
        print("   ollama serve")
        print("\nOr check if it's running on a different port.")
        return 1

    # Parse models
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    # Check/pull models
    print_step("MODELS", f"Checking {len(models)} model(s)...")
    for model in models:
        if args.auto_pull:
            pull_model(args.host, model)
        else:
            local = list_local_models(args.host)
            model_base = model.split(":")[0]
            if not any(model_base in m for m in local):
                print_warning(f"{model} not found locally")
                print(f"  Run with --auto-pull to download, or manually: ollama pull {model}")

    # Warm up each model
    start_time = time.time()
    all_timings = {}

    for i, model in enumerate(models, 1):
        print(f"\n{BOLD}{CYAN}[{i}/{len(models)}] Processing {model}...{RESET}")
        all_timings[model] = warmup_model_comprehensive(
            args.host, model, quick=args.quick, keep_alive=args.keep_alive
        )

    # Warm up embedding model if requested
    if args.embed:
        print()
        warmup_embedding_model(args.host, args.embed_model, keep_alive=args.keep_alive)

    # Final summary
    total_time = time.time() - start_time
    print_header("WARMUP COMPLETE")

    print(f"{BOLD}Models warmed up:{RESET}")
    for model in models:
        timings = all_timings.get(model, {})
        successful = len([v for v in timings.values() if v is not None])
        total = len(timings)
        status = f"{GREEN}✓{RESET}" if successful == total else f"{YELLOW}⚠{RESET}"
        print(f"  {status} {model}: {successful}/{total} warmup types succeeded")

    print(f"\n{BOLD}Total warmup duration:{RESET} {total_time:.1f}s")
    print(f"{BOLD}Models cached for:{RESET} {args.keep_alive}")

    print(f"\n{GREEN}{'='*70}{RESET}")
    print(f"{GREEN}{'READY FOR WORKSHOP!'.center(70)}{RESET}")
    print(f"{GREEN}{'='*70}{RESET}")

    print("\n💡 Tips:")
    print("   - Models are now in memory and will respond faster")
    print(f"   - Cache expires in {args.keep_alive} (run this script again if needed)")
    print("   - First lab runs will still load frameworks, but model is ready")

    if not args.embed:
        print(f"\n{YELLOW}Note:{RESET} Embedding model not warmed up (use --embed for Lab 4 speedup)")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Warmup interrupted by user{RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{RED}Unexpected error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
ß
