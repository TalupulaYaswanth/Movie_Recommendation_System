import pandas as pd
import numpy as np
import os
import random
import threading

class MovieEngine:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.movies_df = pd.DataFrame()
        self.load_data()
        
        # RL Parameters
        self.alpha = 2.0  
        self.d = 0        
        self.A = None     
        self.b = None     
        self.feature_names = []
        self.movie_vectors = []
        self.current_user = None
        self.last_interactions = [] 
        
        # Concurrency Lock
        self.lock = threading.Lock()
        
        self.initialize_rl()
        self.load_model("guest")

    def load_data(self):
        try:
            if os.path.exists(self.data_path):
                self.movies_df = pd.read_csv(self.data_path)
                self.movies_df = self.movies_df.fillna("N/A")
                for col in ['Language', 'Type', 'Genre', 'Year']:
                    self.movies_df[col] = self.movies_df[col].astype(str).str.replace('\u00a0', ' ').str.strip()
                
                # --- DEDUPLICATION LAYER ---
                # 1. Clean titles to find duplicates (remove common suffixes)
                self.movies_df['_clean_title'] = self.movies_df['Title'].str.split('(', n=1).str[0].str.strip()
                self.movies_df['_clean_title'] = self.movies_df['_clean_title'].str.replace(r'\b(Telugu|Tamil|Hindi|Malayalam|Kannada|English)\b', '', regex=True, case=False)
                self.movies_df['_clean_title'] = self.movies_df['_clean_title'].str.replace(r'\b(Dubbed|Original|HD|UHD)\b', '', regex=True, case=False).str.strip()
                
                # 2. Drop duplicates, keeping the first (usually newest/best version)
                initial_count = len(self.movies_df)
                self.movies_df = self.movies_df.drop_duplicates(subset=['_clean_title'], keep='first')
                self.movies_df = self.movies_df.drop_duplicates(subset=['Movie Link'], keep='first')
                
                print(f"Engine: Loaded {len(self.movies_df)} unique movies (Removed {initial_count - len(self.movies_df)} duplicates).")
            else:
                print("Engine Warning: Dataset not found.")
        except Exception as e:
            print(f"Engine Load Error: {e}")
            self.movies_df = pd.DataFrame()

    def initialize_rl(self):
        if self.movies_df.empty: return
        
        # Feature Extraction Flow
        all_langs = sorted(self.movies_df['Language'].unique().tolist())
        all_types = sorted(self.movies_df['Type'].unique().tolist())
        
        decades = set()
        for y in self.movies_df['Year']:
            try: d = str(y)[:3] + "0s"
            except: d = "Unknown"
            decades.add(d)
        all_decades = sorted(list(decades))

        all_genres = set()
        for g_str in self.movies_df['Genre']:
            if g_str != "N/A":
                parts = [p.strip() for p in str(g_str).split(",")]
                all_genres.update(parts)
        all_genres = sorted(list(all_genres))
        
        self.feature_names = all_langs + all_genres + all_types + all_decades
        self.d = len(self.feature_names)
        self.reset_model()
        
        # Vectorization Flow
        self.movie_vectors = []
        for _, row in self.movies_df.iterrows():
            vec = np.zeros(self.d)
            ptr = 0
            if row['Language'] in all_langs: vec[all_langs.index(row['Language'])] = 1
            ptr += len(all_langs)
            if row['Genre'] != "N/A":
                for g in row['Genre'].split(","):
                    g = g.strip()
                    if g in all_genres: vec[ptr + all_genres.index(g)] = 1
            ptr += len(all_genres)
            if row['Type'] in all_types: vec[ptr + all_types.index(row['Type'])] = 1
            ptr += len(all_types)
            d_str = str(row['Year'])[:3] + "0s"
            if d_str in all_decades: vec[ptr + all_decades.index(d_str)] = 1
            
            norm = np.linalg.norm(vec)
            if norm > 0: vec = vec / norm
            self.movie_vectors.append(vec)
        self.movie_vectors = np.array(self.movie_vectors)

    def reset_model(self):
        self.A = np.identity(self.d)
        self.b = np.zeros((self.d, 1))
        self.last_interactions = []

    def save_model(self, uid: str):
        with self.lock:
            try:
                filename = f"models/user_{uid}_state.npz"
                os.makedirs("models", exist_ok=True)
                mood_arr = np.array(self.last_interactions) if self.last_interactions else np.array([])
                np.savez(filename, A=self.A, b=self.b, mood=mood_arr)
            except Exception as e:
                print(f"Save error for {uid}: {e}")

    def load_model(self, uid: str):
        if self.current_user == uid: return
        
        with self.lock:
            filename = f"models/user_{uid}_state.npz"
            self.reset_model()
            
            if os.path.exists(filename):
                try:
                    data = np.load(filename)
                    if data['A'].shape == self.A.shape:
                        self.A = data['A']
                        self.b = data['b']
                        if 'mood' in data and data['mood'].size > 0:
                            self.last_interactions = list(data['mood'])
                except Exception as e:
                    print(f"Load error for {uid}, resetting: {e}")
                    self.reset_model() # Fallback to fresh start
            
            self.current_user = uid

    def recommend(self, n=12, genre=None, lang=None, mtype=None):
        if self.movies_df.empty: return []
        
        with self.lock:
            try:
                # Subset filtering
                df = self.movies_df
                vectors = self.movie_vectors
                indices = np.arange(len(df))
                
                if genre and genre != "All":
                    mask = df['Genre'].str.contains(genre, case=False, na=False).values
                    indices = indices[mask]
                if lang and lang != "All":
                    mask = (df['Language'].str.strip() == lang.strip()).values
                    indices = indices[mask]
                if mtype and mtype != "All":
                    mask = (df['Type'].str.strip() == mtype.strip()).values
                    indices = indices[mask]
                
                if len(indices) == 0: return []
                
                subset_vectors = vectors[indices]
                subset_df = df.iloc[indices].copy()
                
                A_inv = np.linalg.inv(self.A)
                theta = A_inv @ self.b
                mood_boost = np.zeros(self.d)
                if self.last_interactions:
                    for v in self.last_interactions[-10:]: mood_boost += v * 0.4
                
                # Vectorized scoring
                # mean = x.T @ theta -> X @ theta
                # var = sqrt(x.T @ A_inv @ x) -> sqrt(diag(X @ A_inv @ X.T))
                means = (subset_vectors @ theta).flatten()
                variances = np.sqrt(np.sum((subset_vectors @ A_inv) * subset_vectors, axis=1))
                mood_factors = subset_vectors @ mood_boost
                
                scores = means + (self.alpha * variances) + mood_factors + np.random.uniform(0, 0.03, size=len(means))
                
                # Live priority boost
                live_mask = subset_df['Type'].str.strip().str.lower().isin(['live', 'sport', 'event']).values
                scores[live_mask] += 2.0
                    
                top_rel_indices = np.argsort(scores)[::-1][:n]
                return subset_df.iloc[top_rel_indices].to_dict('records')
            except Exception as e:
                print(f"Recommendation Error: {e}")
                import traceback
                traceback.print_exc()
                return self.movies_df.head(n).to_dict('records')

    def rank_custom_subset(self, df_subset, n=200):
        if df_subset.empty: return []
        with self.lock:
            try:
                A_inv = np.linalg.inv(self.A)
                theta = A_inv @ self.b
                
                # Align subset to vectors via indices
                indices = df_subset.index.tolist()
                subset_vectors = self.movie_vectors[indices]
                
                # Vectorized scoring
                means = (subset_vectors @ theta).flatten()
                variances = np.sqrt(np.sum((subset_vectors @ A_inv) * subset_vectors, axis=1))
                
                scores = means + (self.alpha * variances)
                
                # Apply Live boost in search too
                live_mask = df_subset['Type'].str.strip().str.lower().isin(['live', 'sport', 'event']).values
                scores[live_mask] += 2.0
                
                df_ranked = df_subset.copy()
                df_ranked['_score'] = scores
                df_ranked = df_ranked.sort_values(by='_score', ascending=False)
                return df_ranked.head(n).to_dict('records')
            except Exception as e:
                print(f"Ranking Error: {e}")
                return df_subset.head(n).to_dict('records')

    def seasonal_refresh(self):
        with self.lock:
            self.A = (self.A - np.identity(self.d)) * 0.5 + np.identity(self.d)
            self.b = self.b * 0.5
            self.last_interactions = []

    def update(self, movie_link, reward):
        with self.lock:
            matches = self.movies_df.index[self.movies_df['Movie Link'] == movie_link].tolist()
            if not matches: return
            idx = matches[0]
            x = self.movie_vectors[idx].reshape(-1, 1)
            self.A += x @ x.T
            self.b += reward * x
            if reward > 0:
                self.last_interactions.append(self.movie_vectors[idx])
                if len(self.last_interactions) > 20: self.last_interactions.pop(0)

    def rank_hero_list(self, hero_list):
        """Ranks a list of external movies (e.g. upcoming 2026 titles) using user vector."""
        if not hero_list: return []
        with self.lock:
            try:
                A_inv = np.linalg.inv(self.A)
                theta = A_inv @ self.b
                
                # Re-calculate extraction maps from existing data to ensure alignment
                all_langs = sorted(self.movies_df['Language'].unique().tolist())
                all_types = sorted(self.movies_df['Type'].unique().tolist())
                
                all_genres = set()
                for g_str in self.movies_df['Genre']:
                    if g_str != "N/A":
                        parts = [p.strip() for p in str(g_str).split(",")]
                        all_genres.update(parts)
                all_genres = sorted(list(all_genres))
                
                decades = set()
                for y in self.movies_df['Year']:
                    try: d = str(y)[:3] + "0s"
                    except: d = "Unknown"
                    decades.add(d)
                all_decades = sorted(list(decades))

                ranked_list = []
                for movie in hero_list:
                    vec = np.zeros(self.d)
                    ptr = 0
                    # Language
                    if movie.get('Language') in all_langs: 
                        vec[all_langs.index(movie['Language'])] = 1
                    ptr += len(all_langs)
                    
                    # Genre
                    genre_str = movie.get('Genre', 'N/A')
                    if genre_str != "N/A":
                        for g in genre_str.split(","):
                            g = g.strip()
                            if g in all_genres: vec[ptr + all_genres.index(g)] = 1
                    ptr += len(all_genres)
                    
                    # Type
                    m_type = movie.get('Type', 'Movie')
                    if m_type in all_types:
                        vec[ptr + all_types.index(m_type)] = 1
                    ptr += len(all_types)
                    
                    # Year/Decade
                    year = str(movie.get('Year', '2026'))
                    d_str = year[:3] + "0s"
                    if d_str in all_decades:
                        vec[ptr + all_decades.index(d_str)] = 1
                    
                    norm = np.linalg.norm(vec)
                    if norm > 0: vec = vec / norm
                    
                    x = vec.reshape(-1, 1)
                    score = (x.T @ theta)[0, 0] + (self.alpha * np.sqrt(x.T @ A_inv @ x)[0, 0])
                    movie['_score'] = float(score)
                    ranked_list.append(movie)
                
                return sorted(ranked_list, key=lambda x: x['_score'], reverse=True)
            except Exception as e:
                print(f"Hero Ranking Error: {e}")
                return hero_list
