from flask import Flask, render_template, request, redirect, url_for, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure secret key

# Spotify API credentials
SPOTIPY_CLIENT_ID = 'your_client_id'
SPOTIPY_CLIENT_SECRET = 'your_client_secret'
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
        
        # Check if we have any top tracks
        if not top_tracks['items']:
            # If no top tracks, use some popular tracks as seeds
            # You can modify these IDs with tracks that make sense for your use case
            seed_tracks = ['11dFghVXANMlKmJXsNCbNl']  # Example: "Stay With Me" by Sam Smith
        else:
            seed_tracks = [track['id'] for track in top_tracks['items']]
        
        # Get recommendations based on seed tracks
        try:
            recommendations = sp.recommendations(
                seed_tracks=seed_tracks[:5],
                limit=10,
                min_popularity=50  # Add some parameters to improve recommendations
            )
        except Exception as e:
            print(f"Recommendation error: {e}")
            recommendations = {'tracks': []}
        
        return render_template(
            'index.html',
            authenticated=True,
            top_tracks=top_tracks['items'] if top_tracks['items'] else [],
            recommendations=recommendations['tracks']
        )
    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify API Error: {e}")
        session.clear()  # Clear session on API error
        return render_template('index.html', authenticated=False, error="Please log in again.")
    except Exception as e:
        print(f"Error: {e}")
        return render_template('index.html', authenticated=True, error=str(e))

@app.route('/login')
def login():
    # Clear any existing session
    session.clear()
    # Get auth URL
    auth_url = sp.auth_manager.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    try:
        # Get token info from callback
        token_info = sp.auth_manager.get_access_token(request.args['code'])
        session['token_info'] = token_info
    except Exception as e:
        print(f"Callback error: {e}")
        return render_template('index.html', authenticated=False, error="Authentication failed. Please try again.")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)