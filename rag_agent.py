# Import necessary libraries
import os
import re
import json
import requests
import math
from openai import OpenAI
import chromadb
import pdfplumber
from sentence_transformers import SentenceTransformer
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
def search_vector_db(query):
    """Search ChromaDB for relevant document snippets"""
    print(f"\n{RED}RAG Search Query:{RESET} '{query}'")
    results = collection.query(query_texts=[query], n_results=3)
    snippets = results["documents"][0] if results["documents"] else []

    if snippets:
        print(f"{RED}RAG Retrieved Snippets:{RESET}")
        for idx, snippet in enumerate(snippets, 1):
            print(f"{RED}{BOLD}{idx}. {snippet}{RESET}")
    else:
        print(f"{RED}No relevant snippets found in documents{RESET}")

    return snippets

# --- Resolve the city straight from the retrieved office line ---
def extract_city_from_rag(snippets):
    """Resolve the city straight from a retrieved office line, e.g.
    'HQ 123 Main St, New York, NY ...' -> 'New York'. Grounded in what was
    actually retrieved, with no hardcoded city list."""
    for snippet in snippets:
        parts = snippet.split(",")
        if len(parts) >= 2 and parts[1].strip():
            city = parts[1].strip()
            print(f"{GREEN}RAG resolved city from snippet: {city}{RESET}")
            return city
    return None

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
print("\nLoading and indexing PDF into ChromaDB...")
pdf_text = ""
with pdfplumber.open("../data/offices.pdf") as pdf:
    for page in pdf.pages:
        pdf_text += page.extract_text() + "\n"

model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(
    name="office_docs",
    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
)

docs = [line.strip() for line in pdf_text.split('\n') if len(line.strip()) > 20]
ids = [f"doc_{i}" for i in range(len(docs))]
collection.add(documents=docs, ids=ids)
print(f"{GREEN}Indexed {len(docs)} office documents.{RESET}")

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

        # --- Adaptive, self-checking retrieval (orchestrated in code) ---
        # Agentic BEHAVIOR, but the decisions below (grounded? retry? decline?)
        # are made by this Python logic, not by the model. The agent doesn't
        # just look up once; it checks whether retrieval actually found the
        # office asked about, refines the query and retries if not, and answers
        # ONLY if grounded (otherwise it honestly declines).
        stop = {"which", "is", "closer", "to", "me", "or", "the", "office", "tell",
                "about", "what", "and", "how", "far", "from", "an", "of", "city",
                "known", "for", "each", "near", "my", "a"}
        req_words = [w for w in re.findall(r"[a-z]+", user_input.lower())
                     if w not in stop and len(w) >= 2]

        refinements = [user_input,
                       user_input + " office location address",
                       (" ".join(req_words) + " office") if req_words else user_input]

        rag_snippets, detected_city, office_facts, grounded = [], None, [], False
        for attempt, q in enumerate(refinements, 1):
            print(f"\n{CYAN}[Retrieval attempt {attempt}] searching: {q!r}{RESET}")
            rag_snippets = search_vector_db(q)

            # Self-check: did a distinctive word from the request actually
            # appear in a retrieved office line? (grounding check)
            match = None
            for s in rag_snippets:
                toks = set(re.findall(r"[a-z]+", s.lower()))
                if any(w in toks for w in req_words):
                    match = s
                    break
            if match:
                detected_city = extract_city_from_rag([match])
                office_facts = [match]
            if detected_city and office_facts:
                print(f"{GREEN}[Self-check] grounded: matched an office in {detected_city} (attempt {attempt}){RESET}")
                grounded = True
                break
            print(f"{YELLOW}[Self-check] no matching office yet - refining the query and retrying{RESET}")

        # Honest grounding: if nothing matched, say so and list the real offices
        if not grounded:
            all_offices = search_vector_db("office")
            names = ", ".join(s.split(",")[0].strip() for s in all_offices if "," in s)
            print(f"\n{RED}Couldn't ground that request in the documents. Offices on file: {names}{RESET}")
            continue

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
