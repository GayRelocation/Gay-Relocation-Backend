import argparse
import os
import shutil
from langchain.schema.document import Document
from utils.get_embedding_function import get_embedding_function
from langchain_chroma import Chroma
import openai
import os
from dotenv import load_dotenv
from utils.load_documents import load_documents, load_news
from utils.constants import BLOGS_COLLECTION, NEWS_COLLECTION

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Constants
CHROMA_PATH = "chroma"
DATA_PATH = "Data/Blogs"


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
        persist_directory=CHROMA_PATH, embedding_function=get_embedding_function(),
        collection_name=BLOGS_COLLECTION
    )

    existing_items = db.get(include=[])  # IDs are always included by default
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    # Filter out documents that already exist in the database
    new_documents = [
        doc for doc in documents if doc.metadata["id"] not in existing_ids]

    print(f"Adding {len(new_documents)} new documents to the database...")
    db.add_documents(new_documents)


def add_news_to_chroma():
    news = load_news()
    vector_db = Chroma(
        persist_directory=CHROMA_PATH, embedding_function=get_embedding_function(),
        collection_name=NEWS_COLLECTION
    )

    # add in batches of 100
    for i in range(0, len(news), 1000):
        vector_db.add_documents(news[i:i+1000])
        print(f"Added {i+1000} documents to the database.")

    print(f"Added {len(news)} documents to the database.")


if __name__ == "__main__":
    # add_news_to_chroma()
    main()
