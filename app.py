from flask import Flask, render_template, request, redirect, url_for, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure secret key

# Spotify API credentials
SPOTIPY_CLIENT_ID = 'your_c06aed9b7e2d643528ab2098e1fdfbc83lient_id'
SPOTIPY_CLIENT_SECRET = '65f60096ce6a49c88490b3de1a28f75b'
SPOTIPY_REDIRECT_URI = 'http://localhost:5000/callback'
SCOPE = 'user-library-read playlist-modify-public user-top-read'

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope=SCOPE
))

@app.route('/')
def index():
    # Check if user is authenticated
    if not session.get('token_info'):
        return render_template('index.html', authenticated=False)
    
    try:
        # Get user's top tracks
        top_tracks = sp.current_user_top_tracks(limit=5, offset=0, time_range='medium_term')
        
        # Get recommendations based on top tracks
        seed_tracks = [track['id'] for track in top_tracks['items']]
        recommendations = sp.recommendations(seed_tracks=seed_tracks[:5], limit=10)
        
        return render_template(
            'index.html',
            authenticated=True,
            top_tracks=top_tracks['items'],
            recommendations=recommendations['tracks']
        )
    except Exception as e:
        print(f"Error: {e}")
        return render_template('index.html', authenticated=False, error=str(e))

@app.route('/login')
def login():
    # Clear any existing session
    session.clear()
    # Get auth URL
    auth_url = sp.auth_manager.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    # Get token info from callback
    token_info = sp.auth_manager.get_access_token(request.args['code'])
    session['token_info'] = token_info
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)