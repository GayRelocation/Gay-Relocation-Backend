from pydantic import BaseModel


class CityDetails(BaseModel):
    zip_code: str
    city: str
    state_name: str
    state_code: str
    id: int
    
    
{
    "city_1": {
        "home_price": "$1.3M",
        "property_tax": "1.25%",
        "home_appreciation_rate": "5%",
        "price_per_square_foot": "$1,100",
        "education": "90",
        "healthcare_fitness": "85",
        "weather_grade": "80",
        "air_quality_index": "101",
        "commute_transit_score": "90",
        "accessibility": "85",
        "culture_entertainment": "95",
        "unemployment_rate": "3.5%",
        "recent_job_growth": "3%",
        "future_job_growth_index": "85",
        "median_household_income": "$126,730",
        "state_income_tax": "13.3%",
        "utilities": "85",
        "food_groceries": "75",
        "sales_tax": "8.625%",
        "transportation_cost": "80"
    }
}
    
class CityMetricsSchema(BaseModel):    
    home_price: str
    property_tax: str
    home_appreciation_rate: str
    price_per_square_foot: str
    education: int
    healthcare_fitness: int
    weather_grade: int
    air_quality_index: int
    commute_transit_score: int
    accessibility: int
    culture_entertainment: int
    unemployment_rate: str
    recent_job_growth: str
    future_job_growth_index: int
    median_household_income: str
    state_income_tax: str
    utilities: int
    food_groceries: int
    sales_tax: str
    transportation_cost: int
    