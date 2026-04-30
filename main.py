from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import re
import httpx
from typing import List, Optional
from pydantic import BaseModel
from recommendation_model import MovieEngine
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
import asyncio
import threading

# Load environment variables
load_dotenv()

# Setup logging to file
logging.basicConfig(filename='app_errors.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s: %(message)s')

# --- DATABASE SETUP ---
DB_URL = "sqlite:///./database.db"
engine_db = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_db)
Base = declarative_base()

# TMDB API Configuration (Load from .env for security)
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "c7c066ef756e5e7d2349ec6acb2924f3") 
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMG_URL = "https://image.tmdb.org/t/p/w500"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, unique=True, index=True)
    email = Column(String, unique=True)
    display_name = Column(String)
    photo_url = Column(String)
    last_login = Column(DateTime, default=datetime.utcnow)
    mood_last_reset = Column(DateTime, default=datetime.utcnow) # Trigger Field
    blocked = Column(Boolean, default=False)
    is_owner = Column(Boolean, default=False)
    # Relationship to Watchlist
    watchlist = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")

class Watchlist(Base):
    __tablename__ = "watchlist"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    movie_link = Column(String)
    title = Column(String)
    image_link = Column(String)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="watchlist")

class WatchProgress(Base):
    __tablename__ = "watch_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    movie_id = Column(String, index=True)
    title = Column(String)
    image_link = Column(String)
    progress = Column(Float)
    current_time = Column(Float)
    duration = Column(Float)
    last_watched = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

Base.metadata.create_all(bind=engine_db)

