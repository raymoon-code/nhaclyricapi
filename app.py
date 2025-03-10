from fastapi import FastAPI, Query
from bs4 import BeautifulSoup
import requests
import re
from urllib.parse import urljoin

app = FastAPI()

BASE_URL = "https://hopamviet.vn"

def search_songs(query):
    """Search for song URLs based on the query."""
    search_url = f"{BASE_URL}/chord/search.html?song={query.replace(' ', '+')}"
    response = requests.get(search_url)

    if response.status_code != 200:
        return {"error": "Failed to fetch search results"}

    soup = BeautifulSoup(response.text, "html.parser")
    song_list = []

    results = soup.find_all("div", class_="col-md-12")
    if not results:
        return {"error": "No songs found"}

    for song in results[:10]:  # Get up to 10 results
        song_link = song.find("h5").find("a")
        if song_link:
            title = song_link.text.strip()
            song_url = urljoin(BASE_URL, song_link['href'])
            song_list.append({"title": title, "url": song_url})

    return {"songs": song_list}

def get_song_details(song_url):
    """Fetch the title, artist, and lyrics from a song URL."""
    response = requests.get(song_url)
    if response.status_code != 200:
        return {"error": "Failed to fetch song details"}

    soup = BeautifulSoup(response.text, "html.parser")

    try:
        title_info = soup.find("div", class_="ibar mt-2").get_text(strip=True, separator='|').split('|')
        title = title_info[0] if len(title_info) > 0 else "Unknown Title"
        artist = title_info[4] if len(title_info) > 4 else "Unknown Artist"
        
        lyric = soup.find("div", id="lyric").text.strip()
        clean_lyric = re.sub(r'\[[A-G][#b]?[mM]?[0-9]?\]', '', lyric)

        return {"title": title, "artist": artist, "lyrics": clean_lyric, "url": song_url}

    except AttributeError:
        return {"error": "Error extracting song details"}

@app.get("/search/")
def search_song(query: str = Query(..., description="Search for songs by title")):
    return search_songs(query)

@app.get("/song/")
def fetch_song_details(url: str = Query(..., description="Fetch details of a song by URL")):
    return get_song_details(url)
