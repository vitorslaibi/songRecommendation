# app.py
from flask import Flask, render_template, request, redirect, url_for
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

app = Flask(__name__)

# Spotify API credentials (replace with your own)
SPOTIPY_CLIENT_ID = '06aed9b7e2d643528ab2098e1fdfbc83'
SPOTIPY_CLIENT_SECRET = '65f60096ce6a49c88490b3de1a28f75b'

# Initialize Spotipy client
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET
))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    # Get the song name from the form
    song_name = request.form['song_name']

    # Search for the song on Spotify
    results = sp.search(q=song_name, limit=1, type='track')
    if not results['tracks']['items']:
        return "No results found. Please try again."

    # Get the track ID of the first result
    track_id = results['tracks']['items'][0]['id']

    # Get recommendations based on the track
    recommendations = sp.recommendations(seed_tracks=[track_id], limit=5)

    # Extract recommended tracks
    recommended_tracks = []
    for track in recommendations['tracks']:
        track_info = {
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'preview_url': track['preview_url']
        }
        recommended_tracks.append(track_info)

    return render_template('index.html', recommendations=recommended_tracks)

if __name__ == '__main__':
    app.run(debug=True)