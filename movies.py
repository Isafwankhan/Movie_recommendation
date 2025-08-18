import streamlit as st
import requests
import random

# =========================================================================
# Configuration
# =========================================================================

# The API key for The Movie Database (TMDb).
API_KEY = "18f5529a037e94bba4fb6758311b0015"
BASE_URL = "https://api.themoviedb.org/3"
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500/"

# =========================================================================
# Page Setup & Styling
# =========================================================================
st.set_page_config(page_title="Movie Recommender", layout="centered")

st.markdown("""
<style>
/* Simple Black & Red Gradient Theme */
.stApp {
    background: linear-gradient(to bottom, #A52A2A, #0A0A0A); /* A gradient background with a more visible red to black */
    color: #F8F9FA; /* Light text for contrast */
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

h1, h2, h3, h4 {
    color: #A52A2A; /* More visible red for headings */
    text-align: center;
    margin-bottom: 20px;
    font-weight: bold;
}

/* Primary Button (Search & Surprise Me) */
.stButton > button {
    background-color: #A52A2A; /* More visible red button */
    color: #FFFFFF;
    border: 1px solid #A52A2A;
    border-radius: 5px;
    padding: 10px 20px;
    font-weight: bold;
    transition: all 0.2s ease;
    box-shadow: none;
}
.stButton > button:hover {
    background-color: #942525; /* Darker red on hover */
    border-color: #942525;
}

/* Search Bar & Text Input */
.stTextInput > div > div > input {
    background-color: #1A1A1A; /* Darker gray for inputs */
    color: #FFFFFF;
    border: 1px solid #333333;
    border-radius: 5px;
    padding: 10px 15px;
    transition: border-color 0.2s, box-shadow 0.2s;
    box-shadow: none;
}
.stTextInput > div > div > input:focus {
    border-color: #A52A2A;
    box-shadow: 0 0 0 0.2rem rgba(165, 42, 42, 0.25);
}

/* Movie Card Container */
.movie-card-container {
    background-color: #1A1A1A;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 25px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    border: 1px solid #222222;
}

/* Movie Card Content Styling */
.movie-title {
    font-size: 1.5em;
    font-weight: bold;
    color: #A52A2A;
    margin-bottom: 5px;
}
.movie-meta {
    font-size: 0.9em;
    color: #AAAAAA; /* Light gray for meta-info */
    margin-bottom: 15px;
}
.movie-overview {
    font-size: 1em;
    line-height: 1.5;
    color: #CCCCCC;
}

/* Links */
a {
    color: #A52A2A;
    text-decoration: none;
    transition: color 0.2s;
}
a:hover {
    color: #942525;
    text-decoration: underline;
}

/* Separator */
.stDivider {
    background-color: #333333;
    height: 1px;
}

/* Ensure images have rounded corners and shadow */
img {
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: transform 0.3s ease;
}
.movie-poster-item:hover img {
    transform: scale(1.05); /* Zoom effect on hover */
}

/* Horizontal scrollable section */
.horizontal-scroll-container {
    overflow-x: auto;
    white-space: nowrap;
    padding-bottom: 15px; /* Adds space for the scrollbar */
}
.horizontal-scroll-container::-webkit-scrollbar {
    height: 8px;
}
.horizontal-scroll-container::-webkit-scrollbar-track {
    background: #2A2A2A;
    border-radius: 10px;
}
.horizontal-scroll-container::-webkit-scrollbar-thumb {
    background-color: #A52A2A;
    border-radius: 10px;
    border: 2px solid #2A2A2A;
}
.movie-poster-item {
    display: inline-block;
    width: 150px;
    margin-right: 20px;
    vertical-align: top;
    text-align: center;
}
.movie-poster-item p {
    white-space: normal;
    font-size: 0.9em;
    padding-top: 5px;
}
</style>
""", unsafe_allow_html=True)

# =========================================================================
# Session State Initialization
# =========================================================================
if 'surprise_count' not in st.session_state:
    st.session_state.surprise_count = 0
