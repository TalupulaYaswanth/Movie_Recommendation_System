import os

# Using relative path for portability
file_path = os.path.join('static', 'script.js')

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Update fetchTrending to add delay
trending_render_target = """        const data = await response.json();
        renderMovies(data.results, trendingGrid);"""

trending_render_replacement = """        const data = await response.json();
        setTimeout(() => {
            renderMovies(data.results, trendingGrid);
        }, 600);"""

# Update fetchWatchlist to add delay
watchlist_render_target = """        if (data.length === 0) {"""

watchlist_render_replacement = """        setTimeout(() => {
            if (data.length === 0) {"""

# And the closing brace for the setTimeout in watchlist
watchlist_closing_target = """            renderMovies(data, watchlistGrid, true);
        }
    } catch (err) {"""

watchlist_closing_replacement = """            renderMovies(data, watchlistGrid, true);
        }
        }, 600);
    } catch (err) {"""

if trending_render_target in content:
    content = content.replace(trending_render_target, trending_render_replacement)
    print("Added delay to fetchTrending")

if watchlist_render_target in content:
    content = content.replace(watchlist_render_target, watchlist_render_replacement)
    content = content.replace(watchlist_closing_target, watchlist_closing_replacement)
    print("Added delay to fetchWatchlist")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
