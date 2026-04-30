"""
MovieRulz Deep Scraper (Playwright) - v3
Extracts: link, quality, title, hero, heroin, year, language, genre, type, image link
Improved regex for Starring and Genres.
Scrapes up to 379 pages.
"""

import os
import re
import time
import datetime
import csv
from playwright.sync_api import sync_playwright

# ─── CONFIG ──────────────────────────────────────────────────────────────────
BASE_URL    = "https://www.5movierulz.capital/"
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vortex_data.csv")
MAX_PAGES   = 379 

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def clean_title(raw):
    m = re.match(r'^(.+?)\s*\(\d{4}\)', raw)
    if m: return m.group(1).strip()
    return raw.strip()

def detect_quality(text):
    for q in ["HDRip", "DVDScr", "DVDRip", "BRRip", "WEBRip", "WEB-DL", "CAMRip", "BluRay"]:
        if q.lower() in text.lower():
            return q
    return "N/A"

def detect_language(text):
    for lang in ["Hindi", "Telugu", "Tamil", "Malayalam", "Kannada",
                 "Bengali", "Punjabi", "Dubbed", "English", "Marathi"]:
        if lang.lower() in text.lower():
            return lang
    return "Other"

def detect_year(text):
    m = re.search(r'\((\d{4})\)', text)
    return m.group(1) if m else "N/A"

def detect_type(text):
    text_lower = text.lower()
    if any(k in text_lower for k in ["series", "season", "episode", "tv show"]):
        return "Series"
    return "Movie"

def parse_movie_details(page, url):
    """Visit the movie page and extract hero, heroin, genre."""
    print(f"    Visiting Details: {url}")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(1000)
        
        soup_text = page.inner_text("body")
        
        hero = "N/A"
        heroin = "N/A"
        
        # Improved Cast Regex
        # Starring by: Name1, Name2... or Cast: Name1...
        starring_match = re.search(r"(Starring|Cast|Actors)( by)?:\s*(.*)", soup_text, re.IGNORECASE)
        if starring_match:
            cast_line = starring_match.group(3).split("\n")[0]
            cast_list = cast_line.split(",")
            if len(cast_list) > 0: hero = cast_list[0].strip().replace("\ufffd", "")
            if len(cast_list) > 1: heroin = cast_list[1].strip().replace("\ufffd", "")
        
        genre = "N/A"
        # Genres: ... or Genre: ...
        genre_match = re.search(r"Genres?:\s*(.*)", soup_text, re.IGNORECASE)
        if genre_match:
            genre = genre_match.group(1).split("\n")[0].strip().replace("\ufffd", "")
        else:
            categories = page.query_selector_all("a[rel='category tag']")
            if categories:
                genre = ", ".join([c.inner_text().strip() for c in categories])

        # HD Image Extraction from Detail Page
        hd_img_link = "N/A"
        img_element = page.query_selector(".entry-content img, .movie-image img")
        if img_element:
            hd_img_link = img_element.get_attribute("src") or img_element.get_attribute("data-src") or "N/A"

        return hero, heroin, genre, hd_img_link
    except Exception as e:
        print(f"    Error details for {url}: {e}")
        return "N/A", "N/A", "N/A", "N/A"

# ─── MAIN ────────────────────────────────────────────────────────────────────

def scrape_pages(max_pages=MAX_PAGES):
    print("=" * 75)
    print("  MovieRulz Deep Scraper v3 - Total Data Extraction")
    print(f"  Target : {BASE_URL}")
    print(f"  Pages  : {max_pages}")
    print(f"  Time   : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)

    all_data_count = 0
    seen_links = set()

    # If it's a multi-page scrape (full or initial), we might want to overwrite or append.
    # For now, let's keep the logic simple: overwrite if starting from page 1, else append.
    file_mode = "w" if max_pages > 2 else "a"
    
    # If the file doesn't exist, always use "w"
    if not os.path.exists(OUTPUT_FILE):
        file_mode = "w"

    if file_mode == "w":
        with open(OUTPUT_FILE, "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Title", "Year", "Language", "Quality", "Type", "Hero", "Heroin", "Genre", "Image Link", "Movie Link"])

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        detail_page = context.new_page()

        for page_num in range(1, max_pages + 1):
            url = f"{BASE_URL}movies/page/{page_num}" if page_num > 1 else BASE_URL
            print(f"\n[Page {page_num}/{max_pages}] {url}")
            
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)
            except Exception as e:
                print(f"  Error loading list page: {e}")
                continue

            anchors = page.query_selector_all("a[href*='movie-watch-online-free']")
            new_on_page = 0
            
            for anchor in anchors:
                href = anchor.get_attribute("href") or ""
                if not href or href in seen_links:
                    continue
                seen_links.add(href)
                full_link = href if href.startswith("http") else BASE_URL.rstrip("/") + "/" + href.lstrip("/")

                img_link = "N/A"
                img = anchor.query_selector("img")
                if img:
                    img_link = img.get_attribute("src") or img.get_attribute("data-src") or "N/A"
                    raw_title = img.get_attribute("alt") or img.get_attribute("title") or ""
                else:
                    raw_title = anchor.get_attribute("title") or anchor.inner_text().strip()
                
                if not raw_title or len(raw_title) < 3:
                    slug = href.split("/")[-2] if "/" in href else href
                    raw_title = slug.replace("-", " ").title()

                year = detect_year(raw_title)
                lang = detect_language(raw_title)
                qual = detect_quality(raw_title)
                mtype = detect_type(raw_title)
                title = clean_title(raw_title)

                try:
                    hero, heroin, genre, hd_img_link = parse_movie_details(detail_page, full_link)
                    if hd_img_link != "N/A":
                        img_link = hd_img_link
                except Exception as e:
                    print(f"    Warning: Could not get details for {title}: {e}")
                    hero, heroin, genre = "N/A", "N/A", "Drama"

                row = [title, year, lang, qual, mtype, hero, heroin, genre, img_link, full_link]
                
                with open(OUTPUT_FILE, "a", encoding="utf-8", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(row)
                
                all_data_count += 1
                new_on_page += 1

            print(f"  >> Extracted {new_on_page} new. Total unique: {all_data_count}")
            
            if new_on_page == 0 and page_num > 5:
                print("  No new content found. Stopping early.")
                break

        browser.close()

    print(f"\n[DONE] Scraped {all_data_count} movies.")
    print(f"Data saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    scrape_pages()
