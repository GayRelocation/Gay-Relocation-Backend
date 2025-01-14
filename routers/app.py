import openai
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.future import select
from sqlalchemy import or_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from utils.query_data import query_rag
from utils.city_score import get_city_score
from utils.fetch_news import fetch_news
from utils.City_Data.get_city_data import get_city_data
from Database.get_news_db import get_news_db, News
from Database.get_verified_db import get_verified_db
from Database.get_city_list_db import get_city_list_db, CityMetricsQuery
from utils.constants import MAIN_URL
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from Models.models import CityMetrics

# Create the router
api_router = APIRouter()


@api_router.get("/get-cities-list")
async def get_items_list(
    q: str = Query(
        None, description="City name and state name to search"
    ),
    db: Session = Depends(get_city_list_db),
):
    print(q)
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Search term is required.")

    search_query = f"%{q.strip()}%"
    query = db.query(CityMetricsQuery).filter(
        or_(
            CityMetricsQuery.city.ilike(search_query),
            CityMetricsQuery.state_name.ilike(search_query),
            CityMetricsQuery.state_code.ilike(search_query)
        )
    ).order_by(
        case(
            (CityMetricsQuery.city.ilike(search_query), 1),
            else_=2
        )
    ).limit(20)

    cities = query.all()

    if not cities:
        return {
            "results": [],
            "success": False,
            "message": "No matching cities found.",
        }

    return {
        "results": [
            {
                "id": city.id,
                "city": city.city,
                "state_name": city.state_name,
                "state_code": city.state_code,
                "value": f"{city.city}, {city.state_code}",
            }
            for city in cities
        ],
        "success": True,
    }


# Pydantic models for request validation
class CityRequest(BaseModel):
    id: int
    city: Optional[str] = None
    state_code: Optional[str] = None
    state_name: Optional[str] = None


class QueryRequest(BaseModel):
    from_city: Optional[CityRequest] = None
    to_city: Optional[CityRequest] = None


@api_router.post("/comparison")
async def handle_query(request: QueryRequest, db: Session = Depends(get_verified_db)):
    """
    Compare metrics between two cities.
    """

    def model_to_dict(instance):
        return {c.name: getattr(instance, c.name) for c in instance.__table__.columns}

    def add_units(city_data):
        city = {
            "accessibility": str(int(city_data["accessibility"])),
            "air_quality_index": str(int(city_data["air_quality_index"])),
            "city": city_data["city"],
            "commute_transit_score": str(int(city_data["commute_transit_score"])),
            "culture_entertainment": str(int(city_data["culture_entertainment"])),
            "education": str(int(city_data["education"])),
            "food_groceries": str(int(city_data["food_groceries"])),
            "future_job_growth_index": f'{city_data["future_job_growth_index"]}%',
            "healthcare_fitness": str(int(city_data["healthcare_fitness"])),
            "home_appreciation_rate": f"{city_data['home_appreciation_rate']}%",
            "home_price": f"${city_data['home_price']:,}",
            "median_household_income": f"${city_data['median_household_income']:,}",
            "price_per_square_foot": f"${city_data['price_per_square_foot']:,}",
            "property_tax": f"${city_data['property_tax']:,}",
            "recent_job_growth": f'{city_data["recent_job_growth"]}%',
            "sales_tax": f"{city_data['sales_tax']}%",
            "state_code": city_data["state_code"],
            "state_income_tax": f"{city_data['state_income_tax']}%",
            "state_name": city_data["state_name"],
            "transportation_cost": str(int(city_data["transportation_cost"])),
            "unemployment_rate": f"{city_data['unemployment_rate']}%",
            "utilities": str(int(city_data["utilities"])),
            "weather_grade": str(city_data["weather_grade"]),
        }

        return city

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

    city_1_data = get_city_data(request.from_city, db)
    city_2_data = get_city_data(request.to_city, db)
    # db.commit()
    # db.refresh(city_1_data)
    # db.refresh(city_2_data)

    city_1_data = model_to_dict(city_1_data)
    city_2_data = model_to_dict(city_2_data)

    city_1_str = add_units(city_1_data)
    city_2_str = add_units(city_2_data)

    # Check if city data exists
    if not city_1_data or not city_2_data:
        raise HTTPException(
            status_code=404, detail="City data not found for one or both cities."
        )

    return {
        **result,
        "city_1": city_1_str,
        "city_2": city_2_str,
        "comparison": get_city_score(city_1_data, city_2_data),
        "success": True,
    }


@api_router.get("/similar_posts")
async def get_similar_posts(
    city: Optional[str] = Query(
        None, description="Search term to find similar posts"
    ),
    db: AsyncSession = Depends(get_news_db),
):
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


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    city: Optional[str] = None


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


# Define your request model
class ContactUsRequest(BaseModel):
    name: str
    email: str
    phone: str
    comments: str


