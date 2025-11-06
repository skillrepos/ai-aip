  Prerequisites

  1. Install Docker Desktop
    - Download from https://www.docker.com/products/docker-desktop
    - Ensure it's running before proceeding
    - Your machine should have at least:
        - 4 CPU cores
      - 16GB RAM
      - 32GB free storage
  2. Install VS Code
    - Download from https://code.visualstudio.com/
  3. Install the Dev Containers extension
    - Open VS Code
    - Go to Extensions (Cmd+Shift+X on Mac)
    - Search for "Dev Containers" (by Microsoft)
    - Click Install

  Steps to Run Locally

  1. Clone this repository
  git clone https://github.com/skillrepos/ai-aip.git
  cd ai-aip
  2. Open in VS Code
  code .
  3. Reopen in Container
    - VS Code should detect the devcontainer and prompt you to "Reopen in Container"
    - If not prompted, press Cmd+Shift+P and search for "Dev Containers: Reopen in Container"
  4. Wait for setup (10-15 minutes first time)
    - The container will build and run the postCreateCommand which:
        - Sets up Python environment
      - Installs dependencies
      - Installs Ollama
      - Downloads AI models
  5. Verify Ollama is running
    - After container starts, Ollama should start automatically
    - If needed, manually run: ollama serve &
  6. Run the warmup script (recommended)
  python scripts/warmup.py

  That's it! You'll have the same environment as Codespaces but running locally on your machine.
