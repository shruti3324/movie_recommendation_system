import streamlit as st
import pickle
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)


# ============================================================
# FANART API KEY
# ============================================================

FANART_API_KEY = st.secrets["FANART_API_KEY"]


# ============================================================
# LOAD MOVIE DATA
# ============================================================

@st.cache_data
def load_movies():

    with open("movies_dict.pkl", "rb") as file:
        movies_dict = pickle.load(file)

    return pd.DataFrame(movies_dict)


# ============================================================
# LOAD SIMILARITY
# ============================================================

@st.cache_resource
def load_similarity():

    with open("similarity.pkl", "rb") as file:
        return pickle.load(file)


movies = load_movies()
similarity = load_similarity()


# ============================================================
# FETCH POSTER FROM FANART
# ============================================================

@st.cache_data(ttl=86400)
def fetch_poster(movie_id):

    try:

        movie_id = str(movie_id)

        # Fanart API URL
        url = (
            f"https://webservice.fanart.tv/"
            f"v3.2/movies/{movie_id}"
        )

        response = requests.get(
            url,
            params={
                "api_key": FANART_API_KEY
            },
            timeout=5
        )

        # API error
        if response.status_code != 200:

            print(
                f"Fanart error for {movie_id}: "
                f"{response.status_code}"
            )

            return None

        # Convert response to JSON
        data = response.json()

        # Get movie posters
        posters = data.get(
            "movieposter",
            []
        )

        # No poster
        if not posters:
            return None

        # Return poster URL
        return posters[0].get("url")

    except Exception as e:

        print(
            f"Poster error for {movie_id}: {e}"
        )

        return None


# ============================================================
# RECOMMEND MOVIES
# ============================================================

def recommend(movie):

    # Find selected movie index
    movie_index = movies[
        movies["title"] == movie
    ].index[0]

    # Similarity values
    distances = similarity[movie_index]

    # Get top 5 recommendations
    movies_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:6]

    recommended_movies = []
    movie_ids = []

    # --------------------------------------------------------
    # Get movie names and IDs
    # --------------------------------------------------------

    for item in movies_list:

        recommended_index = item[0]

        # Movie title
        title = movies.iloc[
            recommended_index
        ]["title"]

        recommended_movies.append(
            title
        )

        # TMDB ID
        if "id" in movies.columns:

            movie_id = movies.iloc[
                recommended_index
            ]["id"]

        elif "movie_id" in movies.columns:

            movie_id = movies.iloc[
                recommended_index
            ]["movie_id"]

        else:

            movie_id = None

        movie_ids.append(movie_id)

    # --------------------------------------------------------
    # Fetch posters simultaneously
    # --------------------------------------------------------

    with ThreadPoolExecutor(
        max_workers=5
    ) as executor:

        recommended_posters = list(
            executor.map(
                fetch_poster,
                movie_ids
            )
        )

    return (
        recommended_movies,
        recommended_posters
    )


# ============================================================
# STREAMLIT UI
# ============================================================

st.title("🎬 Movie Recommender System")

st.write(
    "Select a movie and discover similar movies."
)


# ============================================================
# MOVIE SELECT BOX
# ============================================================

selected_movie = st.selectbox(
    "Select a movie",
    movies["title"].values
)


# ============================================================
# RECOMMEND BUTTON
# ============================================================

if st.button(
    "🎥 Recommend Movies",
    type="primary"
):

    with st.spinner(
        "Finding similar movies..."
    ):

        names, posters = recommend(
            selected_movie
        )

    st.subheader(
        f"Movies similar to {selected_movie}"
    )

    # Create five columns
    columns = st.columns(5)

    # Display results
    for i in range(len(names)):

        with columns[i]:

            # Poster
            if posters[i]:

                st.image(
                    posters[i],
                    use_container_width=True
                )

            else:

                st.info(
                    "Poster unavailable"
                )

            # Movie name
            st.markdown(
                f"**{names[i]}**"
            )