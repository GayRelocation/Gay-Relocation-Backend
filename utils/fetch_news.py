from bs4 import BeautifulSoup
from utils.constants import MAIN_URL
import requests


def fetch_news(query):
    """
    Fetch news articles based on the query using Beautiful Soup.
    """
    # Perform a web search using the query
    URL = f"{MAIN_URL}/{query}".replace("\\", "/")
    gay_realtors_page = requests.get(URL)

    if gay_realtors_page.status_code == 200:
        soup = BeautifulSoup(gay_realtors_page.content, 'html.parser')
        news_soup = soup.find_all(class_="news_block")

        news = []

        for news_item in news_soup:
            title = news_item.find("h5").text
            url = news_item.find("h5").find("a")["href"]
            # concate all inside p tags
            description = " ".join([p.text for p in news_item.find_all("p")])
            news.append({
                "name": title,
                "url": url,
                "description": description
            })

        return news
    else:
        print(
            f"Failed to fetch the page. Status code: {gay_realtors_page.status_code}")
        return []
