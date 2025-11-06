# Local Setup Guide for Windows

This guide will help you run the AI-AIP workshop devcontainer locally on your Windows machine instead of using GitHub Codespaces.

## Prerequisites

### System Requirements
- Windows 10 64-bit (version 2004 or higher) or Windows 11
- At least 4 CPU cores
- 16GB RAM minimum
- 32GB free disk space
- WSL 2 (Windows Subsystem for Linux 2)

### Required Software

#### 1. Enable WSL 2
Open PowerShell as Administrator and run:
```powershell
wsl --install
```

After installation completes, restart your computer. WSL 2 with Ubuntu will be installed by default.

To verify WSL 2 is installed:
```powershell
wsl --list --verbose
```

#### 2. Install Docker Desktop
- Download from: https://www.docker.com/products/docker-desktop
- Run the installer
- During installation, ensure "Use WSL 2 instead of Hyper-V" is selected
- Restart your computer after installation
- Launch Docker Desktop and complete the setup
- Ensure Docker Desktop is running (you'll see the whale icon in your system tray)

**Important**: In Docker Desktop settings:
- Go to Settings → General
- Ensure "Use the WSL 2 based engine" is checked
- Go to Settings → Resources → WSL Integration
- Enable integration with your Ubuntu distribution

#### 3. Install Visual Studio Code
- Download from: https://code.visualstudio.com/
- Run the installer
- During installation, select:
  - "Add to PATH"
  - "Register Code as an editor for supported file types"
- Launch VS Code

#### 4. Install Dev Containers Extension
- Open VS Code
- Press `Ctrl+Shift+X` to open Extensions
- Search for "Dev Containers" (published by Microsoft)
- Click **Install**

#### 5. Install WSL Extension (Recommended)
- In VS Code Extensions
- Search for "WSL" (published by Microsoft)
- Click **Install**

## Setup Steps

### 1. Clone the Repository
Open PowerShell or Windows Terminal and run:
```powershell
git clone https://github.com/skillrepos/ai-aip.git
cd ai-aip
```

Alternatively, clone directly in WSL:
```bash
wsl
git clone https://github.com/skillrepos/ai-aip.git
cd ai-aip
```

### 2. Open in VS Code
From the repository directory:
```powershell
code .
```

### 3. Reopen in Container
When VS Code opens, you should see a notification asking if you want to "Reopen in Container":
- Click **Reopen in Container**

If you don't see the notification:
- Press `Ctrl+Shift+P` to open the Command Palette
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

### WSL 2 Not Installed or Wrong Version
Check your WSL version:
```powershell
wsl --list --verbose
```

If you see version 1, upgrade to version 2:
```powershell
wsl --set-version Ubuntu 2
```

### Docker Desktop Not Running
If you see "Docker is not running" errors:
- Check that Docker Desktop is running (whale icon in system tray)
- Ensure WSL 2 integration is enabled in Docker Desktop settings
- Try restarting Docker Desktop
- Restart the WSL 2 service:
  ```powershell
  wsl --shutdown
  ```
  Then restart Docker Desktop

### Container Build Fails
- Ensure you have enough disk space (32GB minimum free)
- Check Docker Desktop has sufficient resources allocated:
  - Open Docker Desktop → Settings → Resources
  - Ensure at least 4 CPUs and 8GB memory are allocated
- Ensure your antivirus isn't blocking Docker

### "Cannot connect to Docker daemon" Error
- Verify Docker Desktop is running
- In Docker Desktop, go to Settings → Resources → WSL Integration
- Ensure your Ubuntu distribution is enabled
- Run in PowerShell:
  ```powershell
  wsl --shutdown
  ```
  Then restart Docker Desktop

### Ollama Models Not Downloaded
If models are missing:
```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### Port Already in Use
If you see port conflict errors:
- Check what's using the port in PowerShell:
  ```powershell
  netstat -ano | findstr :PORT_NUMBER
  ```
- Stop the conflicting service or change the port in `.devcontainer/devcontainer.json`

### File Permission Issues
If you encounter permission errors, ensure your repository is cloned in a location accessible to WSL:
- Recommended: Clone inside WSL (e.g., `/home/username/ai-aip`)
- Avoid: Windows filesystem paths like `C:\Users\...`

## Performance Tips

For better performance:
1. Clone repositories inside the WSL filesystem (not Windows filesystem)
2. Allocate more resources to Docker in Settings → Resources
3. Close unnecessary applications to free up RAM

## Next Steps

Once setup is complete, you're ready to start the workshop! Refer to the main [README.md](README.md) for lab instructions.

## Stopping the Container

When you're done working:
- Close VS Code or
- Press `Ctrl+Shift+P` and select "Dev Containers: Reopen Folder Locally"

Docker Desktop can continue running in the background or be quit from the system tray icon.

## Additional Resources

- [Docker Desktop WSL 2 Backend](https://docs.docker.com/desktop/windows/wsl/)
- [Developing in WSL with VS Code](https://code.visualstudio.com/docs/remote/wsl)
- [Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
