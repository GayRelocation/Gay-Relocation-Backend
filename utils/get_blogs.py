import json


def fetch_blogs(document_ids: list[str]) -> dict:

    with open("data/data.json", "r") as file:
        data = json.load(file)
        documents = [doc for doc in data if doc["id"] in document_ids]
        
    return documents
