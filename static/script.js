// --- FIREBASE INITIALIZATION ---
const firebaseConfig = {
  apiKey: "AIzaSyBV_6sZ-RYlhcVI6kpG-RdtCZr8tQ14tbU",
  authDomain: "movie-47dab.firebaseapp.com",
  projectId: "movie-47dab",
  storageBucket: "movie-47dab.appspot.com",
  messagingSenderId: "100234567890",
  appId: "1:100234567890:web:abcdef123456"
};

// --- PLAYER PROGRESS TRACKING ---
window.addEventListener("message", async (event) => {
    try {
        const payload = typeof event.data === "string" ? JSON.parse(event.data) : event.data;
        if (payload.type === "PLAYER_EVENT") {
            const data = payload.data;
            console.log("Player Update:", data);
            
            let posterUrl = "";
            try {
                // Fetch correct poster from TMDB API via our backend
                const posterRes = await fetch(`/api/hd-poster?tmdb_id=${data.id}`);
                const posterData = await posterRes.json();
                posterUrl = posterData.poster_url || "";
            } catch (err) {
                console.warn("Failed to fetch TMDB poster for player event", err);
            }

            // Only sync if user is logged in
            if (currentUID !== "guest") {
                await fetch('/api/progress', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        uid: currentUID,
                        movie_id: data.id,
                        title: data.title || ("Movie " + data.id),
                        image_link: posterUrl,
                        progress: data.progress,
                        current_time: data.currentTime,
                        duration: data.duration
                    })
                });
            }
            
            // Save to local storage for instant resume support
            const progressKey = `progress_${data.id}`;
            localStorage.setItem(progressKey, JSON.stringify({...data, posterUrl}));
        }
    } catch (e) {
        // Not a player event or JSON error
    }
});

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const provider = new firebase.auth.GoogleAuthProvider();

const recGrid = document.getElementById('recGrid');
const recActionGrid = document.getElementById('recActionGrid');
const recDramaGrid = document.getElementById('recDramaGrid');
const recTeluguGrid = document.getElementById('recTeluguGrid');
const recSportsGrid = document.getElementById('recSportsGrid');
const searchGrid = document.getElementById('searchGrid');
const searchInput = document.getElementById('searchInput');
const searchSection = document.getElementById('searchSection');
const toast = document.getElementById('toast');
const loginBtn = document.getElementById('loginBtn');
const signupBtn = document.getElementById('signupBtn');
const loginModal = document.getElementById('loginModal');
const closeLogin = document.getElementById('closeLogin');
const submitLogin = document.getElementById('submitLogin');
const userActions = document.getElementById('userActions');
const userProfile = document.getElementById('userProfile');
const logoutBtn = document.getElementById('logoutBtn');
const userNameDisplay = document.getElementById('userNameDisplay');
const navHome = document.getElementById('navHome');
const navTrending = document.getElementById('navTrending');
const navCategories = document.getElementById('navCategories');
const homeView = document.getElementById('homeView');
const trendingView = document.getElementById('trendingView');
const categoriesView = document.getElementById('categoriesView');
const trendingGrid = document.getElementById('trendingGrid');
const categoryGrid = document.getElementById('categoryGrid');
const heroSection = document.getElementById('heroSection');
const watchlistView = document.getElementById('watchlistView');
const watchlistGrid = document.getElementById('watchlistGrid');

let userWatchlist = new Set();

// Hero Elements
const heroTitle = document.getElementById('heroTitle');
const heroYear = document.getElementById('heroYear');
const heroType = document.getElementById('heroType');
const heroRating = document.getElementById('heroRating');
const heroSummary = document.getElementById('heroSummary');
const heroWatchBtn = document.getElementById('heroWatchBtn');
const heroWatchlistBtn = document.getElementById('heroWatchlistBtn');

// --- OWNER ELEMENTS ---
const ownerBadge = document.getElementById('ownerBadge');
const ownerAnalyzeBtn = document.getElementById('ownerAnalyzeBtn');
const ownerScrapeBtn = document.getElementById('ownerScrapeBtn');
const ownerHdBtn = document.getElementById('ownerHdBtn');
const ownerSendEventBtn = document.getElementById('ownerSendEventBtn');
const ownerModal = document.getElementById('ownerModal');
const ownerModalClose = document.getElementById('ownerModalClose');
const profileMenu = document.getElementById('profileMenu');

// Routing Logic
function showView(view) {
    
    [homeView, trendingView, categoriesView, searchSection, watchlistView].forEach(v => {
        if (v) v.style.display = 'none';
    });
    
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    
    if (view === 'home') {
        homeView.style.display = 'block';
        navHome.classList.add('active');
        heroSection.style.display = 'block';
    } else if (view === 'trending') {
        trendingView.style.display = 'block';
        navTrending.classList.add('active');
        heroSection.style.display = 'none';
        fetchTrending();
    } else if (view === 'categories') {
        categoriesView.style.display = 'block';
        navCategories.classList.add('active');
        heroSection.style.display = 'none';
    } else if (view === 'search') {
        searchSection.style.display = 'block';
        heroSection.style.display = 'none';
    } else if (view === 'watchlist') {
        watchlistView.style.display = 'block';
        heroSection.style.display = 'none';
        fetchWatchlist();
        document.getElementById('profileMenu').style.display = 'none';
    }
}