if 'selected_movie' not in st.session_state:
    st.session_state.selected_movie = None
if 'recommendations_list' not in st.session_state:
    st.session_state.recommendations_list = []
if 'header_text' not in st.session_state:
    st.session_state.header_text = ""
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'trending'

# =========================================================================
# API Functions
# =========================================================================

@st.cache_data
def get_genre_list():
    """Fetches the list of movie genres from the TMDb API."""
    genres_url = f"{BASE_URL}/genre/movie/list?api_key={API_KEY}"
    try:
        response = requests.get(genres_url)
        response.raise_for_status()
        return {genre['id']: genre['name'] for genre in response.json()['genres']}
    except requests.exceptions.RequestException:
        return {}

@st.cache_data
def get_movie_details(movie_id):
    """Fetches detailed movie information."""
    details_url = f"{BASE_URL}/movie/{movie_id}?api_key={API_KEY}&append_to_response=videos,external_ids"
    try:
        response = requests.get(details_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return {}

@st.cache_data
def fetch_movies(endpoint, query=None, surprise_id=0):
    """
    A generic function to fetch movies.
    The 'surprise_id' is a dummy parameter to bypass the cache for random fetches.
    """
    if endpoint == "recommendations":
        search_url = f"{BASE_URL}/search/movie?api_key={API_KEY}&query={query}"
        try:
            response = requests.get(search_url)
            response.raise_for_status()
            data = response.json()
            if not data['results']:
                return [], ""
            
            movie_id = sorted(data['results'], key=lambda x: x.get('popularity', 0), reverse=True)[0]['id']
            url = f"{BASE_URL}/movie/{movie_id}/recommendations?api_key={API_KEY}"
            header = f"Recommendations for '{query}'"
        except requests.exceptions.RequestException as e:
            return [], ""
    elif endpoint == "trending":
        url = f"{BASE_URL}/trending/movie/week?api_key={API_KEY}"
        header = "🔥 Trending Movies This Week"
    elif endpoint == "random":
        url = f"{BASE_URL}/movie/popular?api_key={API_KEY}"
        header = "Here is a popular movie for you!"
    else:
        return [], ""
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        results = response.json().get('results', [])
        if endpoint == "random" and results:
            return [random.choice(results)], header
        return results, header
    except requests.exceptions.RequestException as e:
        return [], header

# =========================================================================
# UI Components
# =========================================================================

def display_movie_card(movie):
    """Displays a single movie's details in a card format."""
    details = get_movie_details(movie['id'])
    
    with st.container():
        c1, c2 = st.columns([1, 2])
        
        with c1:
            if movie.get('poster_path'):
                st.image(POSTER_BASE_URL + movie['poster_path'])
            else:
                st.image("https://via.placeholder.co/500x750/111/EEE?text=No+Image", use_column_width=True)
        
        with c2:
            st.markdown(f"<p class='movie-title'>{movie.get('title', 'N/A')}</p>", unsafe_allow_html=True)
            
            meta_info = f"⭐ {movie.get('vote_average', 0):.1f}/10"
            if 'release_date' in movie and movie['release_date']:
                meta_info += f" &nbsp; | &nbsp; 🗓️ {movie['release_date']}"
            st.markdown(f"<p class='movie-meta'>{meta_info}</p>", unsafe_allow_html=True)

            genres = [get_genre_list().get(gid) for gid in movie.get('genre_ids', [])]
            st.write(f"**Genres:** {', '.join(filter(None, genres))}")
            
            overview = movie.get('overview', 'No overview available.')
            if len(overview) > 250:
                overview = overview[:250].rsplit(' ', 1)[0] + "..."
            st.markdown(f"<p class='movie-overview'>{overview}</p>", unsafe_allow_html=True)

            imdb_id = details.get('external_ids', {}).get('imdb_id')
            if imdb_id:
                st.markdown(f"[View on IMDb](https://www.imdb.com/title/{imdb_id})", unsafe_allow_html=True)

            trailer = next((v for v in details.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), None)
            if trailer:
                st.markdown(f"[▶️ Watch Trailer](https://www.youtube.com/watch?v={trailer['key']})", unsafe_allow_html=True)
        
        st.divider()

def display_recommendation_item(movie):
    """Displays a movie poster with a title for the horizontal carousel."""
    image_url = POSTER_BASE_URL + movie['poster_path'] if movie.get('poster_path') else "https://via.placeholder.co/150x225/111/EEE?text=No+Image"
    st.markdown(
        f"""
        <div class="movie-poster-item">
            <img src="{image_url}" alt="{movie.get('title', 'N/A')}" style="width:150px; height:225px;">
            <p>{movie.get('title', 'N/A')}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================================================================
# Main App Layout (Single Page)
# =========================================================================

st.title("🎬 CineGenie")

# --- Search & Surprise UI ---
movie_input = st.text_input(
    "Enter a movie name to get recommendations:",
    placeholder="e.g., The Shawshank Redemption"
)

col1, col2 = st.columns([1, 1])
with col1:
    search_button = st.button("Search", use_container_width=True)
with col2:
    surprise_button = st.button("✨ Surprise Me!", use_container_width=True)

# --- Logic to handle button clicks and set view state ---
if search_button and movie_input:
    st.session_state.current_view = 'search'
elif surprise_button:
    st.session_state.current_view = 'surprise'
elif not movie_input and st.session_state.current_view not in ['search', 'surprise']:
    st.session_state.current_view = 'trending'

# --- Dynamic Content Display based on View State ---
if st.session_state.current_view == 'trending':
    with st.spinner("Finding trending movies..."):
        trending_movies, header_text = fetch_movies("trending")
    if trending_movies:
        st.header(header_text)
        # Display trending movies in the original vertical list
        for movie in trending_movies:
            display_movie_card(movie)
    else:
        st.info("Could not fetch trending movies at this time.")

elif st.session_state.current_view == 'search':
    with st.spinner("Finding your movie and its recommendations..."):
        # First, find the exact movie the user searched for
        search_url = f"{BASE_URL}/search/movie?api_key={API_KEY}&query={movie_input}"
        try:
            response = requests.get(search_url)
            response.raise_for_status()
            data = response.json()
            if data['results']:
                st.session_state.selected_movie = sorted(data['results'], key=lambda x: x.get('popularity', 0), reverse=True)[0]
            else:
                st.session_state.selected_movie = None
                st.error(f"Could not find a movie named '{movie_input}'. Please check the title.")
        except requests.exceptions.RequestException:
            st.session_state.selected_movie = None
            st.error("Error connecting to the movie database.")
        
        if st.session_state.selected_movie:
            # Then fetch its recommendations
            recs, header = fetch_movies("recommendations", query=movie_input)
            st.session_state.recommendations_list = recs
            st.session_state.header_text = header

    if st.session_state.selected_movie:
        st.subheader("Your Movie:")
        display_movie_card(st.session_state.selected_movie)
        st.subheader(st.session_state.header_text)
        if st.session_state.recommendations_list:
            # Display recommendations in a horizontal, scrollable row
            st.markdown('<div class="horizontal-scroll-container">', unsafe_allow_html=True)
            for movie in st.session_state.recommendations_list:
                display_recommendation_item(movie)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info(f"No recommendations found for '{st.session_state.selected_movie['title']}'.")

elif st.session_state.current_view == 'surprise':
    with st.spinner("Picking a random movie for you..."):
        st.session_state.surprise_count += 1
        surprise_movie, header_text = fetch_movies("random", surprise_id=st.session_state.surprise_count)
        if surprise_movie:
            st.header(header_text)
            display_movie_card(surprise_movie[0])
        else:
            st.info("Could not fetch a movie at this time. Please try again.")

# The Clear All button is now conditional
st.markdown("---")
if st.session_state.current_view in ['search', 'surprise']:
    if st.button("Clear All"):
        st.session_state.selected_movie = None
        st.session_state.recommendations_list = []
        st.session_state.current_view = 'trending'
        st.rerun()
