# VORTEX - Smart Movie Streaming Hub 🍿

VORTEX RL is a high-performance, metadata-rich movie streaming platform powered by Reinforcement Learning (RL) and AI recommendations. It features a cinematic UI, personalized swimlanes, and persistent watch history.

## 🚀 Key Features
- **AI Recommendation Engine**: Uses Contextual Bandits (RL) to learn your taste over time.
- **Cinematic Hero Carousel**: High-resolution backdrops and trending blockbusters.
- **Deduplication Layer**: Smart filtering ensures no repeated content or "twin" movies.
- **HD Image Upgrader**: Automatically fetches high-definition posters from TMDB for a premium look.
- **Watch Progress**: Persistent "Continue Watching" row synchronized via backend database.
- **Smart Filters**: Filter by Language, Genre, Year, and Quality.

## 🛠 Tech Stack
- **Backend**: FastAPI (Python), SQLAlchemy (SQLite), python-dotenv
- **Frontend**: Vanilla JavaScript (ES6+), Modern CSS (Flexbox/Grid)
- **Data**: TMDB API, optimized CSV dataset
- **Machine Learning**: NumPy, Scikit-learn (RL context)

## 📦 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/MovieRulz-RL-AI.git
   cd MovieRulz-RL-AI
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup Environment Variables**:
   Create a `.env` file in the root directory and add your TMDB API Key:
   ```env
   TMDB_API_KEY=your_api_key_here
   ```

4. **Run the Application**:
   ```bash
   python -m uvicorn main:app --reload
   ```
   Open `http://127.0.0.1:8000` in your browser.

## 🔧 Scraper & Tools
- `scraper/update_csv_posters.py`: Synchronizes the CSV dataset with TMDB metadata.
- `scraper/update_hero_images.py`: Fetches high-res backdrops for the hero section.

## 🛡 License
MIT License. Feel free to use and modify for educational purposes.

---
*Created with ❤️ for Movie Lovers.*
