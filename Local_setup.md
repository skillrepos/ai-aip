# Local Environment Setup (No Codespaces) 
**Not guaranteed to work on all systems/setup - recommended environment is GitHub Codespace as described in README.md**

This guide explains how to run the **Implementing AI Agents in Python** labs from this repository **without GitHub Codespaces**. It mirrors the key parts of the dev container so you can work locally on macOS, Linux, or Windows.



---

## 1) Prerequisites

Install the following:

- **Python** 3.10+ (3.11 recommended)
- **Git**
- **Ollama** (local model runtime): https://ollama.com/download
- **Node.js LTS** *(optional; install if any labs/tools need Node or node-gyp)*

After installing Ollama, ensure the `ollama` command is available on your PATH.

---

## 2) Clone the repository

```bash
git clone https://github.com/skillrepos/ai-aip.git
cd ai-aip
```

---

## 3) Create and activate a virtual environment

> The dev container uses a project-local interpreter at `.venv`. We'll mirror that.

```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Verify:
```bash
python --version
which python    # macOS/Linux
where python    # Windows
```

---

## 4) Install Python dependencies

If the repo includes helper scripts (e.g., `scripts/pysetup.sh`), prefer using them. Otherwise install from requirements files.

### Option A — Use setup script (if present)
```bash
# macOS/Linux or Windows via Git Bash/WSL
bash -i scripts/pysetup.sh py_env
```

### Option B — Manual install from requirements
```bash
pip install --upgrade pip wheel
# If a single file exists:
# pip install -r requirements.txt
# If multiple pinned files exist:
# pip install -r requirements/base.txt
# pip install -r requirements/dev.txt
```

---

## 5) Start the Ollama service

Open a new terminal or run in the background:

```bash
# Start in background (macOS/Linux)
ollama serve &

# Or foreground (any OS)
# ollama serve
```

Confirm it is listening (default `127.0.0.1:11434`):
```bash
curl http://127.0.0.1:11434/api/tags
```
You should see JSON output.

---

## 6) Pull the required model

The labs use the **llama3.2:latest** model. Pull it once:

```bash
ollama pull llama3.2:latest
```

You can verify it is available:
```bash
ollama list
```

---

## 7) Run the labs

Open the lab guide and follow the steps, ensuring your virtual environment is active and Ollama is running:

```bash
# Example editor commands
code labs.md        # VS Code
# or open in any editor
```

If a specific lab includes a Python entry point or CLI, run it from the repository root with your venv active. For example:
```bash
python -m your_module_or_script  # replace with the actual module/script
```

---

## 8) Optional: Editor/IDE tips

If you're using VS Code:

- **Interpreter**: Select the `.venv` Python interpreter (`Python: Select Interpreter`).
- **Extensions**: If labs reference Mermaid or PDF previews, install those extensions locally.
- **Terminal**: Use an integrated terminal with the venv activated for running commands.

---

## 9) Troubleshooting

**`ollama: command not found`**  
Reinstall Ollama or ensure it is on your PATH. Start `ollama serve` before running any code that calls the Ollama API.

**Model not found**  
Run `ollama pull llama3.2:latest` and ensure the `ollama serve` process is running in a terminal.

**Package build errors (e.g., node-gyp)**  
Install **Node.js LTS** and necessary build tools for your OS. On Windows, make sure Build Tools for Visual Studio (or the `vs_BuildTools.exe`) are installed if native extensions are needed.

**Wrong Python environment**  
Make sure `.venv` is activated in the shell where you run commands. In VS Code, select the interpreter from `.venv`.

---

## 10) Keeping parity with the dev container

The dev container typically does the following automatically:
- Uses a local project interpreter (e.g., `.venv`)
- Installs Python dependencies
- Starts `ollama serve` on container start
- Pulls models used in the labs

The steps above mirror that lifecycle locally: **create venv → install deps → start Ollama → pull model → run labs**.

---

## 11) Clean up

To remove the virtual environment and cached models later:

```bash
# Remove venv
deactivate 2>/dev/null || true
rm -rf .venv

# Remove ollama model (optional)
ollama rm llama3.2:latest
```

---

## 12) Quick Start (copy/paste)

```bash
# Clone
git clone https://github.com/skillrepos/ai-aip.git
cd ai-aip

# Python venv
python3 -m venv .venv && source .venv/bin/activate  # macOS/Linux
# Windows PowerShell:
# python -m venv .venv ; .\.venv\Scripts\Activate.ps1

# Deps
pip install --upgrade pip wheel
# pip install -r requirements.txt         # if present
# or use: bash -i scripts/pysetup.sh py_env  # if present

# Ollama
ollama serve &
ollama pull llama3.2:latest

# Run labs
# open labs.md in your editor and follow the steps
```

---


