from sqlalchemy import Column, String, Float, Integer, Index, DateTime
from . import Base
from datetime import datetime


class CityMetrics(Base):
    __tablename__ = "city_metrics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Identification
    city = Column(String, index=True)
    state_code = Column(String, index=True)
    state_name = Column(String, index=True)
    search_id = Column(Integer, index=True)

    # Housing Availability
    home_price = Column(Float)  # Adjusted for numeric data
    property_tax = Column(Float)
    home_appreciation_rate = Column(Float)
    price_per_square_foot = Column(Float)

    # Quality of Life
    education = Column(Float)  # Adjusted for numeric data
    healthcare_fitness = Column(Float)
    weather_grade = Column(Float)
    air_quality_index = Column(Float)
    commute_transit_score = Column(Float)
    accessibility = Column(Float)
    culture_entertainment = Column(Float)

    # Job Market Strength
    unemployment_rate = Column(Float)
    recent_job_growth = Column(Float)
    future_job_growth_index = Column(Float)
    median_household_income = Column(Float)

    # Living Affordability
    state_income_tax = Column(Float)
    utilities = Column(Float)
    food_groceries = Column(Float)
    sales_tax = Column(Float)
    transportation_cost = Column(Float)  # Adjusted column name for clarity

    # Dates
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Define composite index for optimized search
    __table_args__ = (
        Index("idx_city_state", "city", "state_name"),
    )
