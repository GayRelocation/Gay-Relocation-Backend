import json
from langchain.schema.document import Document
import os

def load_documents(data_path: str) -> list[Document]:
    """
    Load documents from a data source. Here, we assume a simple structure
    where each file is JSON with 'id' and 'title'.
    """
    data_path = os.path.join(os.path.dirname(__file__), '..', 'Data', "Blogs", data_path)
    documents = []
    with open(data_path, "r") as file:
        data = json.load(file)
        for item in data:
            doc = Document(
                page_content=item["title"],
                metadata={"id": item["id"]}
            )
            documents.append(doc)

    print(f"Loaded {len(documents)} documents.")
    return documents
