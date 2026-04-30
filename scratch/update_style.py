import os

# Using relative path for portability
file_path = os.path.join('static', 'style.css')

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

loader_css = """
/* --- Custom VORTEX Loader --- */
.loader-container {
    display: none; /* Hidden by default */
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 100px 20px;
    width: 100%;
    grid-column: 1 / -1;
    animation: fadeIn 0.5s ease;
}

.vortex-loader {
    width: 65px;
    height: 65px;
    border: 5px solid rgba(255, 255, 255, 0.05);
    border-top: 5px solid var(--accent-secondary);
    border-right: 5px solid var(--accent-primary);
    border-radius: 50%;
    animation: spin 0.8s cubic-bezier(0.4, 0, 0.2, 1) infinite;
    filter: drop-shadow(0 0 15px rgba(0, 212, 255, 0.4));
    margin-bottom: 25px;
    position: relative;
}

.vortex-loader::after {
    content: '';
    position: absolute;
    top: -5px;
    left: -5px;
    right: -5px;
    bottom: -5px;
    border-radius: 50%;
    border: 5px solid transparent;
    border-bottom: 5px solid var(--accent-secondary);
    opacity: 0.3;
    animation: spin 2s linear infinite reverse;
}

.loader-text {
    font-size: 1.1rem;
    font-weight: 700;
    background: var(--gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 2px;
    text-transform: uppercase;
    animation: loaderPulse 1.5s ease-in-out infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

@keyframes loaderPulse {
    0%, 100% { opacity: 0.6; transform: scale(0.98); }
    50% { opacity: 1; transform: scale(1); }
}

/* Fix for search grid when loading */
#searchGrid {
    min-height: 400px;
}
"""

if ".loader-container" not in content:
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(loader_css)
    print("Successfully added loader CSS to style.css")
else:
    print("Loader CSS already exists in style.css")
