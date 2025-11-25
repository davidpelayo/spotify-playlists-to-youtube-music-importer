"""
Flask web application for migrating Spotify playlists to YouTube Music.
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from dotenv import load_dotenv
import os
import json
import time
from utils.spotify_client import SpotifyClient
from utils.youtube_client import YouTubeClient
from utils.matcher import migrate_playlist
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID')
YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET')
print(f"DEBUG: YouTube Client ID: {YOUTUBE_CLIENT_ID[:20]}...")


@app.route('/')
def index():
    """Serve main application page."""
    return render_template('index.html')


@app.route('/auth/spotify')
def spotify_auth():
    """Initiate Spotify OAuth flow."""
    scope = 'playlist-read-private playlist-read-collaborative'
    
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=scope,
        cache_path=None,
        show_dialog=True
    )
    
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/auth/spotify/callback')
def spotify_callback():
    """Handle Spotify OAuth callback."""
    code = request.args.get('code')
    
    if not code:
        return "Error: No authorization code received", 400
    
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope='playlist-read-private playlist-read-collaborative',
        cache_path=None
    )
    
    token_info = sp_oauth.get_access_token(code)
    
    if token_info:
        session['spotify_token'] = token_info
        return redirect('/?spotify=connected')
    
    return "Error: Failed to get access token", 400


@app.route('/auth/youtube')
def youtube_auth():
    """Initiate YouTube Music OAuth flow."""
    # For YouTube Music, we'll use a different approach
    # Store a flag to trigger OAuth in the frontend
    return redirect('/?youtube=auth')


@app.route('/api/spotify/status')
def spotify_status():
    """Check Spotify authentication status."""
    if 'spotify_token' in session:
        try:
            sp = spotipy.Spotify(auth=session['spotify_token']['access_token'])
            user = sp.current_user()
            return jsonify({
                'authenticated': True,
                'user': {
                    'name': user.get('display_name', user['id']),
                    'id': user['id']
                }
            })
        except:
            session.pop('spotify_token', None)
            return jsonify({'authenticated': False})
    
    return jsonify({'authenticated': False})


@app.route('/api/spotify/playlists')
def get_spotify_playlists():
    """Get user's Spotify playlists."""
    if 'spotify_token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        spotify = SpotifyClient()
        spotify.sp = spotipy.Spotify(auth=session['spotify_token']['access_token'])
        playlists = spotify.get_playlists()
        return jsonify({'playlists': playlists})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/youtube/authenticate', methods=['POST'])
