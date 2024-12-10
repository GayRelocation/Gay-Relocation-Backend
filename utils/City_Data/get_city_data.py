from Models.models import CityMetrics
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from .schemas import CityDetails, CityMetricsSchema
from openai import OpenAI
import os
import json
from utils.constants import PERPLEXITY_MODEL
from datetime import datetime

system_prompt = """
You are a real estate agent which gathers data for cities in the United States. You will be provided with the city details which are as follows:
1. City Name
2. State Name
3. State Code
Your task is to provide below city metrics data for the city. 

home_price = String, in dollars (e.g. $500K)
property_tax = String (e.g. 1.5%)
home_appreciation_rate = String (e.g. 5%)
price_per_square_foot = String, in dollars (e.g. $200)
education = String, out of 100 (e.g. 80)
healthcare_fitness = String, out of 100 (e.g. 70)
weather_grade = String, out of 100 (e.g. 90)
air_quality_index = String, integer (e.g. 100)
commute_transit_score = String, out of 100 (e.g. 70)
accessibility = String, out of 100 (e.g. 80)
culture_entertainment = String, out of 100 (e.g. 90)
unemployment_rate = String, in percentage (e.g. 5%)
recent_job_growth = String, in percentage (e.g. 2%)
future_job_growth_index = String, out of 100 (e.g. 80)
median_household_income = String, in dollars (e.g. $100K)
state_income_tax = String, in percentage (e.g. 5%)
utilities = String, out of 100 (e.g. 80)
food_groceries = String, out of 100 (e.g. 70)
sales_tax = String, in percentage (e.g. 5%)
transportation_cost = String, out of 100 (e.g. 80)

Output:
1. Strictly return only JSON formatted data.
2. The output should contain all the above metrics.
3. The output should be in the same order as mentioned above.
4. Do not include any additional information in the output, like messages or notes.
5. Each data should be in the same values as mentioned after the '=' sign.
6. Do not provide range based values, provide exact values.

"""


parser_prompt = """
You are a json data parser bot who takes the city data as input and parses the data to provide the city metrics for calculation.
1. Provided the city data from the response from another LLM, please response in response format 
2. Convert all the currency values to string format (e.g. $250K, $1.5M) not $500,123
3. If values are given in range, provide the average value (e.g. 5-10% -> 7.5%)
"""


client = OpenAI()
perplexity_client = OpenAI(api_key=os.getenv(
    "PERPLEXITY_API_KEY"), base_url="https://api.perplexity.ai")


def get_city_data_from_perplexity(city_details: CityDetails, db: Session):
    user_prompt = f"Get city data for City Name: {city_details.city}, State Name: {city_details.state_name} and State Code:{city_details.state_code}"

    response = perplexity_client.chat.completions.create(
        model=PERPLEXITY_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
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
                "content": city_data,
            },
        ],
        response_format=CityMetricsSchema
    )
    response = response.choices[0].message.parsed
    return response.model_dump()


def get_city_data(city_details: CityDetails, db: Session):
    """
    Get city data from the database based on the zip code.
    """

    city_data = db.query(CityMetrics).filter_by(
        search_id=city_details.id).first()

    if city_data and (datetime.now() - city_data.updated_at).days > 365:
        updated_data = get_city_data_from_perplexity(city_details, db)
        db.query(CityMetrics).filter_by(
            search_id=city_details.id).update(updated_data)
        db.commit()
        city_data = db.query(CityMetrics).filter_by(
            search_id=city_details.id).first()
        db.refresh(city_data)

    if city_data is None:
        new_city_data = get_city_data_from_perplexity(city_details, db)
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