# --- APP SETUP ---
app = FastAPI(title="RL Movie Recommendation System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = "scraper/vortex_data.csv"
rec_engine = MovieEngine(DATA_PATH)

class AuthUser(BaseModel):
    uid: str
    email: str
    displayName: Optional[str] = ""
    photoURL: Optional[str] = ""

class RewardUpdate(BaseModel):
    uid: Optional[str] = "guest"
    movie_link: str
    reward: float

class ProgressUpdate(BaseModel):
    uid: str
    movie_id: str
    title: str
    image_link: str
    progress: float
    current_time: float
    duration: float

# --- AUTH & REFRESH TRIGGER ---
@app.post("/api/auth")
async def auth_user(user_data: AuthUser):
    db = SessionLocal()
    try:
        # Check by UID first
        user = db.query(User).filter(User.uid == user_data.uid).first()
        
        # If not found by UID, check by Email (since email is unique)
        if not user and user_data.email:
            user = db.query(User).filter(User.email == user_data.email).first()
            if user:
                # Update UID to the new one if they match emails
                user.uid = user_data.uid
        
        refreshed = False
        
        if user:
            if user.blocked:
                raise HTTPException(status_code=403, detail="ACCOUNT TERMINATED")
            
            # Handle migration: initialize mood_last_reset if it is None
            if user.mood_last_reset is None:
                user.mood_last_reset = datetime.utcnow()
                db.commit()

            if datetime.utcnow() - user.mood_last_reset > timedelta(days=90):
                rec_engine.load_model(user_data.uid)
                rec_engine.seasonal_refresh()
                rec_engine.save_model(user_data.uid)
                user.mood_last_reset = datetime.utcnow()
                refreshed = True
                
            user.last_login = datetime.utcnow()
            user.display_name = user_data.displayName
            display_name_lower = (user.display_name or "").lower()
            if display_name_lower in ['owner', 'admin'] or user.email == 'talupulayaswanth13@gmail.com':
                user.is_owner = True
        else:
            display_name_lower = (user_data.displayName or "").lower()
            user = User(
                uid=user_data.uid,
                email=user_data.email,
                display_name=user_data.displayName,
                photo_url=user_data.photoURL,
                mood_last_reset=datetime.utcnow(),
                is_owner=True if display_name_lower in ['owner', 'admin'] or user_data.email == 'talupulayaswanth13@gmail.com' else False
            )
            db.add(user)
        
        db.commit()
        return {
            "status": "success", 
            "uid": user_data.uid, 
            "refreshed": refreshed,
            "is_owner": user.is_owner
        }
    except Exception as e:
        logging.error(f"AUTH ERROR: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# --- REMAINING API ENDPOINTS ---
@app.get("/api/recommend")
async def get_recommendations(
    uid: str = "guest", 
    n: int = 30, 
    genre: Optional[str] = None, 
    lang: Optional[str] = None, 
    mtype: Optional[str] = None
):
    rec_engine.load_model(uid)
    recs = rec_engine.recommend(n, genre=genre, lang=lang, mtype=mtype)
    return {"results": recs}

@app.get("/api/trending")
async def get_trending(n: int = 60):
    if rec_engine.movies_df.empty: return {"results": []}
    results = rec_engine.movies_df.head(n).to_dict('records')
    return {"results": results}

@app.get("/api/recommend/hero")
async def get_hero_recommendations(uid: str = "guest"):
    rec_engine.load_model(uid)
    
    # 2026 Featured & Trending Blockbusters with verified High-Res TMDB Backdrops
    hero_movies = [
        {"Title": "The Raja Saab", "Language": "Telugu", "Year": "2026", "Genre": "Horror, Comedy, Romance", "Type": "Movie", "Desc": "Prabhas in a grand horror-comedy-romance spectacle. A royal treat for fans!", "LocalPoster": "/static/assets/hero/The_RajaSaab.webp"},
        {"Title": "Peddi", "Language": "Telugu", "Year": "2026", "Genre": "Action, Drama", "Type": "Movie", "Desc": "Ram Charan & Janhvi Kapoor in a rugged action spectacle.", "LocalPoster": "/static/assets/hero/paddi-futclymrsd-landscape.avif"},
        {"Title": "The Call", "Language": "English", "Year": "2013", "Genre": "Thriller, Crime", "Type": "Movie", "Desc": "A high-stakes thriller where every second counts in a race against time.", "LocalPoster": "/static/assets/hero/the_call.webp"},
        {"Title": "Alpha", "Language": "Telugu", "Year": "2025", "Genre": "Action, Suspense", "Type": "Movie", "Desc": "Hemanth Kumar & Balu Nagendra in a gripping tale of survival and action.", "LocalPoster": "/static/assets/hero/alpha.webp"},
        {"Title": "Balls Up", "Language": "English", "Year": "2026", "Genre": "Comedy, Action", "Type": "Movie", "Desc": "A high-energy comedy spectacle that promises non-stop entertainment.", "LocalPoster": "/static/assets/hero/balls_up.webp"},
        {"Title": "Dacoit: A Love Story", "Language": "Telugu", "Year": "2026", "Genre": "Action, Romance", "Type": "Movie", "Desc": "Adivi Sesh & Mrunal Thakur in an intense action-romance saga.", "LocalPoster": "/static/assets/hero/Dacoit.webp"},
        {"Title": "Biker", "Language": "Telugu", "Year": "2026", "Genre": "Action, Sport", "Type": "Movie", "Desc": "Sharwanand & Rajasekhar in a high-octane motocross racing style.", "LocalPoster": "/static/assets/hero/Biker.avif"},
        {"Title": "Mercy", "Language": "English", "Year": "2026", "Genre": "Action, Sci-Fi", "Type": "Movie", "Desc": "Chris Pratt in a high-stakes sci-fi thriller set in the near future.", "LocalPoster": "/static/assets/hero/Mercy.webp"}
    ]
    
    ranked_hero = rec_engine.rank_hero_list(hero_movies)
    return {"results": ranked_hero}

@app.post("/api/update")
async def update_reward(update: RewardUpdate):
    rec_engine.load_model(update.uid)
    rec_engine.update(update.movie_link, update.reward)
    rec_engine.save_model(update.uid)
    return {"status": "success"}

@app.get("/api/search")
async def search(
    uid: str = "guest", 
    q: Optional[str] = None, 
    lang: Optional[str] = None, 
    genre: Optional[str] = None, 
    mtype: Optional[str] = None, 
    year: Optional[str] = None
):
    if rec_engine.movies_df.empty: return {"results": []}
    df = rec_engine.movies_df.copy()
    if q and q.strip():
        mask = df['Title'].str.contains(q, case=False, na=False) | \
               df['Hero'].str.contains(q, case=False, na=False) | \
               df['Heroin'].str.contains(q, case=False, na=False) | \
               df['Genre'].str.contains(q, case=False, na=False)
        df = df[mask]
    if lang and lang != "All": df = df[df['Language'].str.strip() == lang.strip()]
    if genre and genre != "All": df = df[df['Genre'].str.contains(genre, case=False, na=False)]
    if mtype and mtype != "All": df = df[df['Type'].str.strip() == mtype.strip()]
    if year and year != "All": df = df[df['Year'].astype(str).str.strip() == year.strip()]
    
    # Contextual Ranking
    rec_engine.load_model(uid)
    results = rec_engine.rank_custom_subset(df, n=200)
    return {"results": results}

METADATA_CACHE = {}

@app.get("/api/metadata")
async def get_metadata():
    global METADATA_CACHE
    if METADATA_CACHE:
        return METADATA_CACHE
        
    if rec_engine.movies_df.empty: 
        return {"languages": [], "genres": [], "types": [], "years": []}
        
    languages = ["All"] + sorted([l for l in rec_engine.movies_df['Language'].unique().tolist() if l != 'N/A'])
    genres_set = set()
    for g_str in rec_engine.movies_df['Genre']:
        if g_str != "N/A":
            parts = [p.strip() for p in str(g_str).split(",")]
            genres_set.update(parts)
    genres = ["All"] + sorted(list(genres_set))
    types = ["All"] + sorted([t for t in rec_engine.movies_df['Type'].unique().tolist() if t != 'N/A'])
    years = ["All"] + sorted([y for y in rec_engine.movies_df['Year'].unique().tolist() if y != 'N/A' and str(y) != 'nan'], reverse=True)
    
    METADATA_CACHE = {
        "languages": languages,
        "genres": genres,
        "types": types,
        "years": [str(y) for y in years]
    }
    return METADATA_CACHE

# --- WATCH PROGRESS ENDPOINTS ---
@app.post("/api/progress")
async def update_progress(data: ProgressUpdate):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.uid == data.uid).first()
        if not user: return {"status": "error", "message": "User not found"}
        
        existing = db.query(WatchProgress).filter(
            WatchProgress.user_id == user.id,
            WatchProgress.movie_id == data.movie_id
        ).first()
        
        if existing:
            existing.progress = data.progress
            existing.current_time = data.current_time
            existing.duration = data.duration
            existing.last_watched = datetime.utcnow()
        else:
            item = WatchProgress(
                user_id=user.id,
                movie_id=data.movie_id,
                title=data.title,
                image_link=data.image_link,
                progress=data.progress,
                current_time=data.current_time,
                duration=data.duration
            )
            db.add(item)
        
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@app.get("/api/progress")
async def get_progress(uid: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.uid == uid).first()
        if not user: return []
        progs = db.query(WatchProgress).filter(WatchProgress.user_id == user.id).order_by(WatchProgress.last_watched.desc()).all()
        return [
            {
                "movie_id": p.movie_id,
                "title": p.title,
                "image_link": p.image_link,
                "progress": p.progress,
                "current_time": p.current_time,
                "duration": p.duration,
                "last_watched": p.last_watched.isoformat()
            } for p in progs
        ]
    finally:
        db.close()

# --- OWNER API ENDPOINTS ---
@app.get("/api/owner/stats")
async def get_user_stats(uid: str):
    db = SessionLocal()
    try:
        owner = db.query(User).filter(User.uid == uid).first()
        if not owner or not owner.is_owner:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Mocking mood analysis stats
        total_users = db.query(User).count()
        mood_distribution = {
            "Action/Thriller": 45,
            "Romance/Drama": 25,
            "Comedy": 20,
            "Sci-Fi/Horror": 10
        }
        return {
            "total_users": total_users,
            "mood_distribution": mood_distribution,
            "active_now": 5,
            "recent_likes": 124
        }
    finally:
        db.close()

@app.get("/api/hd-poster")
async def get_hd_poster(title: str = None, tmdb_id: str = None):
    """Fetches HD poster from TMDB API (or falls back to scraping if no key)."""
    # 1. Try TMDB API if key is provided
    if TMDB_API_KEY and TMDB_API_KEY != "YOUR_TMDB_API_KEY_HERE":
        async with httpx.AsyncClient() as client:
            try:
                if tmdb_id:
                    url = f"{TMDB_BASE_URL}/movie/{tmdb_id}?api_key={TMDB_API_KEY}"
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("poster_path"):
                            return {"poster_url": f"{TMDB_IMG_URL}{data['poster_path']}", "source": "api"}
                if title:
                    url = f"{TMDB_BASE_URL}/search/movie?api_key={TMDB_API_KEY}&query={title}"
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        results = resp.json().get("results", [])
                        if results and results[0].get("poster_path"):
                            return {"poster_url": f"{TMDB_IMG_URL}{results[0]['poster_path']}", "source": "api"}
            except Exception as e:
                logging.error(f"TMDB API Error: {e}")

    # 2. Fallback to Scraping if API fails or no key
    if not title: return {"poster_url": None}
    try:
        search_url = f"https://www.themoviedb.org/search?query={title.replace(' ', '+')}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(search_url, timeout=10.0)
            match = re.search(r'src="(https://image\.tmdb\.org/t/p/w[0-9]+_and_h[0-9]+_bestv2/[^"]+\.(jpg|png|webp))"', resp.text)
            if match:
                return {"poster_url": match.group(1), "source": "scrape"}
            match = re.search(r'content="(https://image\.tmdb\.org/t/p/w[0-9]+/[^"]+\.(jpg|png|webp))"', resp.text)
            if match:
                return {"poster_url": match.group(1), "source": "scrape"}
        return {"poster_url": None}
    except Exception as e:
        return {"poster_url": None, "error": str(e)}

@app.post("/api/watchlist/toggle")
async def toggle_watchlist(data: dict = Body(...)):
    uid = data.get('uid')
    movie_data = data.get('movie_data')
    if not uid: return {"status": "error", "message": "Missing UID"}
    if not movie_data: return {"status": "error", "message": "Missing movie data"}
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.uid == uid).first()
        if not user: return {"status": "error", "message": f"User not found for UID: {uid}"}
        
        movie_link = movie_data.get('movie_link')
        if not movie_link: return {"status": "error", "message": "Missing movie_link in movie_data"}
        
        existing = db.query(Watchlist).filter(
            Watchlist.user_id == user.id, 
            Watchlist.movie_link == movie_link
        ).first()
        
        if existing:
            db.delete(existing)
            db.commit()
            return {"status": "removed"}
        else:
            item = Watchlist(
                user_id=user.id,
                movie_link=movie_link,
                title=movie_data.get('title', 'Unknown'),
                image_link=movie_data.get('image_link', '')
            )
            db.add(item)
            db.commit()
            return {"status": "added"}
    except Exception as e:
        logging.error(f"WATCHLIST ERROR: {e}", exc_info=True)
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@app.get("/api/watchlist")
async def get_watchlist(uid: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.uid == uid).first()
        if not user: return []
        return [
            {
                "Title": w.title, 
                "Movie Link": w.movie_link, 
                "Image Link": w.image_link,
                "Language": "N/A", "Year": "N/A" # Simplified for view
            } for w in user.watchlist
        ]
    finally:
        db.close()

