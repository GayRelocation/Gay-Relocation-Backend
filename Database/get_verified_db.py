from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from Models import Base
from Models.models import *
import os

SUPABASE_URL = os.getenv("SUPABASE_DB_URL")

# Create the database engine
engine = create_engine(
    SUPABASE_URL,
    pool_size=5,        
    max_overflow=10,    
)

# Configure the session maker
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def create_tables():
    """
    Create tables defined in the Models if they do not exist.
    """
    Base.metadata.create_all(bind=engine)


# create_tables()

def get_verified_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
