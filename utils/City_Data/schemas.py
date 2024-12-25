from pydantic import BaseModel


class CityDetails(BaseModel):
    id: int
    city: str
    state_name: str
    state_code: str



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
