from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Database URL (SQLite)
DATABASE_URL = "sqlite:///./Database/CityMetricsDB.db"

# Create the database engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Required for SQLite in a multithreaded environment
)

# Configure the session maker
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# Base class for SQLAlchemy models
Base = declarative_base()

# Dependency for getting the database session
def get_db():
    """
    Dependency to get a SQLAlchemy database session.
    Ensures proper handling of session lifecycle (open, close).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
