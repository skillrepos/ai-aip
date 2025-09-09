#!/usr/bin/env python3
"""
Model Warmup Script for AI Agents

This script "warms up" the llama3.2 model by making a simple request to it,
ensuring it's loaded in memory for faster subsequent agent responses.
"""

import asyncio
import ollama
import sys
import time
from openai import OpenAI

# ANSI color codes for output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

def warmup_langchain_ollama():
    """Warmup using langchain_ollama (for agents like agent1.py)"""
    try:
        from langchain_ollama import ChatOllama
        print(f"{CYAN}Warming up langchain_ollama interface...{RESET}")
        
        llm = ChatOllama(model="llama3.2", temperature=0.0)
        start_time = time.time()
        
        # Simple warmup message
        response = llm.invoke("Hello")
        
        end_time = time.time()
        print(f"{GREEN}✓ langchain_ollama warmup completed in {end_time - start_time:.2f}s{RESET}")
        return True
    except Exception as e:
        print(f"{RED}✗ langchain_ollama warmup failed: {e}{RESET}")
        return False

def warmup_openai_client():
    """Warmup using OpenAI client (for agents like rag_agent.py)"""
    try:
        print(f"{CYAN}Warming up OpenAI client interface...{RESET}")
        
        client = OpenAI(
            base_url='http://localhost:11434/v1',
            api_key='ollama',
        )
        
        start_time = time.time()
        
        completion = client.chat.completions.create(
            model="llama3.2",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        end_time = time.time()
        print(f"{GREEN}✓ OpenAI client warmup completed in {end_time - start_time:.2f}s{RESET}")
        return True
    except Exception as e:
        print(f"{RED}✗ OpenAI client warmup failed: {e}{RESET}")
        return False

async def warmup_async_ollama():
    """Warmup using async ollama client (for agents like learning.py, goal.py)"""
    try:
        print(f"{CYAN}Warming up async ollama client...{RESET}")
        
        client = ollama.AsyncClient()
        start_time = time.time()
        
        response = await client.chat(
            model='llama3.2',
            messages=[{'role': 'user', 'content': 'Hello'}],
        )
        
        end_time = time.time()
        print(f"{GREEN}✓ Async ollama warmup completed in {end_time - start_time:.2f}s{RESET}")
        return True
    except Exception as e:
        print(f"{RED}✗ Async ollama warmup failed: {e}{RESET}")
        return False

def warmup_litellm_model():
    """Warmup using LiteLLMModel with ollama_chat (for smolagents)"""
    try:
        from smolagents import LiteLLMModel, ToolCallingAgent
        print(f"{CYAN}Warming up LiteLLMModel interface...{RESET}")
        
        model = LiteLLMModel(
            model_id="ollama_chat/llama3.2",
            api_base="http://localhost:11434",
            num_ctx=4096,
            temperature=0.0,
        )
        
        # Create a simple agent without tools for warmup
        agent = ToolCallingAgent(tools=[], model=model)
        
        start_time = time.time()
        
        # Make a simple test call through the agent
        response = agent.run("Hello")
        
        end_time = time.time()
        print(f"{GREEN}✓ LiteLLMModel warmup completed in {end_time - start_time:.2f}s{RESET}")
        return True
    except Exception as e:
        print(f"{RED}✗ LiteLLMModel warmup failed: {e}{RESET}")
        return False

def check_ollama_status():
    """Check if Ollama server is running"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print(f"{GREEN}✓ Ollama server is running{RESET}")
            return True
        else:
            print(f"{RED}✗ Ollama server returned status {response.status_code}{RESET}")
            return False
    except Exception as e:
        print(f"{RED}✗ Ollama server is not reachable: {e}{RESET}")
        return False

async def main():
    print(f"{BOLD}{CYAN}AI Agents Model Warmup Script{RESET}")
    print("=" * 40)
    
    # Check if Ollama server is running
    print(f"{YELLOW}Checking Ollama server status...{RESET}")
    if not check_ollama_status():
        print(f"{RED}Error: Ollama server is not running. Please start it first with 'ollama serve'{RESET}")
        sys.exit(1)
    
    print(f"\n{YELLOW}Starting model warmup process...{RESET}")
    total_start = time.time()
    
    success_count = 0
    total_tests = 4
    
    # Warmup different client interfaces
    if warmup_langchain_ollama():
        success_count += 1
    
    if warmup_openai_client():
        success_count += 1
        
    if await warmup_async_ollama():
        success_count += 1
        
    if warmup_litellm_model():
        success_count += 1
    
    total_end = time.time()
    
    print("\n" + "=" * 40)
    print(f"{BOLD}Warmup Summary:{RESET}")
    print(f"✓ {success_count}/{total_tests} interfaces warmed up successfully")
    print(f"⏱  Total warmup time: {total_end - total_start:.2f}s")
    
    if success_count == total_tests:
        print(f"{GREEN}{BOLD}🚀 Model is now warmed up and ready for fast agent responses!{RESET}")
        sys.exit(0)
    else:
        print(f"{YELLOW}⚠  Some interfaces failed to warmup, but agents should still work{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
