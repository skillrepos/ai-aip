#!/usr/bin/env python3
import argparse
import concurrent.futures as cf
import json
import os
import time
from pathlib import Path

import requests

def parse_args():
    p = argparse.ArgumentParser(description="Ollama warmup utility")
    p.add_argument("--host", default=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"))
    p.add_argument("--models", required=True, help="Comma-separated list of LLM models")
    p.add_argument("--embed-model", default="", help="Embedding model name (optional)")
    p.add_argument("--prompt-file", default="extra/curr_conv_agent.txt")
    p.add_argument("--reps", type=int, default=3)
    p.add_argument("--concurrency", type=int, default=2)
    p.add_argument("--json", default="auto", choices=["auto", "true", "false"],
                   help="Warm JSON formatter path: auto|true|false")
    return p.parse_args()

def read_prompt(prompt_file: str) -> str:
    p = Path(prompt_file)
    if not p.exists():
        # Fallback generic warm prompt if file not present
        return "You are a helpful assistant. Reply briefly to confirm readiness."
    return p.read_text(encoding="utf-8")[:4000]  # keep it small for warmup

def ping(host: str):
    try:
        r = requests.get(f"{host}/api/version", timeout=2)
        r.raise_for_status()
        return True
    except Exception:
        return False

def gen_once(host: str, model: str, prompt: str, json_mode: bool):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            # keep these small/fast; we just want the graph loaded and paths compiled
            "temperature": 0.0,
            "top_k": 1,
            "num_predict": 32
        },
        "keep_alive": "10m"
    }
    if json_mode:
        # Exercise the JSON formatting path Ollama provides
        payload["format"] = "json"
        # Nudge the model to actually emit valid JSON quickly
        payload["prompt"] = (
            prompt + "\n\n"
            "Return a minimal valid JSON object summarizing your intent, e.g. "
            '{"status":"ready"}'
        )

    t0 = time.perf_counter()
    r = requests.post(f"{host}/api/generate", json=payload, timeout=60)
    dt = time.perf_counter() - t0
    r.raise_for_status()
    _ = r.json().get("response", "")
    return dt

def embed_once(host: str, model: str):
    payload = {
        "model": model,
        "input": "warmup embedding path; short text",
        "keep_alive": "10m"
    }
    t0 = time.perf_counter()
    r = requests.post(f"{host}/api/embeddings", json=payload, timeout=60)
    dt = time.perf_counter() - t0
    r.raise_for_status()
    return dt

def warm_models(host: str, models: list[str], prompt: str, reps: int, concurrency: int, use_json: str):
    # Decide JSON mode: if 'auto', try to detect from the prompt (simple heuristic)
    json_mode = None
    if use_json == "true":
        json_mode = True
    elif use_json == "false":
        json_mode = False
    else:
        # auto: if the prompt looks like it primes a tool/JSON path, enable it
        lowered = prompt.lower()
        json_mode = any(k in lowered for k in ["json", "tool", "function", "schema"])

    print(f"[warmup] JSON-mode: {json_mode}")

    timings: dict[str, list[float]] = {m: [] for m in models}

    for m in models:
        # First single warm to instantiate weights/mmap on CPU/GPU
        try:
            dt = gen_once(host, m, prompt, json_mode)
            timings[m].append(dt)
            print(f"[warmup] {m}: first call {dt:.2f}s")
        except Exception as e:
            print(f"[warmup] ERROR first call for {m}: {e}")
            continue

        # Additional reps with limited concurrency to fill kv-cache and tokenizer paths
        remaining = max(0, reps - 1)
        if remaining:
            with cf.ThreadPoolExecutor(max_workers=concurrency) as ex:
                futs = [ex.submit(gen_once, host, m, prompt, json_mode)
                        for _ in range(remaining)]
                for fut in cf.as_completed(futs):
                    try:
                        timings[m].append(fut.result())
                    except Exception as e:
                        print(f"[warmup] WARN warm call failed for {m}: {e}")

    return timings

def main():
    args = parse_args()

    if not ping(args.host):
        raise SystemExit(f"[warmup] ERROR: Ollama host not reachable at {args.host}")

    models = [m.strip() for m in args.models.split(",") if m.strip()]

    prompt = read_prompt(args.prompt_file)
    print(f"[warmup] Using prompt from {args.prompt_file} ({len(prompt)} chars)")

    timings = warm_models(args.host, models, prompt, args.reps, args.concurrency, args.json)

    # Embedding model warmup (optional)
    if args.embed_model:
        try:
            dt = embed_once(args.host, args.embed_model)
            print(f"[warmup] embed {args.embed_model}: {dt:.2f}s")
        except Exception as e:
            print(f"[warmup] WARN embedding warmup failed for {args.embed_model}: {e}")

    # Summary
    print("\n[warmup] summary (seconds):")
    for m, arr in timings.items():
        if arr:
            print(f"  {m}: first={arr[0]:.2f}, median={sorted(arr)[len(arr)//2]:.2f}, all={','.join(f'{x:.2f}' for x in arr)}")
        else:
            print(f"  {m}: no timings (errors above)")

if __name__ == "__main__":
    main()
