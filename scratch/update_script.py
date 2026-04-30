import os

# Using relative path for portability
file_path = os.path.join('static', 'script.js')

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """    if (!query && lVal === 'All' && gVal === 'All' && tVal === 'All' && yVal === 'All') {
        showView('home');
        return;
    }"""

replacement = """    if (!query && lVal === 'All' && gVal === 'All' && tVal === 'All' && yVal === 'All') {
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
    `;"""

if target in content:
    new_content = content.replace(target, replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully updated script.js")
else:
    print("Target not found")
    # Debug: print a portion of the file
    start_index = content.find("async function searchMovies")
    if start_index != -1:
        print("Found searchMovies function. Content around it:")
        print(content[start_index:start_index+500])
