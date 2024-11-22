import requests
from dotenv import load_dotenv
import os

load_dotenv()


api_key = os.getenv("RAPID_API_KEY")


def get_city_place_id(city_name):
    url = "https://wft-geo-db.p.rapidapi.com/v1/geo/cities?countryIds=US&&types=CITY"

    querystring = {
        "namePrefix": city_name,
        "limit": "5"
    }
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "wft-geo-db.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code == 200:
        cities = response.json().get('data', [])
        if len(cities) == 0:
            return "No cities found."
        return [(city['name'], city['country'], city['id']) for city in cities]
    else:
        return f"Error: {response.status_code} - {response.text}"