def youtube_authenticate():
    """Authenticate with YouTube Music."""
    try:
        youtube = YouTubeClient()
        
        # Use session-specific oauth file
        oauth_path = f'oauth_{session.get("session_id", "default")}.json'
        
        if youtube.authenticate(oauth_path):
            session['youtube_authenticated'] = True
            session['youtube_oauth_path'] = oauth_path
            return jsonify({'success': True})
        
        return jsonify({'error': 'Authentication failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/youtube/status')
def youtube_status():
    """Check YouTube Music authentication status."""
    if session.get('youtube_authenticated'):
        return jsonify({'authenticated': True})
    
    return jsonify({'authenticated': False})


@app.route('/api/migrate', methods=['POST'])
def migrate():
    """Migrate selected playlists."""
    if 'spotify_token' not in session:
        return jsonify({'error': 'Spotify not authenticated'}), 401
    
    if not session.get('youtube_authenticated'):
        return jsonify({'error': 'YouTube Music not authenticated'}), 401
    
    data = request.json
    playlist_ids = data.get('playlist_ids', [])
    
    if not playlist_ids:
        return jsonify({'error': 'No playlists selected'}), 400
    
    # Use Server-Sent Events for real-time progress
    def generate():
        try:
            # Initialize clients
            spotify = SpotifyClient()
            spotify.sp = spotipy.Spotify(auth=session['spotify_token']['access_token'])
            
            youtube = YouTubeClient()
            oauth_path = session.get('youtube_oauth_path', 'oauth.json')
            youtube.ytmusic = __import__('ytmusicapi').YTMusic(oauth_path)
            
            # Get playlist details
            all_playlists = spotify.get_playlists()
            selected_playlists = [p for p in all_playlists if p['id'] in playlist_ids]
            
            yield f"data: {json.dumps({'type': 'start', 'total_playlists': len(selected_playlists)})}\n\n"
            
            for i, playlist in enumerate(selected_playlists):
                yield f"data: {json.dumps({'type': 'playlist_start', 'playlist': playlist, 'index': i})}\n\n"
                
                # Get tracks
                tracks = spotify.get_playlist_tracks(playlist['id'])
                yield f"data: {json.dumps({'type': 'tracks_loaded', 'count': len(tracks)})}\n\n"
                
                # Create YouTube playlist
                yt_playlist_id = youtube.create_playlist(
                    title=f"spotify-{playlist['name']}",
                    description=playlist['description'] or "Migrated from Spotify",
                    privacy_status="PRIVATE"
                )
                
                if not yt_playlist_id:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to create playlist'})}\n\n"
                    continue
                
                yield f"data: {json.dumps({'type': 'playlist_created'})}\n\n"
                
                # Migrate tracks with progress
                def progress_callback(current, total, track_name, status):
                    progress_data = {
                        'type': 'track_progress',
                        'current': current,
                        'total': total,
                        'track_name': track_name,
                        'status': status
                    }
                    return f"data: {json.dumps(progress_data)}\n\n"
                
                # Custom migration with yielding
                matched_count = 0
                unmatched_count = 0
                
                for j, track in enumerate(tracks):
                    track_name = f"{track['title']} - {track['artist']}"
                    
                    yield f"data: {json.dumps({'type': 'track_progress', 'current': j + 1, 'total': len(tracks), 'track_name': track_name, 'status': 'searching'})}\n\n"
                    
                    # Search for match
                    results = youtube.search_song(track['title'], track['artist'], limit=5)
                    
                    from utils.matcher import match_song
                    match, confidence = match_song(track, results)
                    
                    if match and match.get('videoId'):
                        youtube.add_songs_to_playlist(yt_playlist_id, [match['videoId']])
                        matched_count += 1
                        yield f"data: {json.dumps({'type': 'track_progress', 'current': j + 1, 'total': len(tracks), 'track_name': track_name, 'status': 'matched'})}\n\n"
                    else:
                        unmatched_count += 1
                        yield f"data: {json.dumps({'type': 'track_progress', 'current': j + 1, 'total': len(tracks), 'track_name': track_name, 'status': 'unmatched'})}\n\n"
                
                yield f"data: {json.dumps({'type': 'playlist_complete', 'matched': matched_count, 'unmatched': unmatched_count})}\n\n"
            
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    # Generate session ID for each session
    @app.before_request
    def before_request():
        if 'session_id' not in session:
            import uuid
            session['session_id'] = str(uuid.uuid4())
    
    # Check if SSL certificates exist
    import os
    cert_file = 'cert.pem'
    key_file = 'key.pem'
    
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        print("\n⚠️  SSL certificates not found!")
        print("Generating self-signed certificates for HTTPS...")
        print("(Required for Spotify OAuth)\n")
        
        # Generate certificates
        os.system('python3 generate_cert.py')
        
        if not os.path.exists(cert_file) or not os.path.exists(key_file):
            print("\n❌ Failed to generate SSL certificates.")
            print("Please run: python3 generate_cert.py\n")
            exit(1)
    
    print("\n" + "="*60)
    print("  Starting Playlist Migrator Web App")
    print("="*60)
    print(f"\n🌐 Server running at: https://playlists.migrator:5000")
    print("\n⚠️  Your browser will show a security warning because we're")
    print("   using a self-signed certificate. This is normal for local")
    print("   development. Click 'Advanced' and 'Proceed to localhost'.\n")
    print("="*60 + "\n")
    
    # Run with SSL context
    ssl_context = (cert_file, key_file)
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'False') == 'True',
        port=5000,
        ssl_context=ssl_context
    )
