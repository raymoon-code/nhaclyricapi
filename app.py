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
        title_tag = song.find("h5")
        if not title_tag:
            continue  # Skip if <h5> is missing

        song_link = title_tag.find("a")
        if not song_link:
            continue  # Skip if <a> is missing

        title = song_link.text.strip()
        song_url = urljoin(BASE_URL, song_link['href'])

        # Extract lyrics preview
        lyrics_preview_tag = song.find("em")
        lyrics_preview = lyrics_preview_tag.get_text(strip=True) if lyrics_preview_tag else "No preview available"

        song_list.append({
            "title": title,
            "url": song_url,
            "lyrics_preview": lyrics_preview
        })

    return {"songs": song_list} if song_list else {"error": "No valid songs found"}

def get_song_details(song_url):
    """Fetch the title, artist, and lyrics from a song URL."""
    response = requests.get(song_url)
    if response.status_code != 200:
        return {"error": "Failed to fetch song details"}

    soup = BeautifulSoup(response.text, "html.parser")

    try:
        # Extract title and artist
        title_info = soup.find("div", class_="ibar mt-2")
        if not title_info:
            return {"error": "Song metadata not found"}

        title_parts = title_info.get_text(strip=True, separator='|').split('|')
        title = title_parts[0] if len(title_parts) > 0 else "Unknown Title"
        artist = title_parts[4] if len(title_parts) > 4 else "Unknown Artist"

        # Extract lyrics
        lyric_section = soup.find("div", id="lyric")
        if not lyric_section:
            return {"error": "Lyrics not found"}

        raw_lyric = lyric_section.get_text(strip=True)
        clean_lyric = re.sub(r'\[[A-G][#b]?[mM]?[0-9]?\]', '', raw_lyric)  # Remove chord notations

        return {
            "title": title,
            "artist": artist,
            "lyrics": clean_lyric,
            "url": song_url
        }

    except AttributeError:
        return {"error": "Error extracting song details"}

@app.get("/search/")
def search_song(query: str = Query(..., description="Search for songs by title")):
    return search_songs(query)

@app.get("/song/")
def fetch_song_details(url: str = Query(..., description="Fetch details of a song by URL")):
    return get_song_details(url)
