from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Database URL (SQLite)
DATABASE_URL = "sqlite:///./Database/CityMetricsDB.db"

# Create the database engine
engine = create_engine(
    DATABASE_URL,
    # Required for SQLite in a multithreaded environment
    connect_args={"check_same_thread": False}
)

# Configure the session maker
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Dependency for getting the database session
def get_city_list_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
