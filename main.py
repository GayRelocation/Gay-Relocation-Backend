import json
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from utils.query_data import query_rag
from dotenv import load_dotenv
import os
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the request model


class QueryRequest(BaseModel):
    city_1: str
    city_2: str


def sample_data(city_1: str, city_2: str):
    with open('sample_data.json') as f:
        test_data = json.load(f)
    test_data['city_1']['name'] = city_1
    test_data['city_2']['name'] = city_2
    return test_data


@app.post("/comparison")
async def handle_query(request: QueryRequest):
    prompt = "Resources for the LGBTQ+ only for city " + request.city_2
    result = query_rag(prompt)
    data = sample_data(request.city_1, request.city_2)
    return {
        **data,
        **result
    }
