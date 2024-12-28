from Models.models import CityMetrics
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from .schemas import CityDetails, CityMetricsSchema
from openai import OpenAI
import os
import json
from utils.constants import PERPLEXITY_MODEL
from datetime import datetime

system_prompt_for_city = """
You are a real estate data retrieval agent specializing in gathering comprehensive city metrics for cities in the United States. You will be provided with specific city details, including:
1. City Name
2. State Name
3. State Code

Your task is to provide the following city metrics data for the specified city:
"""

system_prompt_for_state = """
You are a real estate data retrieval agent specializing in gathering comprehensive state metrics in the United States. You will be provided with specific state details, including:
1. State Name
2. State Code

Your task is to provide the following state metrics data for the specified state:
"""

default_prompt = """

- home_price: String, in dollars (e.g., $500K)
- property_tax: String (e.g., 1.5%)
- home_appreciation_rate: String (e.g., 5%)
- price_per_square_foot: String, in dollars (e.g., $200)
- education: String, out of 100 (e.g., 80)
- healthcare_fitness: String, out of 100 (e.g., 70)
- weather_grade: String, out of 100 (e.g., 90)
- air_quality_index: String, integer (e.g., 100)
- commute_transit_score: String, out of 100 (e.g., 70)
- accessibility: String, out of 100 (e.g., 80)
- culture_entertainment: String, out of 100 (e.g., 90)
- unemployment_rate: String, in percentage (e.g., 5%)
- recent_job_growth: String, in percentage (e.g., 2%)
- future_job_growth_index: String, out of 100 (e.g., 80)
- median_household_income: String, in dollars (e.g., $100K)
- state_income_tax: String, in percentage (e.g., 5%)
- utilities: String, out of 100 (e.g., 80)
- food_groceries: String, out of 100 (e.g., 70)
- sales_tax: String, in percentage (e.g., 5%)
- transportation_cost: String, out of 100 (e.g., 80)

Output Requirements:
1. If specific city data is unavailable, provide state-level data.
2. Return data strictly in JSON format.
3. Include all the above metrics in the output.
4. Maintain the order of metrics as listed.
5. Exclude any additional information, messages, or notes.
6. Provide exact values, not ranges.
7. If data is unavailable, return null for that metric.
"""


parser_prompt = """
You are a JSON data parser bot. Your task is to parse city data provided by another LLM and format it according to the specified city metrics. 

Follow these guidelines:
1. Convert all currency values to string format (e.g., $250K, $1.5M) instead of exact amounts (e.g., $500,123).
2. If values are given in ranges, calculate and provide the average value (e.g., 5-10% -> 7.5%).
3. If any data is unavailable, return a null value for that metric.
4. Ensure the output strictly follows the CityMetricsSchema format.
5. If values are missing, use your own knowledge to fill in the gaps.
6. If values are missing and you are unsure, return null. 
"""


client = OpenAI()
perplexity_client = OpenAI(api_key=os.getenv(
    "PERPLEXITY_API_KEY"), base_url="https://api.perplexity.ai")


def get_city_data_from_perplexity(city_details: CityDetails):
    user_prompt = f"City Name: {city_details.city}, State Name: {city_details.state_name} and State Code:{city_details.state_code}"

    response = perplexity_client.chat.completions.create(
        model=PERPLEXITY_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt_for_city + default_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]
    )

    city_data = response.choices[0].message.content

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": parser_prompt,
            },
            {
                "role": "user",
                "content": city_data + user_prompt, 
            },
        ],
        response_format=CityMetricsSchema
    )
    response = response.choices[0].message.parsed
    return response.model_dump()


def get_city_data_from_perplexity_for_state(city_details: CityDetails):
    user_prompt = f"Get data for State Name: {city_details.state_name} and State Code:{city_details.state_code}"

    response = perplexity_client.chat.completions.create(
        model=PERPLEXITY_MODEL,
        messages=[
            {
                "role": "user",
                "content": system_prompt_for_state + default_prompt + user_prompt
            },
        ],
        
    )

    city_data = response.choices[0].message.content

    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": parser_prompt,
            },
            {
                "role": "user",
                "content": city_data,
            },
        ],
        response_format=CityMetricsSchema
    )
    response = response.choices[0].message.parsed
    file_name = city_details.state_name.replace(" ", "_") + ".json"
    with open(f"Data/State_Data/{file_name}", "w") as f:
        json.dump(response.model_dump(), f, indent=4)

    return response.model_dump()


def get_city_data(city_details: CityDetails, db: Session):
    """
    Get city data from the database based on the zip code.
    """

    city_data = db.query(CityMetrics).filter_by(
        search_id=city_details.id).first()

    if city_data and (datetime.now() - city_data.updated_at).days > 365:
        updated_data = get_city_data_from_perplexity(city_details)
        db.query(CityMetrics).filter_by(
            search_id=city_details.id).update(updated_data)
        db.commit()
        city_data = db.query(CityMetrics).filter_by(
            search_id=city_details.id).first()
        db.refresh(city_data)

    if city_data is None:
        new_city_data = get_city_data_from_perplexity(city_details)
        city_data = CityMetrics(
            search_id=city_details.id,
            city=city_details.city,
            state_name=city_details.state_name,
            state_code=city_details.state_code,
            **new_city_data
        )
        db.add(city_data)
        db.commit()
        city_data = db.query(CityMetrics).filter_by(
            search_id=city_details.id).first()
        db.refresh(city_data)

    return city_data
