import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Fetch the API key
api_key = os.getenv("RAPID_API_KEY")

# Function to fetch nearby places
def get_nearby_places(place_id):
    if not api_key:
        raise Exception("RAPID_API_KEY not found in environment variables.")

    url = f"https://wft-geo-db.p.rapidapi.com/v1/geo/places/{place_id}/nearbyPlaces"

    querystring = {
        "radius": "100",  # Search radius in kilometers
        "minPopulation": "100000",  # Minimum population filter
    }

    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "wft-geo-db.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)

        if response.status_code == 200:
            cities = response.json().get('data', [])
            if not cities:
                print("No cities found within the specified radius.")
                return []
            # Print formatted results
            for city in cities:
                print(f"City: {city.get('name')}, Country: {city.get('country')}, Population: {city.get('population')}, Distance: {city.get('distance')}")
            return cities
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []

# Example usage
if __name__ == "__main__":
    place_id = "YOUR_PLACE_ID"  # Replace with a valid place_id
    try:
        get_nearby_places(place_id)
    except Exception as e:
        print(e)