navHome.addEventListener('click', (e) => { e.preventDefault(); showView('home'); });
navTrending.addEventListener('click', (e) => { e.preventDefault(); showView('trending'); });
navCategories.addEventListener('click', (e) => { e.preventDefault(); showView('categories'); });

let currentUID = localStorage.getItem('movieUID') || "guest";

// Sync Auth with Backend
async function syncAuth(user) {
    try {
        const response = await fetch('/api/auth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                uid: user.uid,
                email: user.email,
                displayName: user.displayName || user.email.split('@')[0],
                photoURL: user.photoURL
            })
        });
        const data = await response.json();
        if (data.status === 'success') {
            currentUID = user.uid;
            localStorage.setItem('movieUID', currentUID);
            // Store owner status
            localStorage.setItem('isOwner', data.is_owner);
            return data;
        }
    } catch (err) {
        console.error("Auth sync failed", err);
        showToast("Sync Error: Backend not responding. ⚠️");
    }
    return null;
}

const toggleMode = document.getElementById('toggleMode');
const modalTitle = document.getElementById('modalTitle');
const modalSub = document.getElementById('modalSub');
const emailGroup = document.getElementById('emailGroup');
const toggleText = document.getElementById('toggleText');
let isLoginMode = true;

const modalCloseX = document.getElementById('modalCloseX');

// Modal Logic
function openAuthModal(mode) {
    isLoginMode = mode === 'login';
    updateModalUI();
    loginModal.style.display = 'flex';
}

function updateModalUI() {
    if (isLoginMode) {
        modalTitle.innerText = "Login";
        modalSub.innerText = "Welcome back to MovieRulz AI";
        emailGroup.style.display = 'none';
        submitLogin.innerText = "Log In";
        toggleText.innerText = "Don't have an account?";
        toggleMode.innerText = "Sign Up";
    } else {
        modalTitle.innerText = "Create Account";
        modalSub.innerText = "Join to train your personal AI model";
        emailGroup.style.display = 'block';
        submitLogin.innerText = "Create Account";
        toggleText.innerText = "Already have an account?";
        toggleMode.innerText = "Log In";
    }
}

loginBtn.addEventListener('click', () => openAuthModal('login'));
signupBtn.addEventListener('click', () => openAuthModal('signup'));
closeLogin.addEventListener('click', () => loginModal.style.display = 'none');
modalCloseX.addEventListener('click', () => loginModal.style.display = 'none');

// Add hover effect via JS for the X
modalCloseX.onmouseover = () => modalCloseX.style.color = '#ff4757';
modalCloseX.onmouseout = () => modalCloseX.style.color = 'var(--text-dim)';

const googleLoginBtn = document.getElementById('googleLoginBtn');

googleLoginBtn.addEventListener('click', async () => {
    try {
        const result = await auth.signInWithPopup(provider);
        const user = result.user;
        
        const success = await syncAuth(user);
        if (success) {
            loginModal.style.display = 'none';
            updateUserUI(user, success.is_owner);
            
            if (success.refreshed) {
                showToast("AI Model Refreshed for the new season! 🌟");
            } else {
                showToast("Signed in with Google! 🌍✨");
            }
            fetchRecommendations();
            updateHero();
        }
    } catch (error) {
        console.error("Google Login Error", error);
        showToast(`Login failed: ${error.message || "Please try again."}`);
    }
});

function updateUserUI(user, isOwner = false) {
    if (user) {
        loginModal.style.display = 'none'; // Auto-close modal on successful login
        userActions.style.display = 'none';
        userProfile.style.display = 'flex';
        userNameDisplay.innerText = user.displayName || user.email.split('@')[0];
        document.getElementById('menuUserEmail').innerText = user.email || "";
        
        // Owner Specific UI
        
        if (isOwner || localStorage.getItem('isOwner') === 'true') {
            ownerBadge.style.display = 'inline-block';
            ownerAnalyzeBtn.style.display = 'flex';
            ownerScrapeBtn.style.display = 'flex';
            ownerHdBtn.style.display = 'flex';
            ownerSendEventBtn.style.display = 'flex';
        } else {
            ownerBadge.style.display = 'none';
            ownerAnalyzeBtn.style.display = 'none';
            ownerScrapeBtn.style.display = 'none';
            ownerHdBtn.style.display = 'none';
            ownerSendEventBtn.style.display = 'none';
        }
    } else {
        userActions.style.display = 'flex';
        userProfile.style.display = 'none';
        localStorage.removeItem('isOwner');
    }
}

// Persist Login State
auth.onAuthStateChanged(async (user) => {
    if (user) {
        currentUID = user.uid;
        localStorage.setItem('movieUID', currentUID);
        const data = await syncAuth(user);
        updateUserUI(user, data ? data.is_owner : false);
        await updateWatchlistSet(); // Sync watchlist before fetching recs
        fetchRecommendations();
        updateHero();
    } else {
        currentUID = "guest";
        localStorage.removeItem('movieUID');
        localStorage.removeItem('isOwner');
        userWatchlist.clear();
        updateUserUI(null);
        fetchRecommendations();
        updateHero();
    }
});

