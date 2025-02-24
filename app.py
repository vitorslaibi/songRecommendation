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

def get_recommendations(seed_tracks):
    """Get recommendations with additional parameters for better results"""
    try:
        # Get audio features for seed tracks to use as recommendation parameters
        audio_features = sp.audio_features(seed_tracks[:5])
        if audio_features and audio_features[0]:
            # Calculate average values from seed tracks
            avg_tempo = sum(track['tempo'] for track in audio_features) / len(audio_features)
            avg_danceability = sum(track['danceability'] for track in audio_features) / len(audio_features)
            avg_energy = sum(track['energy'] for track in audio_features) / len(audio_features)
            
            # Get recommendations with target values
            recommendations = sp.recommendations(
                seed_tracks=seed_tracks[:5],
                limit=10,
                target_tempo=avg_tempo,
                target_danceability=avg_danceability,
                target_energy=avg_energy,
                min_popularity=50
            )
        else:
            # Fallback if no audio features available
            recommendations = sp.recommendations(
                seed_tracks=seed_tracks[:5],
                limit=10,
                min_popularity=50
            )
        
        print(f"Recommendations received: {len(recommendations['tracks'])} tracks")
        return recommendations
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return None

@app.route('/')
def index():
    if not session.get('token_info'):
        return render_template('index.html', authenticated=False)
    
    try:
        # Get user's top tracks
        top_tracks = sp.current_user_top_tracks(limit=5, offset=0, time_range='medium_term')
        print(f"Top tracks received: {len(top_tracks['items'])} tracks")
        
        recommendations = None
        if top_tracks['items']:
            seed_tracks = [track['id'] for track in top_tracks['items']]
            recommendations = get_recommendations(seed_tracks)
        else:
            # Fallback to some popular tracks if user has no top tracks
            fallback_tracks = [
                '11dFghVXANMlKmJXsNCbNl',  # "Stay With Me" by Sam Smith
                '7KXjTSCq5nL1LoYtL7XAwS',  # "HUMBLE." by Kendrick Lamar
                '1zi7xx7UVEFkmKfv06H8x0',  # "One Dance" by Drake
                '3T4UodGkfZObJ43RtA5KDF',  # "Thinking Out Loud" by Ed Sheeran
                '5uCax9HTNlzGybIStD3vDh'   # "Say You Won't Let Go" by James Arthur
            ]
            recommendations = get_recommendations(fallback_tracks)
        
        if recommendations and recommendations['tracks']:
            return render_template(
                'index.html',
                authenticated=True,
                top_tracks=top_tracks['items'],
                recommendations=recommendations['tracks']
            )
        else:
            return render_template(
                'index.html',
                authenticated=True,
                top_tracks=top_tracks['items'],
                error="Unable to get recommendations at this time. Please try again."
            )
            
    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify API Error: {e}")
        session.clear()
        return render_template('index.html', authenticated=False, error="Please log in again.")
    except Exception as e:
        print(f"Error: {e}")
        return render_template('index.html', authenticated=True, error=str(e))

@app.route('/login')
def login():
    session.clear()
    auth_url = sp.auth_manager.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    try:
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