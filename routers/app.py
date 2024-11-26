from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.future import select
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
from db import get_db
from Models.models import CityMetrics
from utils.query_data import query_rag
import openai
import os
from utils.city_score import get_city_score
from utils.constants import CHROMA_PATH, NEWS_COLLECTION, MAIN_URL
from langchain_chroma import Chroma
from get_embedding_function import get_embedding_function
from utils.fetch_news import fetch_news
from get_news_db import get_news_db, News

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
    # result = {}
    result = query_rag(request.from_city.city, request.to_city.city)
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
    db: AsyncSession = Depends(get_news_db),
):
    """
    Get similar posts based on the search term.
    """

    results = db.execute(select(News).filter(
        News.name.ilike(f"%{city}%"))).scalars().all()[0]

    def serialize_news(news):
        return {
            "id": news.id,
            "name": news.name,
            "url": news.url,  # Add other attributes as needed
        }

    results = serialize_news(results)
    results = fetch_news(results["url"])

    return {
        "results": results,
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