async function updateWatchlistSet() {
    if (currentUID === "guest") {
        userWatchlist.clear();
        return;
    }
    try {
        const response = await fetch(`/api/watchlist?uid=${encodeURIComponent(currentUID)}`);
        const data = await response.json();
        userWatchlist = new Set(data.map(m => m['Movie Link']));
        console.log("Watchlist synced:", userWatchlist.size, "items");
    } catch (err) {
        console.error("Failed to update watchlist set", err);
    }
}

toggleMode.addEventListener('click', (e) => {
    e.preventDefault();
    isLoginMode = !isLoginMode;
    updateModalUI();
});

submitLogin.addEventListener('click', async () => {
    const username = document.getElementById('usernameInput').value;
    const email = document.getElementById('emailInput').value || `${username}@example.com`;
    
    if (username) {
        const dummyUser = {
            uid: "user_" + username.toLowerCase().replace(/\s/g, '_'),
            email: email,
            displayName: username,
            photoURL: ""
        };

        const success = await syncAuth(dummyUser);
        if (success) {
            loginModal.style.display = 'none';
            updateUserUI(dummyUser, success.is_owner);
            
            if (success.refreshed) {
                showToast("AI Model Refreshed for the new season! 🌟");
            } else {
                showToast(isLoginMode ? `Welcome back, ${username}! ✨` : `Account created for ${username}! 🚀`);
            }
            fetchRecommendations(); 
        }
    }
});

logoutBtn.addEventListener('click', () => {
    auth.signOut().then(() => {
        document.getElementById('profileMenu').style.display = 'none';
        showToast("Logged out. Using Guest profile.");
    }).catch((error) => {
        console.error("Logout Error", error);
    });
});

// --- PROFILE & OWNER LOGIC ---
const userTrigger = document.getElementById('userTrigger');

userTrigger.addEventListener('click', (e) => {
    e.stopPropagation();
    profileMenu.style.display = profileMenu.style.display === 'block' ? 'none' : 'block';
});

document.addEventListener('click', () => {
    profileMenu.style.display = 'none';
});

profileMenu.addEventListener('click', (e) => e.stopPropagation());

ownerModalClose.onclick = () => ownerModal.style.display = 'none';

ownerAnalyzeBtn.onclick = async () => {
    profileMenu.style.display = 'none';
    ownerModal.style.display = 'flex';
    document.getElementById('ownerModalTitle').innerText = "User Mood Analysis";
    document.getElementById('moodAnalysisView').style.display = 'block';
    document.getElementById('sendEventView').style.display = 'none';
    
    // Fetch stats
    try {
        const response = await fetch(`/api/owner/stats?uid=${encodeURIComponent(currentUID)}`);
        const data = await response.json();
        
        document.getElementById('statTotalUsers').innerText = data.total_users;
        document.getElementById('statActiveNow').innerText = data.active_now;
        
        const moodChart = document.getElementById('moodChart');
        moodChart.innerHTML = '';
        
        Object.entries(data.mood_distribution).forEach(([mood, percent]) => {
            const item = document.createElement('div');
            item.innerHTML = `
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                    <span>${mood}</span>
                    <span>${percent}%</span>
                </div>
                <div class="mood-bar-container">
                    <div class="mood-bar" style="width: ${percent}%"></div>
                </div>
            `;
            moodChart.appendChild(item);
        });
    } catch (err) {
        showToast("Failed to fetch stats.");
    }
};

ownerSendEventBtn.onclick = () => {
    profileMenu.style.display = 'none';
    ownerModal.style.display = 'flex';
    document.getElementById('ownerModalTitle').innerText = "Send New Release Event";
    document.getElementById('moodAnalysisView').style.display = 'none';
    document.getElementById('sendEventView').style.display = 'block';
};

ownerScrapeBtn.onclick = async () => {
    profileMenu.style.display = 'none';
    showToast("Starting background scraper... ⏳");
    try {
        const response = await fetch(`/api/owner/scrape_new?uid=${encodeURIComponent(currentUID)}`, { method: 'POST' });
        const data = await response.json();
        showToast(data.message || data.detail || "Scraper started!");
    } catch (err) {
        showToast("Failed to start scraper.");
    }
};

ownerHdBtn.onclick = async () => {
    profileMenu.style.display = 'none';
    ownerModal.style.display = 'flex';
    document.getElementById('ownerModalTitle').innerText = "HD Poster Upgrade Queue";
    document.getElementById('moodAnalysisView').style.display = 'none';
    document.getElementById('sendEventView').style.display = 'none';
    document.getElementById('hdUpgradeView').style.display = 'block';
    
    await refreshLowResTable();
};

