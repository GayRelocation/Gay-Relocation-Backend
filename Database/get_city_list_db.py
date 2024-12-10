from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Index


# Database URL (SQLite)
DATABASE_URL = "sqlite:///./Database/CityList.db"

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

Base = declarative_base()


class CityMetricsQuery(Base):
    __tablename__ = "city_metrics"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, index=True)
    state_code = Column(String)
    state_name = Column(String, index=True)

    __table_args__ = (
        Index("idx_city_state", "city", "state_name"),
    )


# Dependency for getting the database session
def get_city_list_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
