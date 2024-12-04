from bs4 import BeautifulSoup
from utils.constants import MAIN_URL
import requests


def fetch_news(query):

    URL = f"{MAIN_URL}/{query}".replace("\\", "/")
    gay_realtors_page = requests.get(URL)

    if gay_realtors_page.status_code == 200:
        soup = BeautifulSoup(gay_realtors_page.content, 'html.parser')
        news_soup = soup.find_all(class_="news_block")
        gay_realtors_soup = soup.find_all(class_="agent_list_wrap")

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

        gay_realtors = []
        for realtor in gay_realtors_soup:
            name = realtor.find("h3").find("a").text
            name_url = realtor.find("h3").find("a")["href"]
            agent_type = realtor.find("span", class_="agent_type").text
            agent_type = agent_type.replace("-", "").strip()
            stars = 5 if realtor.find("div", class_="agent_review").find(
                "img") else None
            profile_url = realtor.find("a", text="View Full Profile")["href"]
            contact_url = realtor.find("a", text="Contact")["href"]
            img_url = "https://www.gayrealestate.com" + \
                realtor.find("div", class_="agent_small_pic").find(
                    "img")["data-src"]
            # description class agent_info inside p tag
            description = " ".join([p.text for p in realtor.find(
                "div", class_="agent_info").find_all("p")]).replace("...read more", "")

            gay_realtors.append({
                "name": name,
                "description": description,
                "name_url": name_url,
                "agent_type": agent_type,
                "stars": stars,
                "profile_url": profile_url,
                "contact_url": contact_url,
                "img_url": img_url,
            })

        return {
            "news": news,
            "gay_realtors": gay_realtors
        }
    else:
        print(
            f"Failed to fetch the page. Status code: {gay_realtors_page.status_code}")
        return []
