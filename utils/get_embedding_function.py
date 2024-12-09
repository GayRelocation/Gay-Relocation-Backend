from langchain_openai import OpenAIEmbeddings

def get_embedding_function():
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    return embeddings
