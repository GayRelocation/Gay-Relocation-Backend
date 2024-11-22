

import requests
from dotenv import load_dotenv
import os
load_dotenv()


api_key = os.getenv("RAPID_API_KEY")

place_id = "3281278"
url = f"https://wft-geo-db.p.rapidapi.com/v1/geo/places/{place_id}/nearbyPlaces"

# Query parameters for filtering (optional)
querystring = {
    "radius": "100",          # Radius in kilometers
    "minPopulation": "100000",  # Minimum population for nearby cities
    "limit": "10"             # Maximum number of cities to return
}

# Headers for the API request
headers = {
    "x-rapidapi-key": api_key,
    "x-rapidapi-host": "wft-geo-db.p.rapidapi.com"
}

# Making the GET request
response = requests.get(url, headers=headers, params=querystring)

# Checking if the request was successful
if response.status_code == 200:
    # Parsing the JSON response
    cities = response.json().get('data', [])
    for city in cities:
        print(city.get('name'), end=', ')
else:
    print(f"Error: {response.status_code} - {response.text}")
