import os

# Using relative path for portability
file_path = os.path.join('static', 'script.js')

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Update fetchTrending
trending_target = """async function fetchTrending() {
    trendingGrid.innerHTML = '<div class="shimmer" style="height: 300px; width: 100%; border-radius: 20px;"></div>';
    try {"""

trending_replacement = """async function fetchTrending() {
    trendingGrid.innerHTML = `
        <div class="loader-container" style="display: flex;">
            <div class="vortex-loader"></div>
            <div class="loader-text">Loading Trending Blockbusters...</div>
        </div>
    `;
    try {"""

# Update fetchWatchlist
watchlist_target = """async function fetchWatchlist() {
    try {"""

watchlist_replacement = """async function fetchWatchlist() {
    watchlistGrid.innerHTML = `
        <div class="loader-container" style="display: flex;">
            <div class="vortex-loader"></div>
            <div class="loader-text">Retrieving Your Watchlist...</div>
        </div>
    `;
    try {"""

if trending_target in content:
    content = content.replace(trending_target, trending_replacement)
    print("Updated fetchTrending")
else:
    print("Trending target not found")

if watchlist_target in content:
    content = content.replace(watchlist_target, watchlist_replacement)
    print("Updated fetchWatchlist")
else:
    print("Watchlist target not found")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