async function refreshLowResTable() {
    const tableBody = document.getElementById('lowResTableBody');
    tableBody.innerHTML = '<tr><td colspan="3" style="padding: 20px; text-align: center;">Scanning database...</td></tr>';
    
    try {
        const response = await fetch(`/api/owner/low_res_movies?uid=${encodeURIComponent(currentUID)}`);
        const data = await response.json();
        
        const countEl = document.getElementById('lowResCount');
        if (countEl) countEl.innerText = `${data.total} items pending upgrade`;
        
        tableBody.innerHTML = '';
        if (!data.results || data.results.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="3" style="padding: 20px; text-align: center; color: var(--accent-secondary);">All posters are HD! 🏆</td></tr>';
            return;
        }
        
        data.results.forEach(movie => {
            const row = document.createElement('tr');
            row.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
            row.innerHTML = `
                <td style="padding: 12px; font-weight: 600;">${movie.Title}</td>
                <td style="padding: 12px; color: var(--text-dim);">${movie.Language}</td>
                <td style="padding: 12px;"><span style="color: #ff4757; font-size: 0.75rem;">● Missing HD</span></td>
            `;
            tableBody.appendChild(row);
        });
    } catch (err) {
        console.error("Queue fetch error", err);
        tableBody.innerHTML = '<tr><td colspan="3" style="padding: 20px; text-align: center; color: #ff4757;">Failed to load queue.</td></tr>';
    }
}

const triggerHdSyncBtn = document.getElementById('triggerHdSyncBtn');
if (triggerHdSyncBtn) {
    triggerHdSyncBtn.onclick = async () => {
        showToast("Starting TMDB Sync... 🚀");
        try {
            const response = await fetch(`/api/owner/upgrade_hd?uid=${encodeURIComponent(currentUID)}`, { method: 'POST' });
            const data = await response.json();
            showToast(data.message || "Sync started!");
            // Refresh the list after a delay to show progress
            setTimeout(refreshLowResTable, 5000);
        } catch (err) {
            showToast("Sync failed.");
        }
    };
}

