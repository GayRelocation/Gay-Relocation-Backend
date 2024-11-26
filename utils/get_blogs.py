import requests
from bs4 import BeautifulSoup

def fetch_blogs(blog_ids: list[str]) -> dict:
    """
    Fetch blogs from the database using the provided document IDs.
    """
    blogs = []

    for blog_id in blog_ids:
        blog = requests.get(
            "https://www.gayrealestate.com/blog/wp-json/wp/v2/posts/" + str(blog_id))
        if blog.status_code == 200:
            blogs.append(blog.json())

    return blogs


def filter_blog(blog: dict) -> dict:
    """
    Filter the blog content to include only the necessary fields.
    """
    return {
        "title": blog["title"]["rendered"],
        "description": BeautifulSoup(blog["content"]["rendered"], "html.parser").text,
    }
    
def filter_blogs(blogs: list[dict]) -> list[dict]:
    """
    Filter the blog content to include only the necessary fields.
    """
    return [filter_blog(blog) for blog in blogs]