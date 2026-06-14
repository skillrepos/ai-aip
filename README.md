# Implementing AI Agents in Python
## Using frameworks, MCP, and RAG for agentic AI

Repository for Implementing AI Agents in Python hands-on workshop

These instructions will guide you through configuring a GitHub Codespaces environment that you can use to run the course labs. 

<br><br>

**1. Change your codespace's default timeout from 30 minutes to longer.**
To do this, when logged in to GitHub, go to https://github.com/settings/codespaces and scroll down on that page until you see the *Default idle timeout* section. Adjust the value as desired.

<br><br>

![Changing codespace idle timeout value](./images/aa4.png?raw=true "Changing codespace idle timeout value")

<br><br>

**2. Click on the button below to start a new codespace from this repository.**

Click here ➡️  [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/skillrepos/ai-aip?quickstart=1)

<br><br>

**3. Then click on the option to create a new codespace.**

![Creating new codespace from button](./images/aip1.png?raw=true "Creating new codespace from button")

This will run for several minutes while it gets everything ready.

After the initial startup, it will run a script to setup the python environment, install needed python pieces, install Ollama, and then download the models we will use. This will take several more minutes to run. It will look like this while this is running.

![Final prep](./images/aip2.png?raw=true "Final prep")

The codespace is ready to use when you see a prompt like the one shown below in its terminal.

![Ready to use](./images/aip3.png?raw=true "Ready to use")

<br><br>

**4. Get a free API key for groq to enable use of more powerful models for some of the labs.**

In a browser, go to https://console.groq.com and sign in (free).
Open **API Keys**, click **Create API Key**, and copy the key (you can't view it again later).
Back in the codespace **TERMINAL**, set these two environment variables - paste your real key in place of `<paste-your-key-here>`:


```
export KEY=<paste-your-key-here>

echo "export AGENT_PROVIDER=groq" >> ~/.bashrc
echo "export GROQ_API_KEY=$KEY" >> ~/.bashrc

source ~/.bashrc 
```

Verify they're set (this does NOT print the key):

```
echo "provider=$AGENT_PROVIDER  key=$([ -n "$GROQ_API_KEY" ] && echo set || echo MISSING)"
```

You should see `provider=groq  key=set`.

![Getting API key](./images/aip42.png?raw=true "Getting API key")

![Getting API key](./images/aip44.png?raw=true "Getting API key")

<br><br>

**5. Run the *warm-up* script for faster LLM interactions.**

```
python scripts/warmup.py --embed --keep-alive 300m --auto-pull &
```

After this runs, you'll see a **READY FOR WORKSHOP!** message. You can just hit `Enter` to get back to a prompt.
(If you happen to hit an error where the script gets interrupted, just run it again.)

![Run warmup script](./images/aip22.png?raw=true "Run warmup script")

<br><br>

**6. Open up the *labs.md* file so you can follow along with the labs.**
You can either open it in a separate browser instance or open it in the codespace. 

<br><br>

![Opening labs](./images/aip4.png?raw=true "Opening labs")

**Now, you are ready for the labs!**

<br><br>


**NOTE: If your codespace times out and you need to reopen it**

1. Go to https://github.com/your_github_userid/codespaces
2. Find the codespace in the list, right-click, and select *Open in browser*
3. Repeat the step from the main section (#4) above to run the warmup script again.
<br/><br/>