document.getElementById('broadcastEventBtn').onclick = async () => {
    const title = document.getElementById('eventTitle').value;
    const date = document.getElementById('eventDate').value;
    const desc = document.getElementById('eventDesc').value;
    
    if (!title || !date) return showToast("Please fill title and date!");
    
    try {
        const response = await fetch(`/api/owner/send_event?uid=${encodeURIComponent(currentUID)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, date, desc })
        });
        if (response.ok) {
            showToast("Event Broadcasted Successfully! 📣");
            ownerModal.style.display = 'none';
        }
    } catch (err) {
        showToast("Broadcast failed.");
    }
};

function setQuickFilter(type, value) {
    const { lang, genre } = getFilterEls();
    if (type === 'Language' && lang) lang.value = value;
    if (type === 'Genre' && genre) genre.value = value;
    profileMenu.style.display = 'none';
    searchMovies("");
}

function initSliderControls(trackId) {
    const track = document.getElementById(trackId);
    const prevBtn = document.getElementById(`btn-prev-${trackId}`);
    const nextBtn = document.getElementById(`btn-next-${trackId}`);
    
    if (!track || !prevBtn || !nextBtn) return;
    
    const updateButtons = () => {
        const scrollLeft = track.scrollLeft;
        const maxScroll = track.scrollWidth - track.clientWidth;
        
        // Use a small buffer for precision
        if (scrollLeft <= 10) {
            prevBtn.classList.add('disabled');
        } else {
            prevBtn.classList.remove('disabled');
        }
        
        if (scrollLeft >= maxScroll - 10) {
            nextBtn.classList.add('disabled');
        } else {
            nextBtn.classList.remove('disabled');
        }
    };
    
    nextBtn.onclick = () => {
        const amount = track.clientWidth * 0.8;
        track.scrollBy({ left: amount, behavior: 'smooth' });
    };
    
    prevBtn.onclick = () => {
        const amount = track.clientWidth * 0.8;
        track.scrollBy({ left: -amount, behavior: 'smooth' });
    };
    
    track.onscroll = updateButtons;
    // Delay initial check to ensure layout is ready
    setTimeout(updateButtons, 600);
}

async function fetchRecommendations(isMoodShift = false) {
    try {
        const uid = encodeURIComponent(currentUID);
        const seenMovieLinks = new Set(); // TRACKER: Ensure no movie repeats on the entire page
        
        // Reset swimlanes
        ['recGrid', 'recActionGrid', 'recDramaGrid', 'recTeluguGrid', 'latestGrid'].forEach(id => {
            const el = document.getElementById(id);
            if (el && isMoodShift) {
                el.classList.remove('grid-refresh');
                void el.offsetWidth; // Trigger reflow
                el.classList.add('grid-refresh');
            }
        });

        // Reset visibility for categorized segments
        ['latestMoviesSection', 'recActionSection', 'recDramaSection', 'recTeluguSection', 'recSportsSection', 'continueWatchingSection'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
        
        // 1. General Recommendations (Top Priority)
        const resGen = await fetch(`/api/recommend?uid=${uid}&n=20`);
        const dataGen = await resGen.json();
        const filteredGen = dataGen.results.filter(m => {
            if (seenMovieLinks.has(m['Movie Link'])) return false;
            seenMovieLinks.add(m['Movie Link']);
            return true;
        });
        renderMovies(filteredGen, recGrid);

        // 1.5 Latest Movies Swimlane (2026)
        const resLatest = await fetch(`/api/search?uid=${uid}&year=2026`);
        const dataLatest = await resLatest.json();
        const filteredLatest = dataLatest.results.filter(m => {
            if (seenMovieLinks.has(m['Movie Link'])) return false;
            seenMovieLinks.add(m['Movie Link']);
            return true;
        });
        if (filteredLatest.length > 0) {
            document.getElementById('latestMoviesSection').style.display = 'block';
            renderMovies(filteredLatest, document.getElementById('latestGrid'));
            initSliderControls('latestGrid');
        }

        // 2. Action Swimlane
        const resAction = await fetch(`/api/recommend?uid=${uid}&n=30&genre=Action`);
        const dataAction = await resAction.json();
        const filteredAction = dataAction.results.filter(m => {
            if (seenMovieLinks.has(m['Movie Link'])) return false;
            seenMovieLinks.add(m['Movie Link']);
            return true;
        });
        if (filteredAction.length > 0) {
            document.getElementById('recActionSection').style.display = 'block';
            renderMovies(filteredAction, recActionGrid);
            initSliderControls('recActionGrid');
        }

        // 3. Drama Swimlane
        const resDrama = await fetch(`/api/recommend?uid=${uid}&n=30&genre=Drama`);
        const dataDrama = await resDrama.json();
        const filteredDrama = dataDrama.results.filter(m => {
            if (seenMovieLinks.has(m['Movie Link'])) return false;
            seenMovieLinks.add(m['Movie Link']);
            return true;
        });
        if (filteredDrama.length > 0) {
            document.getElementById('recDramaSection').style.display = 'block';
            renderMovies(filteredDrama, recDramaGrid);
            initSliderControls('recDramaGrid');
        }

        // 4. Telugu Swimlane
        const resTelugu = await fetch(`/api/recommend?uid=${uid}&n=30&lang=Telugu`);
        const dataTelugu = await resTelugu.json();
        const filteredTelugu = dataTelugu.results.filter(m => {
            if (seenMovieLinks.has(m['Movie Link'])) return false;
            seenMovieLinks.add(m['Movie Link']);
            return true;
        });
        if (filteredTelugu.length > 0) {
            document.getElementById('recTeluguSection').style.display = 'block';
            renderMovies(filteredTelugu, recTeluguGrid);
            initSliderControls('recTeluguGrid');
        }

        // 5. Sports Swimlane
        const resSports = await fetch(`/api/recommend?uid=${uid}&n=20&mtype=Sport`);
        const dataSports = await resSports.json();
        const filteredSports = (dataSports.results || []).filter(m => {
            if (seenMovieLinks.has(m['Movie Link'])) return false;
            seenMovieLinks.add(m['Movie Link']);
            return true;
        });
        if (filteredSports.length > 0) {
            document.getElementById('recSportsSection').style.display = 'block';
            renderMovies(filteredSports, recSportsGrid);
        }

        // 6. Continue Watching (Excluded from global seen filter to allow resume)
        if (currentUID !== "guest") {
            const resProg = await fetch(`/api/progress?uid=${uid}`);
            const dataProg = await resProg.json();
            if (dataProg.length > 0) {
                document.getElementById('continueWatchingSection').style.display = 'block';
                renderContinueWatching(dataProg);
            }
        }
    } catch (err) {
        console.error("Failed to fetch recommendations", err);
    }
}

function renderContinueWatching(items) {
    const grid = document.getElementById('continueWatchingGrid');
    grid.innerHTML = '';
    items.forEach(item => {
        const card = document.createElement('div');
        card.className = 'movie-card continue-card';
        card.innerHTML = `
            <div class="poster-container" onclick="resumeMovie('${item.movie_id}', ${item.current_time})">
                <img src="${item.image_link || 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=400&q=80'}" alt="${item.title}">
                <div class="progress-overlay">
                    <div class="progress-bar-inner" style="width: ${item.progress}%"></div>
                </div>
                <div class="play-overlay"><i class="fas fa-play"></i></div>
            </div>
            <div class="movie-info">
                <h3>${item.title}</h3>
                <p style="font-size: 0.75rem; color: var(--accent-secondary)">${Math.round(item.progress)}% Watched</p>
            </div>
        `;
        grid.appendChild(card);
    });
    initSliderControls('continueWatchingGrid');
}

function resumeMovie(id, time) {
    showToast(`Resuming from ${Math.floor(time / 60)}m ${Math.floor(time % 60)}s...`);
    // Logic to open player with timestamp would go here
    // For now, search for it
    window.open(`https://www.google.com/search?q=${id} movie watch online`, '_blank');
}

// Hero Slider Logic
let heroSlides = [];
let currentSlideIndex = 0;
let heroInterval = null;

async function updateHero() {
    await initHeroSlider();
}

async function initHeroSlider() {
    try {
        const response = await fetch(`/api/recommend/hero?uid=${encodeURIComponent(currentUID)}`);
        const data = await response.json();
        heroSlides = data.results;
        
        if (heroSlides && heroSlides.length > 0) {
            currentSlideIndex = 0;
            displayHeroSlide(heroSlides[currentSlideIndex]);
            
            if (heroInterval) clearInterval(heroInterval);
            heroInterval = setInterval(() => {
                currentSlideIndex = (currentSlideIndex + 1) % heroSlides.length;
                displayHeroSlide(heroSlides[currentSlideIndex]);
            }, 30000);
        }
    } catch (err) {
        console.error("Hero Slider Error", err);
    }
}

async function displayHeroSlide(movie) {
    if (!movie) return;
    
    // Smooth text update
    heroTitle.style.opacity = 0;
    setTimeout(() => {
        heroTitle.innerText = movie.Title;
        heroYear.innerText = movie.Year;
        heroType.innerText = movie.Type;
        
        const confidence = (9.5 + Math.random() * 0.4).toFixed(1);
        if (typeof heroRating !== 'undefined') heroRating.innerText = `AI ${confidence}`;
        
        heroSummary.innerText = movie.Desc || "Featured Blockbuster";
        heroTitle.style.opacity = 1;
    }, 500);

    // Fetch Cinematic Backdrop or use Local Asset
    try {
        let backdropUrl = movie.LocalPoster;
        if (!backdropUrl) {
            const backdropRes = await fetch(`/api/hd-poster?title=${encodeURIComponent(movie.Title + ' official movie backdrop wallpaper')}`);
            const backdropData = await backdropRes.json();
            backdropUrl = backdropData.poster_url || 'https://images.unsplash.com/photo-1626814026160-2237a95fc5a0?q=80&w=2070&auto=format&fit=crop';
        }
        
        heroSection.style.backgroundImage = `linear-gradient(to right, rgba(5, 7, 10, 0.7) 10%, rgba(5, 7, 10, 0.2) 40%, transparent), url('${backdropUrl}')`;
    } catch (e) {
        console.warn("Hero Backdrop failed", e);
    }

    // Update button listeners
    heroWatchBtn.onclick = (e) => {
        if (movie.Year === '2026') {
            showToast(`"${movie.Title}" is not yet released! Coming in ${movie.Year}. 📅`);
            // AI feedback removed for unreleased films as per request
        } else {
            window.open(`https://www.google.com/search?q=${encodeURIComponent(movie.Title + ' movie watch online')}`, '_blank');
            sendFeedback('Hero-' + movie.Title, 1.0, e); 
        }
    };
    
    heroWatchlistBtn.onclick = (e) => {
        toggleWatchlist('Featured-' + movie.Title, movie.Title, '', heroWatchlistBtn, e);
        if (movie.Year !== '2026') {
            sendFeedback('Hero-' + movie.Title, 0.5, e);
        }
    };
}

// Old updateHero placeholder (removed)
async function _oldUpdateHero() {
    try {
        const response = await fetch(`/api/recommend?uid=${encodeURIComponent(currentUID)}&n=5`);
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
            const movie = data.results[0];
            
            heroTitle.innerText = movie.Title;
            heroYear.innerText = movie.Year !== 'N/A' ? movie.Year : '2024';
            heroType.innerText = movie.Type !== 'N/A' ? movie.Type : 'Movie';
            
            // Artificial AI confidence score for UI effect
            const confidence = (9.0 + Math.random()).toFixed(1);
            heroRating.innerText = `AI ${confidence}`;
            
            heroSummary.innerText = `Experience this trending ${movie.Language} ${movie.Type.toLowerCase()} in high quality. Our AI predicts this matches your current mood perfectly based on your interaction history.`;
            
            // Set Background
            let posterUrl = movie['Image Link'];
            if (posterUrl && posterUrl !== 'N/A') {
                heroSection.style.backgroundImage = `url('${posterUrl}')`;
            }

            // RL Listeners
            heroWatchBtn.onclick = () => {
                watchMovie(movie['Movie Link']);
                sendFeedback(movie['Movie Link'], 1.0); // High Reward
            };

            const isSaved = userWatchlist.has(movie['Movie Link']);
            heroWatchlistBtn.innerHTML = isSaved ? '<i class="fas fa-check"></i>' : '<i class="fas fa-plus"></i>';
            heroWatchlistBtn.onclick = (e) => {
                toggleWatchlist(movie['Movie Link'], movie.Title, movie['Image Link'], null, e);
                sendFeedback(movie['Movie Link'], 0.5); // Moderate Reward
                heroWatchlistBtn.innerHTML = '<i class="fas fa-check"></i>';
            };
        }
    } catch (err) {
        console.error("Hero update failed", err);
    }
}

async function fetchTrending() {
    trendingGrid.innerHTML = '<div class="shimmer" style="height: 300px; width: 100%; border-radius: 20px;"></div>';
    try {
        const response = await fetch('/api/trending');
        const data = await response.json();
        renderMovies(data.results, trendingGrid);
    } catch (err) {
        console.error("Failed to fetch trending", err);
    }
}

const getFilterEls = () => ({
    lang: document.getElementById('langFilter'),
    genre: document.getElementById('genreFilter'),
    type: document.getElementById('typeFilter'),
    year: document.getElementById('yearFilter'),
    apply: document.getElementById('applyFilters')
});

// Fetch Metadata (Filters)
async function fetchMetadata() {
    try {
        const response = await fetch('/api/metadata');
        const data = await response.json();
        
        const { lang, genre, type, year } = getFilterEls();
        console.log("Metadata fetched:", data);
        
        if (lang) populateDropdown(lang, data.languages);
        if (genre) populateDropdown(genre, data.genres);
        if (type) populateDropdown(type, data.types);
        if (year) populateDropdown(year, data.years);
        
        // Add listeners for instant filtering
        [lang, genre, type, year].forEach(el => {
            if (el) {
                el.onchange = () => searchMovies(searchInput.value);
            }
        });
        
        renderCategories(data.genres);
    } catch (err) {
        console.error("Failed to fetch metadata", err);
    }
}

function renderCategories(genres) {
    categoryGrid.innerHTML = '';
    const icons = {
        'Action': 'fa-bolt', 'Comedy': 'fa-face-laugh', 'Drama': 'fa-masks-theater',
        'Horror': 'fa-ghost', 'Romance': 'fa-heart', 'Sci-Fi': 'fa-rocket',
        'Thriller': 'fa-user-ninja', 'Crime': 'fa-handcuffs', 'Animation': 'fa-palette'
    };

    genres.forEach(genre => {
        if (genre === 'All') return;
        const card = document.createElement('div');
        card.className = 'category-card';
        const icon = icons[genre] || 'fa-film';
        card.innerHTML = `
            <i class="fas ${icon}"></i>
            <h3>${genre}</h3>
        `;
        card.onclick = () => {
            const { genre: genreEl } = getFilterEls();
            if (genreEl) genreEl.value = genre;
            searchMovies(""); // Trigger search with new filter
        };
        categoryGrid.appendChild(card);
    });
}

function populateDropdown(dropdown, items) {
    console.log(`Populating ${dropdown.id} with ${items.length} items`);
    dropdown.innerHTML = '';
    items.forEach(item => {
        const option = document.createElement('option');
        option.value = item;
        let label = item;
        if (item === 'All') {
            const type = dropdown.id.replace('Filter', '');
            label = `All ${type.charAt(0).toUpperCase() + type.slice(1)}s`;
        }
        option.textContent = label;
        dropdown.appendChild(option);
    });
}

async function searchMovies(query) {
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
        
        showView('search'); // Switch to full-page search mode
        renderMovies(data.results, searchGrid);
        
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
        console.error("Search failed", err);
    }
}

