import csv
import asyncio
import httpx
import os

# --- CONFIG ---
CSV_PATH = "scraper/movierulz_deep_data.csv"
OUTPUT_PATH = "scraper/movierulz_deep_data_updated.csv"
API_KEY = "c7c066ef756e5e7d2349ec6acb2924f3"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMG_URL = "https://image.tmdb.org/t/p/w500"

# Language Code Mapping
LANG_MAP = {
    "te": "Telugu",
    "hi": "Hindi",
    "ta": "Tamil",
    "en": "English",
    "ml": "Malayalam",
    "kn": "Kannada",
    "bn": "Bengali",
    "pa": "Punjabi",
    "mr": "Marathi",
    "gu": "Gujarati"
}

async def fetch_movie_meta(client, title, current_year):
    """Fetch movie poster, year, and language from TMDB."""
    try:
        url = f"{TMDB_BASE_URL}/search/movie"
        params = {
            "api_key": API_KEY,
            "query": title,
            "year": current_year if (current_year and current_year != "N/A") else ""
        }
        resp = await client.get(url, params=params, timeout=10.0)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                movie = results[0]
                new_poster = f"{TMDB_IMG_URL}{movie['poster_path']}" if movie.get("poster_path") else None
                
                # Extract year
                new_year = None
                if movie.get("release_date"):
                    new_year = movie["release_date"][:4]
                
                # Extract language
                new_lang = None
                lang_code = movie.get("original_language")
                if lang_code in LANG_MAP:
                    new_lang = LANG_MAP[lang_code]
                
                return {"poster": new_poster, "year": new_year, "lang": new_lang}
    except Exception:
        pass
    return None

async def main():
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found.")
        return

    print(f"Reading {CSV_PATH}...")
    with open(CSV_PATH, mode='r', encoding='utf-8') as f:
        reader = list(csv.DictReader(f))

    print(f"Starting deep metadata update (Poster, Year, Lang) for {len(reader)} movies...")
    
    async with httpx.AsyncClient() as client:
        batch_size = 20
        for i in range(0, len(reader), batch_size):
            batch = reader[i : i + batch_size]
            tasks = []
            for row in batch:
                tasks.append(fetch_movie_meta(client, row['Title'], row['Year']))
            
            results = await asyncio.gather(*tasks)
            
            p_upd, y_upd, l_upd = 0, 0, 0
            for j, meta in enumerate(results):
                if meta:
                    if meta["poster"]:
                        reader[i + j]['Image Link'] = meta["poster"]
                        p_upd += 1
                    if meta["year"]:
                        reader[i + j]['Year'] = meta["year"]
                        y_upd += 1
                    if meta["lang"]:
                        reader[i + j]['Language'] = meta["lang"]
                        l_upd += 1
            
            print(f"Processed {i + len(batch)}/{len(reader)}... (Batch: +{p_upd} posters, +{y_upd} years, +{l_upd} langs)")
            
            # Save incrementally every 100 movies
            if (i + batch_size) % 100 == 0 or (i + batch_size) >= len(reader):
                with open(OUTPUT_PATH, mode='w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=reader[0].keys())
                    writer.writeheader()
                    writer.writerows(reader)
            
            await asyncio.sleep(0.1)

    print(f"FINAL SAVE to {OUTPUT_PATH}...")
    print("DONE! Poster, Year, and Language synchronization complete.")

if __name__ == "__main__":
    asyncio.run(main())
