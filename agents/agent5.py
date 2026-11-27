from crewai import Crew, Task, Agent, LLM

# The local llama3.2 model, served by Ollama inside the codespace.
# CrewAI's own LLM class talks to it directly - no API key needed.
ollama_llm = LLM(
    model="ollama/llama3.2",
    base_url="http://localhost:11434"
)

# Define the AI agent 

# Define the tasks with expected outputs
# Create a task to extract travel details (source, destination, date) using the LLM.

# Create a task to find suitable flights

# Create a task to present flight options 

# Create a task to book the flight

# Create the Crew

# Run the process with user input
user_input = "I need a flight to New York on June 11."
result = crew.kickoff(inputs={"user_request": user_input})
print("Confirmation:", result)
