import os
import csv
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.exc import IntegrityError
from geohash2 import encode as geohash_encode

# Paths and constants
DATABASE_URL = "sqlite:///./nearby_cities.db"
WORLD_CITIES_CSV_PATH = "worldcities.csv"  # Replace with your actual CSV file path

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

# ORM Models
class Migration(Base):
    __tablename__ = "migrations"
    name = Column(String, primary_key=True)

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

# Prepare Database Function
def prepare_db():
    # Ensure the database directory exists
    os.makedirs(os.path.dirname(DATABASE_URL.split("///")[1]), exist_ok=True)

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Start a session
    db_session = SessionLocal()

    # Check if migration has been applied
    migration = db_session.query(Migration).filter_by(name="cities_table").first()
    if not migration:
        # Import data from the world cities CSV
        with open(WORLD_CITIES_CSV_PATH, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            cities = []
            for row in reader:
                cities.append(City(
                    city=row["city"],
                    city_ascii=row["city_ascii"],
                    lat=float(row["lat"]),
                    lng=float(row["lng"]),
                    country=row["country"],
                    iso2=row["iso2"],
                    iso3=row["iso3"],
                    admin_name=row["admin_name"],
                    capital=row["capital"],
                    population=row["population"],
                    id=int(row["id"])
                ))

            # Bulk insert cities
            db_session.bulk_save_objects(cities)
            db_session.commit()

        # Generate geospatial indexes
        cities = db_session.query(City).all()
        geo_indexes = []
        for city in cities:
            geohash = geohash_encode(city.lat, city.lng)
            geo_indexes.append(GeoSpatialIndex(geohash=geohash, city_id=city.id))

        # Bulk insert geospatial indexes
        db_session.bulk_save_objects(geo_indexes)
        db_session.commit()

        # Mark migration as applied
        db_session.add(Migration(name="cities_table"))
        db_session.commit()

    db_session.close()
    print("Database prepared successfully.")

# Main script
if __name__ == "__main__":
    prepare_db()
