from fastapi import FastAPI, Query
from bs4 import BeautifulSoup
import requests
import re
from urllib.parse import urljoin

app = FastAPI()

BASE_URL = "https://hopamviet.vn"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

def search_songs(query):
    """Search for song URLs based on the query."""
    search_url = f"{BASE_URL}/chord/search?song={query.replace(' ', '+')}"
    response = requests.get(search_url, headers=HEADERS)

    if response.status_code != 200:
        return {"error": f"Failed to fetch search results: status {response.status_code}"}

    soup = BeautifulSoup(response.text, "html.parser")
    song_list = []

    results = soup.find_all("a", class_="song-card")
    for song in results[:10]:
        song_url = song.get('href')
        if not song_url:
            continue
        song_url = urljoin(BASE_URL, song_url)

        # Extract title
        title_div = song.find("div", class_="font-bold")
        song_title = title_div.text.strip() if title_div else "Unknown Title"

        # Extract artist
        artist_span = song.find("span", class_="truncate")
        artist = artist_span.text.strip() if artist_span else "Unknown Artist"

        # Combine title and artist for display
        display_title = f"{song_title} - {artist}"

        # Extract lyrics preview
        preview_div = song.find("div", class_="italic")
        lyrics_preview = preview_div.text.strip() if preview_div else "No preview available"

        song_list.append({
            "title": display_title,
            "url": song_url,
            "lyrics_preview": lyrics_preview
        })

    return {"songs": song_list} if song_list else {"error": "No songs found"}

def get_song_details(song_url):
    """Fetch the title, artist, and lyrics from a song URL."""
    response = requests.get(song_url, headers=HEADERS)
    if response.status_code != 200:
        return {"error": f"Failed to fetch song details: status {response.status_code}"}

    soup = BeautifulSoup(response.text, "html.parser")

    try:
        # Extract title and artist from page title: "Hợp âm [Song] - [Artist]"
        page_title = soup.title.text.strip() if soup.title else ""
        if page_title.startswith("Hợp âm "):
            page_title = page_title[len("Hợp âm "):]
        
        parts = page_title.split(" - ")
        title = parts[0].strip() if len(parts) > 0 else "Unknown Title"
        artist = parts[1].strip() if len(parts) > 1 else "Unknown Artist"

        # Extract lyrics block
        lyric_section = soup.find("div", class_="lyric-block")
        if not lyric_section:
            lyric_section = soup.find(id="lyricBox")
            
        if not lyric_section:
            return {"error": "Lyrics not found"}

        # Decompose chord span elements
        for chord_span in lyric_section.find_all("span", class_="chord"):
            chord_span.decompose()

        raw_lyric = lyric_section.text.strip()
        # Clean bracketed chords and redundant white spaces
        clean_lyric = re.sub(r'\[[A-G][#b]?[mM]?[0-9]?\]', '', raw_lyric)
        clean_lyric = re.sub(r'\n{3,}', '\n\n', clean_lyric)

        return {
            "title": title,
            "artist": artist,
            "lyrics": clean_lyric,
            "url": song_url
        }

    except Exception as e:
        return {"error": f"Error extracting song details: {str(e)}"}

@app.get("/search/")
def search_song(query: str = Query(..., description="Search for songs by title")):
    return search_songs(query)

@app.get("/song/")
def fetch_song_details(url: str = Query(..., description="Fetch details of a song by URL")):
    return get_song_details(url)