@api_router.post("/contact-us")
def contact_us(request: ContactUsRequest):
    # Replace MAIN_URL with the actual base URL
    URL = f"{MAIN_URL}/contact-gay-real-estate.html"
    driver = None

    try:
        # Configure Chrome options for headless operation
        # Set up the Selenium WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--headless')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(90)

        # Load the URL and get the page source
        driver.implicitly_wait(6)
        driver.get(URL)
        # ...

        # Fill in the form fields
        try:
            driver.find_element(By.ID, "clientName").send_keys(request.name)
            driver.find_element(By.ID, "clientEmail").send_keys(request.email)
            driver.find_element(By.ID, "clientPhone").send_keys(request.phone)
            driver.find_element(By.ID, "clientComments").send_keys(
                request.comments)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error filling form: {str(e)}"
            )

        # Handle the "Send" button
        try:
            # Wait for the button to be clickable
            submit_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.ID, "contactUsSubmit"))
            )

            # Scroll the button into view
            driver.execute_script(
                "arguments[0].scrollIntoView(true);", submit_button)

            # Force click the button
            driver.execute_script("arguments[0].click();", submit_button)

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error clicking submit button: {str(e)}"
            )

        # Wait for success message
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "successMsg"))
            )
            return {
                "success": True,
                "message": "Thank You! We have received your request and one of our staff members will reply shortly.",
            }
        except Exception as e:
            raise HTTPException(
                status_code=500, detail="Success message not found after submission."
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}"
        )
    finally:
        if driver:
            driver.quit()


# import csv

# @api_router.post("/add_city_data_bulk_csv")
# async def add_city_data_bulk_csv(db: Session = Depends(get_verified_db), city_list_db: Session = Depends(get_city_list_db)):
#     try:
#         with open('merged.csv', newline='', encoding='utf-8') as csvfile:
#             reader = csv.DictReader(csvfile)

#             for row in reader:
#                 try:
#                     # Extract required fields from the CSV row
#                     city_name = row.get('city')
#                     state_name = row.get('state_name')
#                     state_code = row.get('state_code')

#                     if not city_name or not state_name or not state_code:
#                         return {
#                             "success": False,
#                             "message": "Missing required fields: city, state_name, or state_code in CSV row."
#                         }

#                     # Check if the city exists in the city list database
#                     city_list = city_list_db.query(CityMetricsQuery).filter(
#                         CityMetricsQuery.city == city_name,
#                         CityMetricsQuery.state_name == state_name,
#                         CityMetricsQuery.state_code == state_code
#                     ).first()

#                     if not city_list:
#                         return {
#                             "success": False,
#                             "message": f"City {city_name}, {state_name} not found in city list database."
#                         }

#                     search_id = city_list.id

#                     # Prepare the city data for insertion
#                     city_data = CityMetrics(
#                         search_id=search_id,
#                         state_name=row.get('state_name'),
#                         state_code=row.get('state_code'),
#                         home_price=float(row.get('home_price', 0)),
#                         property_tax=float(row.get('property_tax', 0)),
#                         home_appreciation_rate=float(row.get('home_appreciation_rate', 0)),
#                         price_per_square_foot= float(row.get('price_per_square_foot', 0)) if row.get('price_per_square_foot', 0) else None,
#                         education=int(row.get('education', 0)),
#                         healthcare_fitness=int(row.get('healthcare_fitness', 0)),
#                         weather_grade=int(row.get('weather_grade', 0)),
#                         air_quality_index=int(row.get('air_quality_index', 0)),
#                         commute_transit_score=int(row.get('commute_transit_score', 0)),
#                         accessibility=int(row.get('accessibility', 0)),
#                         culture_entertainment=int(row.get('culture_entertainment', 0)),
#                         unemployment_rate=float(row.get('unemployment_rate', 0)),
#                         recent_job_growth=float(row.get('recent_job_growth', 0)),
#                         future_job_growth_index=float(row.get('future_job_growth_index', 0)),
#                         median_household_income=float(row.get('median_household_income', 0)),
#                         state_income_tax=float(row.get('state_income_tax', 0)),
#                         utilities=float(row.get('utilities', 0)),
#                         food_groceries=float(row.get('food_groceries', 0)),
#                         sales_tax=float(row.get('sales_tax', 0)),
#                         transportation_cost=float(row.get('transportation_cost', 0)),
#                         city=row.get('city')
#                     )

#                     db.add(city_data)

#                 except Exception as e:
#                     db.rollback()
#                     return {
#                         "success": False,
#                         "message": f"An error occurred while processing city {row.get('city')}: {str(e)}"
#                     }

#             db.commit()
#             return {"success": True, "message": "All city data added successfully."}

#     except Exception as e:
#         return {"success": False, "message": f"An error occurred: {str(e)}"}
