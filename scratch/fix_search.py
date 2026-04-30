import os

# Using relative path for portability
file_path = os.path.join('static', 'script.js')

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add a search controller to handle out-of-order requests
controller_decl = "let searchController = null;"
if controller_decl not in content:
    content = content.replace("let currentUID = localStorage.getItem('movieUID') || \"guest\";", 
                              f"let currentUID = localStorage.getItem('movieUID') || \"guest\";\n{controller_decl}")

# Update searchMovies to be more robust
old_search_movies = """async function searchMovies(query) {
    const { lang, genre, type, year } = getFilterEls();
    const lVal = lang ? lang.value : 'All';
    const gVal = genre ? genre.value : 'All';
    const tVal = type ? type.value : 'All';
    const yVal = year ? year.value : 'All';

    // Show search view if any filter or query is active
    if (!query && lVal === 'All' && gVal === 'All' && tVal === 'All' && yVal === 'All') {
        showView('home');
        return;
    }

    // Show Loader State
    showView('search');
    searchGrid.innerHTML = `
        <div class="loader-container" style="display: flex;">
            <div class="vortex-loader"></div>
            <div class="loader-text">Analyzing VORTEX Database...</div>
        </div>
    `;

    try {
        const params = new URLSearchParams({
            uid: currentUID,
            q: query || '',
            lang: lVal,
            genre: gVal,
            mtype: tVal,
            year: yVal
        });
        
        const response = await fetch(`/api/search?${params.toString()}`);
        const data = await response.json();
        
        // Slight delay to make the transition feel smoother and premium
        setTimeout(() => {
            renderMovies(data.results, searchGrid);
        }, 600);
        
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
        console.error("Search failed", err);
    }
}"""

new_search_movies = """async function searchMovies(query) {
    const { lang, genre, type, year } = getFilterEls();
    const lVal = lang ? lang.value : 'All';
    const gVal = genre ? genre.value : 'All';
    const tVal = type ? type.value : 'All';
    const yVal = year ? year.value : 'All';

    // If everything is 'All' and no query, go back to home
    if (!query && lVal === 'All' && gVal === 'All' && tVal === 'All' && yVal === 'All') {
        showView('home');
        return;
    }

    // Cancel any ongoing search to prevent race conditions
    if (searchController) searchController.abort();
    searchController = new AbortController();

    // Ensure search view is visible
    showView('search');
    
    // Show Premium Loader
    searchGrid.innerHTML = `
        <div class="loader-container" style="display: flex;">
            <div class="vortex-loader"></div>
            <div class="loader-text">Analyzing VORTEX Database...</div>
        </div>
    `;

    try {
        const params = new URLSearchParams({
            uid: currentUID,
            q: query || '',
            lang: lVal,
            genre: gVal,
            mtype: tVal,
            year: yVal
        });
        
        const response = await fetch(`/api/search?${params.toString()}`, {
            signal: searchController.signal
        });
        const data = await response.json();
        
        // We still keep a small delay but make it more robust
        setTimeout(() => {
            // Only render if this is still the active search
            if (!searchController.signal.aborted) {
                renderMovies(data.results, searchGrid);
            }
        }, 400); // Reduced slightly for better responsiveness
        
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
        if (err.name === 'AbortError') return; // Expected
        console.error("Search failed", err);
        searchGrid.innerHTML = '<p style="color: #ff4757; text-align: center; padding: 50px;">Search failed. Please check your connection.</p>';
    }
}"""

if old_search_movies in content:
    content = content.replace(old_search_movies, new_search_movies)
    print("Updated searchMovies with AbortController and better logic.")
else:
    # Fallback to a simpler replacement if whitespace differs
    print("Direct replacement failed, check script.js content.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
