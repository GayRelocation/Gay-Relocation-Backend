from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import Column, Integer, String, Float, create_engine, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from pydantic import BaseModel
from geopy.distance import geodesic
import geohash2
import re

# Database Setup
DATABASE_URL = "sqlite:///nearby_cities.db"

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM Models
class City(Base):
    __tablename__ = "cities"
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, index=True)
    city_ascii = Column(String, index=True)
    lat = Column(Float)
    lng = Column(Float)
    country = Column(String)
    iso2 = Column(String)
    iso3 = Column(String)
    admin_name = Column(String)
    capital = Column(String)
    population = Column(String)

class GeoSpatialIndex(Base):
    __tablename__ = "geospatial_index"
    id = Column(Integer, primary_key=True, index=True)
    geohash = Column(String, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"), unique=True)
    city = relationship("City")

# Pydantic Models for Response Validation
class CityResponse(BaseModel):
    city: str
    lat: float
    lng: float
    admin_name: str
    country: str
    geohash: str
    distance: float

class SearchResponse(BaseModel):
    from_city: str
    nearby_cities: list[CityResponse]

# FastAPI App
app = FastAPI()

# Utility Functions
def estimate_length_required(radius_km):
    if radius_km >= 2500:
        return 1
    elif radius_km >= 630:
        return 2
    elif radius_km >= 78:
        return 3
    elif radius_km >= 20:
        return 4
    elif radius_km >= 2.4:
        return 5
    elif radius_km >= 0.61:
        return 6
    elif radius_km >= 0.076:
        return 7
    elif radius_km >= 0.019:
        return 8
    else:
        return 9

def normalize_query(query):
    return re.sub(r"[^\w\s]", "", query, flags=re.UNICODE).lower()

def find_nearby_cities(db_session, from_city):
    # Normalize the input query
    normalized_city = normalize_query(from_city)

    # Fetch the city details from the database
    city = db_session.query(City).filter(City.city_ascii.ilike(f"%{normalized_city}%")).first()
    if not city:
        return [], ""

    # Calculate nearby cities
    return find_nearby_cities_by_lat_lng(db_session, city.lat, city.lng), f"{city.city}, {city.country}"

def find_nearby_cities_by_lat_lng(db_session, lat, lng, radius_km=100):
    geohash = geohash2.encode(lat, lng)
    length = estimate_length_required(radius_km)

    # Query for nearby cities using geohash prefix
    nearby_cities = (
        db_session.query(City, GeoSpatialIndex.geohash)
        .join(GeoSpatialIndex, GeoSpatialIndex.city_id == City.id)
        .filter(GeoSpatialIndex.geohash.like(f"{geohash[:length]}%"))
        .all()
    )

    # Calculate distances and format results
    results = []
    for city, geohash in nearby_cities:
        distance = geodesic((lat, lng), (city.lat, city.lng)).km
        results.append({
            "city": city.city,
            "lat": city.lat,
            "lng": city.lng,
            "admin_name": city.admin_name,
            "country": city.country,
            "geohash": geohash,
            "distance": round(distance, 2),
        })

    # Remove the origin city from the results
    results = [city for city in results if not (city["lat"] == lat and city["lng"] == lng)]
    results.sort(key=lambda x: x["distance"])

    return results

# FastAPI Endpoints
@app.get("/", response_class=JSONResponse)
def welcome():
    return {"message": "Welcome to the Nearby Cities API!"}

@app.get("/search", response_model=SearchResponse)
def search(city: str = ""):
    if not city:
        raise HTTPException(status_code=400, detail="City name is required.")

    db_session = SessionLocal()
    try:
        nearby_cities, from_city_full = find_nearby_cities(db_session, city)

        return SearchResponse(
            from_city=from_city_full,
            nearby_cities=nearby_cities
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        db_session.close()

# Run Database Initialization
if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")
