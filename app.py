from fastapi import FastAPI
from bs4 import BeautifulSoup
import requests
import re
from urllib.parse import urljoin

app = FastAPI()

BASE_URL = "https://hopamviet.vn"

def search_songs(query):
    """Search for songs on HopAmViet"""
    search_url = f"{BASE_URL}/chord/search.html?song={query.replace(' ', '+')}"
    response = requests.get(search_url)

    if response.status_code != 200:
        return {"error": "Failed to fetch search results"}

    soup = BeautifulSoup(response.text, "html.parser")
    songs = []

    son = soup.find_all("div", class_="col-md-12")
    if not son:
        return {"error": "No songs found"}

    # Extract first result
    song_url = urljoin(BASE_URL, son[0].h5.a['href'])

    response2 = requests.get(song_url)
    if response2.status_code != 200:
        return {"error": "Failed to fetch song details"}

    soup2 = BeautifulSoup(response2.text, "html.parser")

    try:
        title = soup2.find("div", class_="ibar mt-2").get_text(strip=True, separator='|').split('|')[0]
        artist = soup2.find("div", class_="ibar mt-2").get_text(strip=True, separator='|').split('|')[4]
        lyric = soup2.find("div", id="lyric").text.strip()
        clean_lyric = re.sub(r'\[[A-G][#b]?[mM]?[0-9]?\]', '', lyric)

        return {"title": title, "artist": artist, "lyrics": clean_lyric, "url": song_url}

    except AttributeError:
        return {"error": "Error extracting song details"}

@app.get("/search/")
def get_song(query: str):
    return search_songs(query)