@app.post("/api/owner/send_event")
async def send_event(uid: str, event_data: dict = Body(...)):
    db = SessionLocal()
    try:
        owner = db.query(User).filter(User.uid == uid).first()
        if not owner or not owner.is_owner:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # In a real app, this would send push notifications or emails
        print(f"!!! OWNER EVENT SENT: {event_data.get('title')}")
        return {"status": "success", "message": "Event information sent to all users"}
    finally:
        db.close()

@app.post("/api/owner/scrape_new")
async def scrape_new_movies(uid: str):
    db = SessionLocal()
    try:
        owner = db.query(User).filter(User.uid == uid).first()
        if not owner or not owner.is_owner:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        from scraper.incremental_updater import run_incremental_update
        
        # Run in background to avoid timeout
        thread = threading.Thread(target=run_incremental_update, args=(1,))
        thread.start()
        
        return {"status": "success", "message": "Scraper started in background. New movies will appear shortly."}
    finally:
        db.close()

@app.post("/api/owner/upgrade_hd")
async def upgrade_hd_posters(uid: str):
    db = SessionLocal()
    try:
        owner = db.query(User).filter(User.uid == uid).first()
        if not owner or not owner.is_owner:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        from scraper.update_csv_posters import run_hd_update
        
        # Run in background via a helper that creates a new event loop for the async function
        def run_async_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_hd_update())
            loop.close()

        thread = threading.Thread(target=run_async_in_thread)
        thread.start()
        
        return {"status": "success", "message": "HD Upgrade started! Finding posters on Google/TMDB..."}
    finally:
        db.close()

@app.get("/api/owner/low_res_movies")
async def get_low_res_movies(uid: str):
    db = SessionLocal()
    try:
        owner = db.query(User).filter(User.uid == uid).first()
        if not owner or not owner.is_owner:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        df = rec_engine.movies_df
        if df.empty: return {"results": [], "total": 0}
        
        # Find N/A or placeholder images
        mask = (df['Image Link'] == 'N/A') | (df['Image Link'] == '') | (df['Image Link'].isna())
        low_res = df[mask]
        
        return {
            "results": low_res.head(15).to_dict('records'), 
            "total": int(len(low_res))
        }
    finally:
        db.close()

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def index():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
