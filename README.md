# Implementing AI Agents in Python
## Using frameworks, MCP, and RAG for agentic AI

Repository for Implementing AI Agents in Python hands-on workshop

These instructions will guide you through configuring a GitHub Codespaces environment that you can use to run the course labs. 

<br><br>

**1. Click on the button below to start a new codespace from this repository.**

Click here ➡️  [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/skillrepos/ai-aip?quickstart=1)

<br><br>

**2. Then click on the option to create a new codespace.**

![Creating new codespace from button](./images/aip1.png?raw=true "Creating new codespace from button")

This will run for a long time (10 or more minutes) while it gets everything ready.

After the initial startup, it will run a script to setup the python environment, install needed python pieces, install Ollama, and then download the models we will use. This will take several more minutes to run. It will look like this while this is running.

![Final prep](./images/aip2.png?raw=true "Final prep")

The codespace is ready to use when you see a prompt like the one shown below in its terminal.

![Ready to use](./images/aip3.png?raw=true "Ready to use")

<br><br>

**3. Open up the *labs.md* file so you can follow along with the labs.**
You can either open it in a separate browser instance or open it in the codespace. 
![Opening labs](./images/aip4.png?raw=true "Opening labs")

**Now, you are ready for the labs!**

<br><br>

**4. (Optional, but recommended) Run the script below to "warm up" access for the local model to reduce response times for some of the labs.**
In the codespace *TERMINAL*, run the command below.

```
scripts/warmup.sh
```

![LLM warmup](./images/aip16.png?raw=true "LLM warmup")

<br><br>

**5. (Optional, but recommended) Change your codespace's default timeout from 30 minutes to longer (60 for half-day sessions, 90 for deep dive sessions).**
To do this, when logged in to GitHub, go to https://github.com/settings/codespaces and scroll down on that page until you see the *Default idle timeout* section. Adjust the value as desired.

![Changing codespace idle timeout value](./images/aa4.png?raw=true "Changing codespace idle timeout value")

**NOTE: If your codespace times out and you need to reopen it**

1. Go to https://github.com/your_github_userid/codespaces
2. Find the codespace in the list, right-click, and select *Open in browser*
3. Run the *ollama serve &* command to restart Ollama
```
ollama serve &
```

<br/><br/>


