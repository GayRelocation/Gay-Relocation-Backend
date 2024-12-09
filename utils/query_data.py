
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from openai import OpenAI
from utils.get_embedding_function import get_embedding_function
from utils.get_blogs import fetch_blogs, filter_blogs
from pydantic import BaseModel
from typing import List
from utils.constants import CHROMA_PATH, BLOGS_COLLECTION


class Resource(BaseModel):
    title: str
    description: str
    strings: list[str]


class ResourceResponse(BaseModel):
    response: List[Resource]


sample_json = {
    "title": "LGBTQ+ Community Centers",
    "description": "Spaces offering support, resources, and social connections.",
    "content": [
        "SF LGBT Center",
        "GLBT Historical Society Museum",
        "The LGBTQ+ Youth Space",
        "Openhouse (for LGBTQ+ seniors)"
    ]
}


PROMPT_TEMPLATE = """
**Task Description:**

You are tasked with finding and listing resources related to LGBTQ+ support services, based on the provided context. The context consists of blogs that contain information on various LGBTQ+ topics and resources. If context is not provided, please generate the response based on your own knowledge.

**Instructions:**

- **Read the context carefully.**
- **Provide a list of resources based on the query provided, using only the information from the context.**
- Each resource should include:
  - A **title**: a very short string that describes the resource as title.
  - A **description**: a short description with useful piece of information about the resource.
- There should be at least 4 resources with atleast 4 strings in content in the list.
- **Provide as many resources as you can find based on the context.**
- Your output should follow the JSON format specified in 
  - json_template: {json_template}

**Example Titles (for reference):**

1. LGBTQ+ Health Services
2. LGBTQ+ Community Centers
3. Legal Support & Advocacy
4. LGBTQ+ Inclusive Education
5. LGBTQ+ Nightlife & Entertainment
6. LGBTQ+ Employment Resources
7. Support & Social Groups

---

**Context:**

{context}

---

**Question:**

{question}

---

**Answer:**
"""

client = OpenAI()


def format_file_reference(reference):
    if reference is None:
        return "Location: Unknown"
    # Split the reference into file path, page, and line
    file_path, page, line = reference.split(":")

    # Extract the file name from the full path
    file_name = file_path.split("\\")[-1]

    # Convert page and line numbers to be human-readable
    display_page = int(page) + 1  # Convert zero-indexed page to one-indexed
    display_line = int(line)

    # Construct and return the formatted string
    return f"""
**File Name**: `{file_name}`  
**Page no**: `{display_page}`   **Line no**: `{display_line}`
"""


def query_rag(from_city, to_city):

    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=get_embedding_function(),
        collection_name=BLOGS_COLLECTION
    )

    # Search the DB.
    query_text = "Resources for the LGBTQ+ Community in" + to_city
    temperature = 0.2
    results = db.similarity_search_with_relevance_scores(query_text, k=3)
    if len(results) == 0 or results[0][1] < 0.9:
        query_text = f"From {from_city} to {to_city}: LGBTQ+ Cities"
        results = db.similarity_search_with_relevance_scores(query_text, k=3)

    if len(results) == 0:
        return {"lgbtq-resources": "No relevant resources found."}

    sources = []
    for doc, score in results:
        if score < 0.9:
            continue  # Skip low-relevance scores
        sources.append({
            "id": doc.metadata.get("id", "unknown"),
            "score": score,
            "content": doc.page_content,
        })

    # Fetch blogs based on source IDs
    blog_ids = [source["id"] for source in sources]
    blogs = fetch_blogs(blog_ids)
    blogs = filter_blogs(blogs)

    # Create the context text for the prompt
    context_text = "\n\n---\n\n".join(
        [f"title: {blog['title']}\ndescription: {blog['description']}" for blog in blogs]
    )

    if len(blogs) == 0:
        context_text = "No relevant blogs found, in the database. Please use your own knowledge to generate the response."
        temperature = 0.8

    # Format the prompt using the template
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(
        context=context_text,
        question=query_text,
        json_template=sample_json
    )

    # Make the API call for the completion
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format=ResourceResponse,
        temperature=temperature
    )

    # Parse the response into the expected Resource format
    response_text = completion.choices[0].message.parsed.response

    return {
        "lgbtq_resources": response_text,  # Return the response text
        "sources": sources,  # Add the sources for traceability
    }
