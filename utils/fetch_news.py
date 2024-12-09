from bs4 import BeautifulSoup
from utils.constants import MAIN_URL
import requests


def fetch_news(query):

    URL = f"{MAIN_URL}/{query}".replace("\\", "/")
    realtors_page = requests.get(URL)

    try:
        if realtors_page.status_code == 200:
            soup = BeautifulSoup(realtors_page.content, 'html.parser')
            news_soup = soup.find_all(class_="news_block")
            realtors_soup = soup.find_all(class_="agent_list_wrap")

            news = []
            for news_item in news_soup:
                title = news_item.find("h5").text
                url = news_item.find("h5").find("a")["href"]
                # concate all inside p tags
                description = " ".join(
                    [p.text for p in news_item.find_all("p")])
                news.append({
                    "name": title,
                    "url": url,
                    "description": description
                })

            realtors = []
            for realtor in realtors_soup:
                name = realtor.find("h3").find("a").text
                name_url = realtor.find("h3").find("a")["href"]
                agent_type = realtor.find("span", class_="agent_type").text
                agent_type = agent_type.replace("-", "").strip()
                stars = 5 if realtor.find("div", class_="agent_review").find(
                    "img") else None
                profile_url = realtor.find(
                    "a", text="View Full Profile")["href"]
                contact_url = realtor.find("a", text="Contact")["href"]
                img_url = MAIN_URL + \
                    realtor.find("div", class_="agent_small_pic").find(
                        "img")["data-src"]
                # description class agent_info inside p tag
                description = " ".join([p.text for p in realtor.find(
                    "div", class_="agent_info").find_all("p")]).replace("...read more", "")

                realtors.append({
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
                "url": URL,
                "news": news,
                "realtors": realtors[:2],
            }
        else:
            print(
                f"Failed to fetch the page. Status code: {realtors_page.status_code}")
            return []
    except Exception as e:
        print(f"Failed to parse the page. Error: {e}")
        return []
