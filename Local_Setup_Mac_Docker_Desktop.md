# Local Setup Guide for Mac

This guide will help you run the AI-AIP workshop devcontainer locally on your Mac instead of using GitHub Codespaces.

## Prerequisites

### System Requirements
- macOS (Intel or Apple Silicon)
- At least 4 CPU cores
- 16GB RAM minimum
- 32GB free disk space

### Required Software

#### 1. Install Docker Desktop
- Download from: https://www.docker.com/products/docker-desktop
- Choose the appropriate version:
  - **Apple Silicon (M1/M2/M3)**: Download "Mac with Apple chip"
  - **Intel Mac**: Download "Mac with Intel chip"
- Install by dragging Docker.app to Applications
- Launch Docker Desktop and complete the setup
- Ensure Docker Desktop is running (you'll see the whale icon in your menu bar)

#### 2. Install Visual Studio Code
- Download from: https://code.visualstudio.com/
- Open the downloaded .zip file
- Drag Visual Studio Code to your Applications folder
- Launch VS Code

#### 3. Install Dev Containers Extension
- Open VS Code
- Press `Cmd+Shift+X` to open Extensions
- Search for "Dev Containers" (published by Microsoft)
- Click **Install**

## Setup Steps

### 1. Clone the Repository
Open Terminal and run:
```bash
git clone https://github.com/skillrepos/ai-aip.git
cd ai-aip
```

### 2. Open in VS Code
```bash
code .
```

### 3. Reopen in Container
When VS Code opens, you should see a notification asking if you want to "Reopen in Container":
- Click **Reopen in Container**

If you don't see the notification:
- Press `Cmd+Shift+P` to open the Command Palette
- Type "Dev Containers: Reopen in Container"
- Press Enter

### 4. Wait for Initial Setup
The first time you open the container, it will take **10-15 minutes** to:
- Build the Docker container
- Set up the Python environment
- Install all dependencies
- Install Ollama
- Download required AI models

You can monitor progress in the VS Code terminal.

### 5. Verify Ollama is Running
After the container finishes building, Ollama should start automatically. To verify:
```bash
ollama list
```

If Ollama is not running, start it manually:
```bash
ollama serve &
```

### 6. Run the Warmup Script (Recommended)
To ensure everything is working correctly:
```bash
python scripts/warmup_comprehensive.py
```

## Troubleshooting

### Docker Desktop Not Running
If you see "Docker is not running" errors:
- Check that Docker Desktop is running (whale icon in menu bar)
- Try restarting Docker Desktop
- Ensure you've completed the Docker Desktop setup wizard

### Container Build Fails
- Ensure you have enough disk space (32GB minimum free)
- Check Docker Desktop has sufficient resources allocated:
  - Open Docker Desktop → Settings → Resources
  - Ensure at least 4 CPUs and 8GB memory are allocated

### Ollama Models Not Downloaded
If models are missing:
```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### Port Already in Use
If you see port conflict errors:
- Check what's using the port: `lsof -i :PORT_NUMBER`
- Stop the conflicting service or change the port in `.devcontainer/devcontainer.json`

## Next Steps

Once setup is complete, you're ready to start the workshop! Refer to the main [README.md](README.md) for lab instructions.

## Stopping the Container

When you're done working:
- Close VS Code or
- Press `Cmd+Shift+P` and select "Dev Containers: Reopen Folder Locally"

Docker Desktop can continue running in the background or be quit from the menu bar icon.
