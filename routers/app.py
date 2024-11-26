from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.future import select
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
from db import get_db
from Models.models import CityMetrics
from utils.query_data import query_rag
import requests
import openai
import os
openai.api_key = os.getenv("OPENAI_API_KEY")


# Create the router
api_router = APIRouter()


# Pydantic models for request validation
class CityRequest(BaseModel):
    id: int
    zip_code: Optional[str] = None
    city: Optional[str] = None
    state_code: Optional[str] = None
    state_name: Optional[str] = None


class QueryRequest(BaseModel):
    from_city: Optional[CityRequest] = None
    to_city: Optional[CityRequest] = None


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    city: Optional[str] = None


@api_router.get("/get-cities-list")
async def get_items_list(
    q: Optional[str] = Query(
        None, description="City name, state name, or zip code to search"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Search for cities based on city name, state name, or zip code
    and return the top 10 matching results.
    """
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Search term is required.")

    search_query = f"%{q.strip()}%"
    is_digit = q.isdigit()  # Check if the search term is numeric (zip code)

    # Perform query using SQLAlchemy
    query = select(CityMetrics).filter(
        or_(
            CityMetrics.city.ilike(search_query),
            CityMetrics.state_name.ilike(search_query),
            CityMetrics.zip_code.ilike(search_query) if is_digit else False,
        )
    ).limit(10)

    result = db.execute(query)
    cities = result.scalars().all()  # Correctly fetch all matching cities

    # If no results found
    if not cities:
        return {
            "results": [],
            "success": False,
            "message": "No matching cities found.",
        }

    # Prepare response
    return {
        "results": [
            {
                "id": city.id,
                "zip_code": city.zip_code,
                "city": city.city,
                "state_name": city.state_name,
                "state_code": city.state_code,
                "value": f"{city.city}, {city.state_code}{f' ({city.zip_code})' if is_digit else ''}",
            }
            for city in cities
        ],
        "success": True,
    }


def parse_price(price_str):
    """Parse price strings like '$100K' into numerical values."""
    price_str = price_str.replace('$', '').replace(
        ',', '').replace('K', '000').replace('M', '000000').replace('B', '000000000').replace('T', '000000000000').replace(' ', '')
    return float(price_str)


def parse_percentage(percent_str):
    """Parse percentage strings like '10%' into numerical values."""
    return float(percent_str.replace('%', ''))


def calculate_housing_affordability(home_price, median_income):
    """Calculate housing affordability score."""
    home_price_value = parse_price(home_price)
    median_income_value = parse_price(median_income)
    ratio = home_price_value / median_income_value
    ratio = max(2, min(10, ratio))
    score = ((10 - ratio) / 8) * 70 + 30
    return min(score, 99.9)


def calculate_quality_of_life(city_data):
    """Calculate quality of life score."""
    factors = [
        float(city_data["education"]),
        float(city_data["healthcare_fitness"]),
        float(city_data["weather_grade"]),
        float(city_data["air_quality_index"]),
        float(city_data["commute_transit_score"]),
        float(city_data["accessibility"]),
        float(city_data["culture_entertainment"]),
    ]
    average_score = sum(factors) / len(factors)
    score = (average_score / 100) * 70 + 30
    return min(score, 99.9)


def calculate_job_market_strength(city_data):
    """Calculate job market strength score."""
    unemployment_rate = parse_percentage(city_data["unemployment_rate"])
    recent_job_growth = parse_percentage(city_data["recent_job_growth"])
    future_job_growth_index = float(city_data["future_job_growth_index"])

    unemployment_score = ((10 - unemployment_rate) / 10) * 100
    recent_job_growth_score = ((recent_job_growth + 5) / 10) * 100
    future_job_growth_score = future_job_growth_index

    weighted_score = (
        unemployment_score * 0.4 +
        recent_job_growth_score * 0.2 +
        future_job_growth_score * 0.4
    )
    score = (weighted_score / 100) * 70 + 30
    return min(score, 99.9)


def calculate_living_affordability(city_data):
    """Calculate living affordability score."""
    cost_factors = [
        float(city_data["utilities"]),
        float(city_data["food_groceries"]),
        float(city_data["transportation_cost"]),
    ]
    tax_factors = [
        parse_percentage(city_data["sales_tax"]),
        parse_percentage(city_data["state_income_tax"]),
        parse_percentage(city_data["property_tax"]),
    ]
    cost_index = sum(cost_factors) / len(cost_factors)
    normalized_cost_index = (1 - (cost_index / 150)) * 100

    average_tax_rate = sum(tax_factors) / len(tax_factors)
    normalized_tax_score = (1 - (average_tax_rate / 15)) * 100

    weighted_score = (
        normalized_cost_index * 0.7 +
        normalized_tax_score * 0.3
    )
    score = (weighted_score / 100) * 70 + 30
    return min(score, 99.9)


def get_city_score(city_data):
    """Calculate overall city score."""

    housing_affordability = calculate_housing_affordability(
        city_data["home_price"], city_data["median_household_income"]
    )
    quality_of_life = calculate_quality_of_life(city_data)
    job_market_strength = calculate_job_market_strength(city_data)
    living_affordability = calculate_living_affordability(city_data)

    overall_city_score = (housing_affordability + quality_of_life +
                          job_market_strength + living_affordability) / 4

    response = {
        "housing_affordability": round(housing_affordability, 2),
        "quality_of_life": round(quality_of_life, 2),
        "job_market_strength": round(job_market_strength, 2),
        "living_affordability": round(living_affordability, 2),
        "overall_city_score": round(overall_city_score, 2),
    }
    return response


@api_router.post("/comparison")
async def handle_query(request: QueryRequest, db: AsyncSession = Depends(get_db)):
    """
    Compare metrics between two cities.
    """
    # Validate input
    if not request.from_city or not request.to_city:
        raise HTTPException(
            status_code=400, detail="Both from_city and to_city are required."
        )

    # Fetch result from RAG function
    result = {}
    # result = query_rag(request.from_city.city, request.to_city.city)
    result["heading"] = {
        "title": "BIG MOVE!",
        "description": f"A move from {request.from_city.city} to {request.to_city.city} covers a significant distance. This move would bring substantial changes in cost of living, climate, and urban environment.",
    }

    # Fetch city data from the database
    city_1_data = db.execute(select(CityMetrics).filter(
        CityMetrics.zip_code == request.from_city.zip_code)).scalar_one_or_none()

    city_2_data = db.execute(select(CityMetrics).filter(
        CityMetrics.zip_code == request.to_city.zip_code)).scalar_one_or_none()

    # Check if city data exists
    if not city_1_data or not city_2_data:
        raise HTTPException(
            status_code=404, detail="City data not found for one or both cities."
        )

    return {
        **result,
        "city_1": city_1_data.__dict__,
        "city_2": city_2_data.__dict__,
        "comparison": get_city_score(city_2_data.__dict__),
    }


@api_router.get("/similar_posts")
async def get_similar_posts(
    city: Optional[str] = Query(
        None, description="Search term to find similar posts"
    ),
):
    """
    Get similar posts based on the search term.
    """
    if not city:
        raise HTTPException(status_code=400, detail="Search term is required.")

    # replace space with + for the search query
    city = city.replace(" ", "+")

    data = requests.get(
        f"https://www.gayrealestate.com/blog/wp-json/wp/v2/posts?search={city}").json()
    # return top 3
    data = data[:3]
    return {
        "results": data,
        "success": True,
    }


def chat_with_gpt(messages: List[Message], city: str):
    """Send a prompt to OpenAI GPT-4 model and return the response."""
    try:
        system_prompt = f"You are an AI chatbot who is expert on LGBTQ+ related topics. Provide quick, concise, and helpful answers not more than 300 chars about LGBTQ+ resources, events, and information in {city}."

        messages = [{"role": "system", "content": system_prompt}] + messages

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@api_router.post("/chat")
def chatbot(request: ChatRequest):
    """Endpoint to interact with the city chatbot."""
    if not request.messages:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    response = chat_with_gpt(request.messages, request.city)
    return {"response": response}