document.addEventListener('click', (e) => {
    if (e.target.id === 'applyFilters') {
        profileMenu.style.display = 'none';
        searchMovies(searchInput.value);
    }
});

// Initial load removed here, moved to end

function renderMovies(movies, container, isWatchlist = false) {
    container.innerHTML = '';
    if (!movies || movies.length === 0) {
        container.innerHTML = '<p style="color: var(--text-dim)">No movies found.</p>';
        return;
    }

    const escapeJS = (str) => {
        if (!str) return "";
        return str.replace(/\\/g, "\\\\").replace(/'/g, "\\'");
    };

    movies.forEach(async (movie) => {
        const card = document.createElement('div');
        card.className = 'movie-card';
        
        // Default placeholder or original link
        let posterUrl = movie['Image Link'] && movie['Image Link'] !== 'N/A' 
            ? movie['Image Link'] 
            : 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=400&q=80';

        // Apply Weserv.nl sharpening
        const optimizedUrl = `https://images.weserv.nl/?url=${encodeURIComponent(posterUrl)}&w=400&h=600&fit=cover&sharp=5&errorredirect=https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=400&q=80`;

        const isActuallySaved = isWatchlist || userWatchlist.has(movie['Movie Link']);
        const isLive = movie.Type && movie.Type.toLowerCase().trim() === 'sport';
        const safeTitle = escapeJS(movie.Title);
        const safeMovieLink = escapeJS(movie['Movie Link']);

        card.innerHTML = `
            <div class="poster-container" onclick="watchMovie('${safeMovieLink}', event)">
                <img id="img-${safeTitle.replace(/\s+/g, '-')}" src="${optimizedUrl}" alt="${safeTitle}" onerror="globalImageFallback(this)">
                <div class="badge ${isLive ? 'badge-live' : ''}">${isLive ? 'LIVE' : (movie.Quality || 'HD')}</div>
                <div class="hd-indicator" style="display: none;"><i class="fas fa-check-circle"></i> HD+</div>
            </div>
            <div class="movie-info">
                <h3 onclick="watchMovie('${safeMovieLink}', event)" style="cursor: pointer;">${movie.Title}</h3>
                <div class="meta">
                    <span>${movie.Language}</span>
                    <span>${movie.Year !== 'N/A' ? movie.Year : ''}</span>
                </div>
                <p style="font-size: 0.8rem; color: var(--text-dim); margin-bottom: 10px;">
                    ${movie.Genre && movie.Genre !== 'N/A' ? movie.Genre : 'Drama'}
                </p>
                <div class="actions">
                    <button class="btn btn-save ${isActuallySaved ? 'saved' : ''}" onclick="toggleWatchlist('${safeMovieLink}', '${safeTitle}', '${posterUrl}', this, event)" title="Save for later">
                        <i class="fas fa-bookmark"></i>
                    </button>
                    <button class="btn btn-like" onclick="sendFeedback('${safeMovieLink}', 1.0, event)">
                        <i class="fas fa-thumbs-up"></i>
                    </button>
                    <button class="btn btn-dislike" onclick="sendFeedback('${safeMovieLink}', -1.0, event)">
                        <i class="fas fa-thumbs-down"></i>
                    </button>
                    <button class="btn btn-play" onclick="watchMovie('${safeMovieLink}', event)">
                        Play
                    </button>
                </div>
            </div>
        `;
        container.appendChild(card);

        // BACKGROUND RESOLUTION: Try to upgrade to TMDB API Poster automatically
        if (posterUrl === 'N/A' || !posterUrl.includes('tmdb.org')) {
            const imgElement = card.querySelector('img');
            handleImageError(imgElement, movie.Title);
        }
    });
}

// HD Image Resolver Technique
async function handleImageError(img, title) {
    // If we have a valid non-TMDB image, we try to UPGRADE it, but don't overwrite if we fail
    try {
        const response = await fetch(`/api/hd-poster?title=${encodeURIComponent(title)}`);
        const data = await response.json();
        if (data.poster_url && data.poster_url !== 'N/A') {
            img.src = data.poster_url;
            const card = img.closest('.movie-card');
            if (card) {
                const indicator = card.querySelector('.hd-indicator');
                if (indicator) indicator.style.display = 'block';
            }
        }
    } catch (err) {
        console.warn("Upgrade failed for:", title);
    }
}

// Global fallback for truly broken images
function globalImageFallback(img) {
    img.src = 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=400&q=80';
    img.onerror = null; // Prevent infinite loop
}

async function sendFeedback(movieLink, reward, event) {
    event.stopPropagation();
    try {
        const response = await fetch('/api/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                uid: currentUID,
                movie_link: movieLink, 
                reward: reward 
            })
        });
        if (response.ok) {
            let msg = reward > 0 ? "AI learned your like! ✨" : "AI noted your dislike 🛑";
            if (reward === 0.5) msg = "AI is learning your taste... 🧠✨";
            showToast(msg);
            fetchRecommendations(true); // Trigger Mood Shift Animation
            updateHero();
        }
    } catch (err) {
        console.error("Feedback failed", err);
    }
}

