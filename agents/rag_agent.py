# Import necessary libraries
import os
import json
import requests
import math
from openai import OpenAI
import chromadb
import pdfplumber
from chromadb.utils import embedding_functions

# ANSI color codes for terminal output
BLUE = "\033[94m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Configuration constants
STARTING_LOC_FILE = "user_starting_location.json"
DEFAULT_LOCATION = {"city": "Raleigh, NC", "lat": 35.7796, "lon": -78.6382}

# Connect to local Ollama server
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama',  # dummy key
)

# --- Functions for Location Management ---
def load_starting_location():
    """Load saved starting location from file or return default"""
    if os.path.exists(STARTING_LOC_FILE):
        try:
            with open(STARTING_LOC_FILE, 'r') as f:
                data = json.load(f)
                print(f"{GREEN}Loaded saved starting location: {data['city']}{RESET}")
                return data
        except:
            print(f"{YELLOW}Error loading location file. Using default.{RESET}")
    return DEFAULT_LOCATION

def save_starting_location(city, lat, lon):
    """Save new starting location to file"""
    data = {"city": city, "lat": lat, "lon": lon}
    with open(STARTING_LOC_FILE, 'w') as f:
        json.dump(data, f)
    print(f"{GREEN}Saved new starting location: {city}{RESET}")

def set_starting_location_interactively():
    """Prompt user to set/update starting location"""
    current_loc = load_starting_location()
    
    print(f"\n{CYAN}Current starting location: {current_loc['city']} ({current_loc['lat']}, {current_loc['lon']}){RESET}")
    change = input("Do you want to change your starting location? (y/n): ").strip().lower()
    
    if change == 'y':
        while True:
            new_city = input("Enter new starting city (e.g., 'New York, NY'): ").strip()
            if not new_city:
                continue
                
            lat, lon = geocode_location(new_city)
            if lat is None or lon is None:
                print(f"{YELLOW}Could not find coordinates for '{new_city}'. Please try again.{RESET}")
            else:
                save_starting_location(new_city, lat, lon)
                return {"city": new_city, "lat": lat, "lon": lon}
    
    return current_loc

# --- Core Functions ---
# --- Convert city name to lat/lon coordinates ---
def geocode_location(location_query):
    """Convert city name to lat/lon coordinates"""
    print(f"{CYAN}Geocoding location: '{location_query}'{RESET}")
    headers = {'User-Agent': 'TravelAssistant/1.0'}
    try:
        response = requests.get(
            f"https://nominatim.openstreetmap.org/search?q={location_query}&format=json", 
            headers=headers
        )
        geo = response.json()
        if geo:
            return float(geo[0]['lat']), float(geo[0]['lon'])
        return None, None
    except Exception as e:
        print(f"{RED}Geocoding error: {e}{RESET}")
        return None, None

# --- Calculate straight-line distance between two points (in miles) ---
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate straight-line distance between two points (in miles)"""
    R = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 + 
         math.cos(math.radians(lat1)) * 
         math.cos(math.radians(lat2)) * 
         math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_distance_tool(starting_loc, destination_query):
    """Calculate distance from starting location to destination"""
    print(f"\n{CYAN}Using Distance Calculation Tool{RESET}")
    print(f"{YELLOW}Starting location: {starting_loc['city']} ({starting_loc['lat']}, {starting_loc['lon']}){RESET}")
    print(f"{YELLOW}Destination: {destination_query}{RESET}")
    
    # Geocode destination
    dest_lat, dest_lon = geocode_location(destination_query)
    if dest_lat is None or dest_lon is None:
        return {"error": "Could not find destination coordinates"}
    
    print(f"{YELLOW}Destination coordinates: ({dest_lat}, {dest_lon}){RESET}")
    
    # Calculate distance
    miles = haversine_distance(
        starting_loc['lat'], starting_loc['lon'],
        dest_lat, dest_lon
    )
    distance = round(miles, 2)
    print(f"{YELLOW}Calculated distance: {distance} miles{RESET}")
    return {"destination": destination_query, "distance_miles": distance}

# --- RAG Functions ---
# --- Search the vector database to find relevant snippets

# --- See if we can pull a city from the RAG results ---

# --- As a fallback, try to pull a city via the LLM ---

# --- Prompt and Response Generation ---
def get_city_facts(location_name):
    """Get interesting facts about a city"""
    messages = [
        {"role": "system", "content": "Provide exactly 3 interesting facts about the city. Each fact starts with a dash (-)."},
        {"role": "user", "content": f"Tell me 3 interesting facts about {location_name}."}
    ]
    completion = client.chat.completions.create(
        model="llama3.2",
        messages=messages,
    )
    return completion.choices[0].message.content

# --- Format output ----
def format_final_output(location_name, office_facts, city_facts, distance_info, starting_city):
    """Format final response for user"""
    output = f"{BOLD}{BLUE}Facts about the Office in {location_name}:{RESET}{BLUE}\n\n"
    for fact in office_facts:
        output += f"• {fact.strip()}\n"
    
    output += f"\n{BOLD}{BLUE}Facts about {location_name}:{RESET}{BLUE}\n\n"
    for fact in city_facts:
        output += f"• {fact.strip()}\n"
    
    dist = distance_info.get('distance_miles', 'unknown')
    output += f"\n{BOLD}{BLUE}Distance from {starting_city}:{RESET}{BLUE} {dist} miles"
    return output

# --- Document Indexing ---

# --- Main Interaction Loop ---
if __name__ == "__main__":
    # Set starting location
    starting_loc = set_starting_location_interactively()
    
    print("\nTravel Assistant ready! (Type 'exit' to quit)")
    print(f"{CYAN}Current starting location: {starting_loc['city']} ({starting_loc['lat']}, {starting_loc['lon']}){RESET}")

    while True:
        user_input = input("\nUser: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        # RAG Document Search
        
        # City Detection Workflow
        if not detected_city:
            detected_city = fallback_detect_city_with_llm(user_input)
        
        if not detected_city:
            print(f"{RED}Could not detect a valid city name{RESET}")
            continue

        # Prepare Office Facts
        
        # Prepare City Facts
        city_facts_text = get_city_facts(detected_city)
        city_facts = [line[1:].strip() for line in city_facts_text.split('\n') 
                     if line.startswith('-') or line.startswith('•')][:3]
        
        # Calculate Distance
        distance_info = calculate_distance_tool(starting_loc, detected_city)
        
        # Generate Final Output
        final_output = format_final_output(
            detected_city,
            office_facts,
            city_facts,
            distance_info,
            starting_loc['city']
        )
        
        print(f"\n{GREEN}Assistant Final Response:{RESET}\n\n{BLUE}{final_output}{RESET}")
