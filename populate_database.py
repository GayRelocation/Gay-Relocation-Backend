import argparse
import os
import shutil
from langchain.schema.document import Document
from get_embedding_function import get_embedding_function
from langchain_chroma import Chroma
import openai
import os
from dotenv import load_dotenv
from utils.load_documents import load_documents

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Constants
CHROMA_PATH = "chroma"
DATA_PATH = "Filtered"


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true",
                        help="Reset the database.")
    parser.add_argument("--query", type=str,
                        help="Query to search for relevant documents.")
    
    for file in os.listdir(DATA_PATH):
        documents = load_documents(file)
        add_to_chroma(documents)


def add_to_chroma(documents: list[Document]):
    """
    Add documents to the Chroma database.
    """
    # Load or create the Chroma database
    db = Chroma(
        persist_directory=CHROMA_PATH, embedding_function=get_embedding_function()
    )

    existing_items = db.get(include=[])  # IDs are always included by default
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    # Filter out documents that already exist in the database
    new_documents = [
        doc for doc in documents if doc.metadata["id"] not in existing_ids]

    print(f"Adding {len(new_documents)} new documents to the database...")
    db.add_documents(new_documents)


if __name__ == "__main__":
    main()
