import asyncio
import httpx
import os
from PIL import Image
from io import BytesIO
import sys

# Set encoding for Windows terminal
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# --- CONFIG ---
HERO_DIR = "static/assets/hero"
API_KEY = "c7c066ef756e5e7d2349ec6acb2924f3"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMG_URL = "https://image.tmdb.org/t/p/original"

# Selection of movies with verified backdrops
HERO_MOVIES = [
    {"Title": "Balls Up", "filename": "balls_up.webp"},
    {"Title": "The Call", "filename": "the_call.webp"},
    {"Title": "Alpha", "filename": "alpha.webp"},
    {"Title": "The Raja Saab", "filename": "The_RajaSaab.webp"},
    {"Title": "Peddi", "filename": "paddi-futclymrsd-landscape.webp"},
    {"Title": "Dacoit", "filename": "Dacoit.webp"},
    {"Title": "Biker", "filename": "Biker.webp"},
    {"Title": "Mercy", "filename": "Mercy.webp"}
]

async def update_hero_image(client, movie):
    title = movie["Title"]
    filename = movie["filename"]
    save_path = os.path.join(HERO_DIR, filename)

    if os.path.exists(save_path):
        print(f"Skipping: {title}")
        return True

    print(f"Searching: {title}")
    try:
        search_url = f"{TMDB_BASE_URL}/search/movie"
        resp = await client.get(search_url, params={"api_key": API_KEY, "query": title})
        if resp.status_code != 200: return False
        
        results = resp.json().get("results", [])
        if not results: return False
        
        # Pick the most relevant one (usually the first)
        movie_data = results[0]
        movie_id = movie_data["id"]
        
        # Prefer actual high-res backdrops from the images endpoint
        images_url = f"{TMDB_BASE_URL}/movie/{movie_id}/images"
        img_resp = await client.get(images_url, params={"api_key": API_KEY})
        
        backdrop_path = None
        if img_resp.status_code == 200:
            backdrops = img_resp.json().get("backdrops", [])
            if backdrops:
                backdrops.sort(key=lambda x: x["width"], reverse=True)
                backdrop_path = backdrops[0]["file_path"]
        
        if not backdrop_path:
            backdrop_path = movie_data.get("backdrop_path")
            
        if not backdrop_path:
            print(f"  No backdrop for {title}")
            return False

        img_url = f"{TMDB_IMG_URL}{backdrop_path}"
        print(f"  Downloading: {img_url}")
        img_data = await client.get(img_url)
        
        img = Image.open(BytesIO(img_data.content))
        img.save(save_path, "WEBP", quality=90)
        print(f"  Saved: {save_path}")
        return True

    except Exception as e:
        return False

async def main():
    if not os.path.exists(HERO_DIR):
        os.makedirs(HERO_DIR)

    async with httpx.AsyncClient() as client:
        tasks = [update_hero_image(client, m) for m in HERO_MOVIES]
        await asyncio.gather(*tasks)
    
    print("\nHero update complete.")

if __name__ == "__main__":
    asyncio.run(main())
