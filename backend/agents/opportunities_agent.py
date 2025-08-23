import os
import logging
import re
import json
from typing import List, Tuple, Set
from pydantic import BaseModel, Field
from tavily import TavilyClient
from dotenv import load_dotenv

# --- Setup and Configuration ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the Tavily client
tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    # Fallback for environments where dotenv doesn't load early enough
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
if not tavily_api_key:
    raise ValueError("TAVILY_API_KEY environment variable not set. Please add it to your .env file.")
tavily = TavilyClient(api_key=tavily_api_key)

class Event(BaseModel):
    """Data model to hold structured information about a single global event."""
    name: str
    date: str = Field(default="Not Found")
    city: str = Field(default="Not Found")
    country: str = Field(default="Not Found")
    source_url: str = Field(default="Not Found")

def _extract_location(content: str) -> Tuple[str, str]:
    """A helper function to extract city and country from text content."""
    location_match = re.search(
        r'\b(in|at|location|venue):\s*([A-Z][a-zA-Z\s.-]+),\s*([A-Z][a-zA-Z\s.-]+)\b',
        content,
        re.IGNORECASE
    )
    if location_match:
        city = location_match.group(2).strip()
        country = location_match.group(3).strip()
        if len(city) > 2 and len(country) > 2:
            return city, country
            
    city_match = re.search(r'\b(London|Paris|Berlin|Tokyo|Singapore|Dubai|Toronto|Sydney|Seoul)\b', content, re.IGNORECASE)
    if city_match:
        return city_match.group(0), "Not Found"

    return "Not Found", "Not Found"

# CORRECTED FUNCTION: Renamed and modified to return the file path
def run_opportunities_agent(business_idea: str) -> str:
    """
    Performs a broad, global search for relevant events and saves them to a file.

    Args:
        business_idea: The core concept of the business (e.g., "generative AI startups").

    Returns:
        The path to the output file containing the event data.
    """
    if not business_idea:
        logger.error("Business idea cannot be empty.")
        raise ValueError("Please provide a valid business idea.")

    logger.info(f"Starting GLOBAL event search for: '{business_idea}'")

    discovery_queries = [
        f"list of global conferences for '{business_idea}' in 2024 and 2025",
        f"top international trade shows for the '{business_idea}' industry",
        f"major European tech summits for '{business_idea}'",
        f"leading Asian expos and forums for '{business_idea}'",
        f"must-attend North American events for '{business_idea}' startups"
    ]

    event_candidates: Set[str] = set()
    all_search_content = ""

    for query in discovery_queries:
        logger.info(f"Executing Tavily search: \"{query}\"")
        try:
            discovery_data = tavily.search(query=query, search_depth="advanced", max_results=5)
            content = " ".join([result.get('content', '') for result in discovery_data.get('results', [])])
            all_search_content += content + " "
            
            found_names = re.findall(r'\b([A-Z][a-zA-Z0-9\s-]{4,}\b(?:Conference|Expo|Summit|Show|Week|Days|Forum|Festival|Connect))\b', content)
            for name in found_names:
                event_candidates.add(name.strip().replace("  ", " "))

        except Exception as e:
            logger.error(f"Tavily search for query '{query}' failed: {e}")
            continue
    
    if not event_candidates:
        logger.warning("No potential event candidates found from the global search.")
        return "No events found."
        
    logger.info(f"Found {len(event_candidates)} unique potential events to investigate globally.")

    verified_events: List[Event] = []
    for event_name in list(event_candidates)[:15]:
        logger.info(f"Investigating event: '{event_name}'")
        try:
            detail_query = f"official website date and location for the event '{event_name}'"
            detail_data = tavily.search(query=detail_query, search_depth="basic", max_results=1)

            if not (detail_data and detail_data.get("results")):
                logger.warning(f"Could not find specific details for '{event_name}'. Skipping.")
                continue

            top_result = detail_data["results"][0]
            event_url = top_result.get("url", "Not Found")
            result_content = top_result.get("content", "")

            date_match = re.search(r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:(?:st|nd|rd|th)|(?:-\d{1,2}(?:st|nd|rd|th)?))?,\s+\d{4})\b', result_content, re.IGNORECASE)
            event_date = date_match.group(0) if date_match else "Not Found"

            city, country = _extract_location(result_content)

            event = Event(name=event_name, date=event_date, city=city, country=country, source_url=event_url)
            verified_events.append(event)
            logger.info(f"-> Success for '{event.name}': [Date: {event.date}, Location: {event.city}, {event.country}]")

        except Exception as e:
            logger.error(f"Failed to process details for event '{event_name}': {e}")
    
    # --- Define output path and save file ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Use a new filename to avoid confusion with the old output
    output_filename = os.path.join(output_dir, "global_events_output.json")
    
    if verified_events:
        logger.info(f"Saving {len(verified_events)} verified global events to '{output_filename}'")
        events_dict_list = [event.model_dump() for event in verified_events]
        
        # Overwrite the file with new results for each run
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(events_dict_list, f, indent=4)
    else:
        # If no events are found, write an empty list to the file
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)

    # CORRECTED: Return the path to the output file
    return output_filename

# --- Example Usage for a Global Search ---
if __name__ == "__main__":
    my_business_idea = "Financial Technology (FinTech) solutions"
    print(f"--- Starting a global search for events related to '{my_business_idea}'... ---")
    
    # Updated to call the new function name
    output_file = run_opportunities_agent(my_business_idea)
    print(f"--- Search complete. Results saved to: {output_file} ---")