function watchMovie(url, event) {
    if (event) event.stopPropagation();
    window.open(url, '_blank');
    // Also send a small positive reward for clicking (interest)
    sendFeedback(url, 0.5, { stopPropagation: () => {} });
}

function showToast(message) {
    toast.innerText = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

// Debounced search for snappy performance
let timeout = null;
searchInput.addEventListener('input', (e) => {
    clearTimeout(timeout);
    // 300ms is the sweet spot for feeling "Instant"
    timeout = setTimeout(() => searchMovies(e.target.value), 300);
});

async function toggleWatchlist(movieLink, title, imageLink, btn, event) {
    if (event) event.stopPropagation();
    if (currentUID === "guest") {
        showToast("Please login to save movies! 🔑");
        loginModal.style.display = 'flex';
        return;
    }

    try {
        const response = await fetch('/api/watchlist/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                uid: currentUID,
                movie_data: {
                    movie_link: movieLink,
                    title: title,
                    image_link: imageLink
                }
            })
        });
        const data = await response.json();
        if (data.status === 'added') {
            showToast("Saved to Watchlist! 📌");
            btn.classList.add('saved');
            userWatchlist.add(movieLink);
        } else if (data.status === 'removed') {
            showToast("Removed from Watchlist 🗑️");
            btn.classList.remove('saved');
            userWatchlist.delete(movieLink);
            // Refresh if in watchlist view
            if (watchlistView.style.display === 'block') fetchWatchlist();
        } else {
            showToast("Failed to save: " + (data.message || "Unknown error"));
        }
    } catch (err) {
        console.error("Watchlist toggle failed", err);
        showToast("Connection error. Try again.");
    }
}

async function fetchWatchlist() {
    try {
        const response = await fetch(`/api/watchlist?uid=${encodeURIComponent(currentUID)}`);
        const data = await response.json();
        
        // Update the local set as well
        userWatchlist = new Set(data.map(m => m['Movie Link']));
        
        if (data.length === 0) {
            watchlistGrid.innerHTML = `
                <div style="text-align: center; grid-column: 1/-1; padding: 50px; color: var(--text-dim);">
                    <i class="fas fa-bookmark" style="font-size: 3rem; margin-bottom: 20px; opacity: 0.2;"></i>
                    <p>Your watchlist is empty.</p>
                    <p style="font-size: 0.8rem; margin-top: 10px;">Movies you save will only be visible to you.</p>
                    <button class="btn btn-play" onclick="showView('home')" style="margin-top: 20px;">Explore Movies</button>
                </div>
            `;
        } else {
            renderMovies(data, watchlistGrid, true);
        }
    } catch (err) {
        console.error("Watchlist fetch failed", err);
    }
}

// Initial load
fetchMetadata();
fetchRecommendations();
updateHero();
showView('home');
