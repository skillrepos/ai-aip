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

booking_agent = Agent(
    role="Airline Booking Assistant",
    goal="Help users find and book flights efficiently.",
    backstory="You are an expert airline booking assistant, providing the best travel options with clear information.",
    verbose=True,
    llm=ollama_llm,  
)

# Define the tasks with expected outputs
# Create a task to extract travel details (source, destination, date) using the LLM.
extract_travel_info_task = Task(
    description=(
        "Extract destination and date from {user_request}"
       # "Return your result as a JSON object formatted as: "
       # "{\"destination\": \"<destination>\", \"date\": \"<date>\"}."
    ),
    agent=booking_agent,
    expected_output="A JSON object containing 'destination', and 'date'."
)

# Create a task to find suitable flights
find_flights_task = Task(
    description="Find available flights for the extracted destination and date.",
    agent=booking_agent,
    expected_output="A JSON list of available flights, including flight number, airline, departure time, and price."
)

# Create a task to present flight options 
present_flights_task = Task(
    description="Present flight options in a user-friendly format and ask the user to choose one. The list of flight should not be in JSON format and should have a number by each choice.",
    agent=booking_agent,
    expected_output="The selected flight number chosen by the user. If no response, just use 1."
)

# Create a task to book the flight
book_flight_task = Task(
    description="Book the selected flight and confirm booking. If more than one option, just use the first one.",
    agent=booking_agent,
    function=lambda details: book_flight(details["flight_number"]),
    expected_output="A confirmation message with flight number and booking status.",
    verbose=True
)

# Create the Crew
crew = Crew(
    agents=[booking_agent],
    tasks=[extract_travel_info_task, find_flights_task, present_flights_task, book_flight_task],
    process="sequential",
    verbose=False
)

# Run the process with user input
user_input = "I need a flight to New York on December 11, 2025."
result = crew.kickoff(inputs={"user_request": user_input})
print("Confirmation:", result)
