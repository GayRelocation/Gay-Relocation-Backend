from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from fastapi import Body
from dotenv import load_dotenv
import os
import openai
from routers.app import api_router
# from Database.get_verified_db import get_verified_db
# from fastapi import Depends
# from sqlalchemy.orm import Session
# import sqlite3
# from Models.models import CityMetrics
# import csv


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


# @app.post("/fill_db")
# def fill_db(password: str, verifieddb: Session = Depends(get_verified_db)):
#     """
#     Migrate data from a CSV file to Supabase PostgreSQL, generating new UUIDs.
#     """
#     # Authorization
#     if password != os.getenv("DB_MIGRATION_PASSWORD", "sahil123"):
#         return {"error": "Unauthorized"}

#     # Path to the CSV file
#     csv_file_path = "city_metrics_rows.csv"

#     # Read the CSV file
#     with open(csv_file_path, mode="r") as csvfile:
#         csv_reader = csv.DictReader(csvfile)

#         # Iterate through the rows in the CSV file
#         for row in csv_reader:
#             # Remove the 'id' field if it exists
#             row.pop("id", None)

#             # Create a new CityMetrics instance
#             new_record = CityMetrics(**row)

#             # Add the record to the Supabase session
#             verifieddb.add(new_record)

#         # Commit the session to save data in Supabase
#         verifieddb.commit()

#     return {"message": "Data migration from CSV completed successfully."}