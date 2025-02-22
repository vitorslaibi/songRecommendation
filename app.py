from flask import Flask, render_template, request, redirect, url_for, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Flask app setup
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management

# Spotify API credentials
CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
REDIRECT_URI = "http://localhost:5000/callback"  # Must match Spotify Developer Dashboard

# Spotify OAuth setup
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="user-library-read user-top-read"
)

# Home page
@app.route("/")
def index():
    # Check if user is logged in
    if "token_info" in session:
        return render_template("index.html", logged_in=True)
    return render_template("index.html", logged_in=False)

# Login route
@app.route("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

# Callback route after Spotify login
@app.route("/callback")
def callback():
    session.clear()
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info
    return redirect(url_for("index"))

# Logout route
@app.route("/logout")
def logout():
    session.pop("token_info", None)
    return redirect(url_for("index"))

# Fetch user's top tracks
@app.route("/top_tracks")
def top_tracks():
    if "token_info" not in session:
        return redirect(url_for("login"))
    
    sp = spotipy.Spotify(auth=session["token_info"]["access_token"])
    top_tracks = sp.current_user_top_tracks(limit=10)["items"]
    return render_template("index.html", top_tracks=top_tracks, logged_in=True)

# Recommend songs based on audio features
@app.route("/recommend", methods=["POST"])
def recommend():
    if "token_info" not in session:
        return redirect(url_for("login"))
    
    sp = spotipy.Spotify(auth=session["token_info"]["access_token"])
    track_id = request.form["track_id"]
    
    # Fetch audio features for the selected track
    target_features = sp.audio_features(track_id)[0]
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
    return render_template("index.html", recommendations=recommendations[:5], logged_in=True)

# Run the app
if __name__ == "__main__":
    app.run(debug=True)