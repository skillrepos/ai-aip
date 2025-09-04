import json
import ollama
import os
import re
from crewai import Crew, Task, Agent
from langchain_openai import ChatOpenAI

os.environ["OPENAI_API_KEY"] = "testapikey"

# Use a lightweight LLM model optimized for CPU
ollama_llm = ChatOpenAI(
    model="ollama/llama3.2",
    base_url="http://localhost:11434"
)

# Simulated function to book a flight
def book_flight(flight_number: str):
    print(f"Booking flight {flight_number}...")
    return json.dumps({"status": "confirmed", "flight_number": flight_number})

# Define the AI agent 

# Define the tasks with expected outputs
# Create a task to extract travel details (source, destination, date) using the LLM.

# Create a task to find suitable flights

# Create a task to present flight options 

# Create a task to book the flight

# Create the Crew

# Run the process with user input
user_input = "I need a flight to New York on December 11, 2025."
result = crew.kickoff(inputs={"user_request": user_input})
print("Confirmation:", result)
