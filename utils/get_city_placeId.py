import requests
from dotenv import load_dotenv
import os

load_dotenv()


api_key = "c8744b2958mshfede3b57afa743bp15bb21jsnd344030714f5"
city_name = "New York"
url = "https://wft-geo-db.p.rapidapi.com/v1/geo/cities"

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
        print("No cities found.")
    for city in cities:
        print(
            f"City: {city['name']}, Country: {city['country']}, Place ID: {city['id']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
