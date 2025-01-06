from pydantic import BaseModel


class CityDetails(BaseModel):
    id: int
    city: str
    state_name: str
    state_code: str


class CityMetricsSchema(BaseModel):
    home_price: float
    property_tax: float
    home_appreciation_rate: float
    price_per_square_foot: float
    education: float
    healthcare_fitness: float
    weather_grade: float
    air_quality_index: float
    commute_transit_score: float
    accessibility: float
    culture_entertainment: float
    unemployment_rate: float
    recent_job_growth: float
    future_job_growth_index: float
    median_household_income: float
    state_income_tax: float
    utilities: float
    food_groceries: float
    sales_tax: float
    transportation_cost: float
