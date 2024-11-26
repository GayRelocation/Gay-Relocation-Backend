from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import json
from sqlalchemy import Column, Integer, String


# Database URL (SQLite)
DATABASE_URL = "sqlite:///./Database/news.db"

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

# Base class for SQLAlchemy models
Base = declarative_base()


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    url = Column(String, index=True)

# Dependency for getting the database session


def get_news_db():
    """
    Dependency to get a SQLAlchemy database session.
    Ensures proper handling of session lifecycle (open, close).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
