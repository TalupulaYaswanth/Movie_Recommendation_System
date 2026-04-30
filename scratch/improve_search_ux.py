import os

# Using relative path for portability
file_path = os.path.join('static', 'script.js')

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update renderCategories to clear search input and update the view properly
old_render_categories_item = """        card.onclick = () => {
            const { genre: genreEl } = getFilterEls();
            if (genreEl) genreEl.value = genre;
            searchMovies(""); // Trigger search with new filter
        };"""

new_render_categories_item = """        card.onclick = () => {
            const { genre: genreEl } = getFilterEls();
            if (genreEl) genreEl.value = genre;
            // Clear search bar to avoid confusion when a category is selected
            if (searchInput) searchInput.value = "";
            searchMovies(""); // Trigger search with new filter
        };"""

if old_render_categories_item in content:
    content = content.replace(old_render_categories_item, new_render_categories_item)
    print("Updated renderCategories to clear search bar on click.")

# 2. Add a click listener to the search icon for a more intuitive UX
search_icon_listener = """
// Make the search icon clickable
const searchIcon = document.querySelector('.search-container i.fa-search');
if (searchIcon) {
    searchIcon.style.cursor = 'pointer';
    searchIcon.onclick = () => searchMovies(searchInput.value);
}
"""
if "searchIcon.onclick" not in content:
    content += search_icon_listener
    print("Added click listener to search icon.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
