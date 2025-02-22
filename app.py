from flask import Flask, render_template, request, redirect, url_for, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth, CacheFileHandler
import os
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Flask app setup
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management
cache_handler = CacheFileHandler(cache_path=".spotify_token_cache")

# Spotify API credentials
CLIENT_ID = "7b9b560a429140ca8ad82a9c2b6bf5bc"
CLIENT_SECRET = "dcd42166b8d046dd86da1381b66adbc6"
REDIRECT_URI = "http://localhost:5000/callback"  # Must match Spotify Developer Dashboard

# Set up cache handler
cache_handler = CacheFileHandler(cache_path=".spotify_token_cache")

# Spotify OAuth setup
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="user-library-read user-top-read user-read-private user-read-email",
    cache_handler=cache_handler
)

# Function to get Spotify object
def get_spotify_object():
    token_info = cache_handler.get_cached_token()
    print("Cached Token Info:", token_info)
    
    if not token_info:
        print("No token found. Redirecting to login.")
        return None
    
    if sp_oauth.is_token_expired(token_info):
        print("Token expired. Refreshing...")
        token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])
        cache_handler.save_token_to_cache(token_info)
        print("New Token Info:", token_info)
    
    return spotipy.Spotify(auth=token_info["access_token"])

# Home page
@app.route("/")
def index():
    if "token_info" in session:
        return render_template("index.html", logged_in=True)
    return render_template("index.html", logged_in=False)

# Login route
@app.route("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

# Callback route
@app.route("/callback")
def callback():
    session.clear()
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code)
    print("Token Info from Callback:", token_info)
    
    if not token_info:
        return "Failed to retrieve token. Please try again."
    
    session["token_info"] = token_info
    cache_handler.save_token_to_cache(token_info)
    return redirect(url_for("index"))

# Logout route
@app.route("/logout")
def logout():
    session.pop("token_info", None)
    cache_handler.clear()
    return redirect(url_for("index"))

# Top tracks route
@app.route("/top_tracks")
def top_tracks():
    if "token_info" not in session:
        return redirect(url_for("login"))
    
    sp = get_spotify_object()
    if not sp:
        return redirect(url_for("login"))
    
    top_tracks = sp.current_user_top_tracks(limit=10)["items"]
    return render_template("index.html", top_tracks=top_tracks, logged_in=True)

# Recommend route
@app.route("/recommend", methods=["POST"])
def recommend():
    if "token_info" not in session:
        return redirect(url_for("login"))
    
    sp = get_spotify_object()
    if not sp:
        return redirect(url_for("login"))
    
    track_id = request.form["track_id"]
    
    try:
        # Fetch audio features for the selected track
        target_features = sp.audio_features(track_id)[0]
        if not target_features:
            return "Failed to fetch audio features. Please try again."
        
        target_vector = np.array([
            target_features["danceability"],
            target_features["energy"],
            target_features["valence"],
            target_features["tempo"]
        ]).reshape(1, -1)
        
        # Fetch user's saved tracks
        saved_tracks = sp.current_user_saved_tracks(limit=50)["items"]
        track_ids = [track["track"]["id"] for track in saved_tracks]
        features_list = sp.audio_features(track_ids)
        
        # Compute similarity
        recommendations = []
        for i, features in enumerate(features_list):
            if features:
                feature_vector = np.array([
                    features["danceability"],
                    features["energy"],
                    features["valence"],
                    features["tempo"]
                ]).reshape(1, -1)
                similarity = cosine_similarity(target_vector, feature_vector)[0][0]
                recommendations.append({
                    "name": saved_tracks[i]["track"]["name"],
                    "artist": saved_tracks[i]["track"]["artists"][0]["name"],
                    "similarity": similarity
                })
        
        # Sort by similarity
        recommendations.sort(key=lambda x: x["similarity"], reverse=True)
        return render_template("recommend.html", recommendations=recommendations[:5], logged_in=True)
    
    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify API Error: {e}")
        return f"Spotify API Error: {e}", 403

# Run the app
if __name__ == "__main__":
    app.run(debug=True)