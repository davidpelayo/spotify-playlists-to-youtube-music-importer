"""
Spotify API client wrapper for playlist operations.
"""
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from typing import List, Dict, Optional


class SpotifyClient:
    """Wrapper class for Spotify API operations."""
    
    def __init__(self, client_id: str = None, client_secret: str = None, redirect_uri: str = None):
        """
        Initialize Spotify client with OAuth.
        
        Args:
            client_id: Spotify app client ID
            client_secret: Spotify app client secret
            redirect_uri: OAuth redirect URI
        """
        self.client_id = client_id or os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = redirect_uri or os.getenv('SPOTIFY_REDIRECT_URI')
        
        self.scope = 'playlist-read-private playlist-read-collaborative'
        self.sp = None
    
    def authenticate(self, cache_path: str = '.cache-spotify') -> bool:
        """
        Authenticate with Spotify using OAuth.
        
        Args:
            cache_path: Path to cache authentication token
            
        Returns:
            True if authentication successful
        """
        try:
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=self.scope,
                cache_path=cache_path,
                open_browser=True
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            # Test authentication
            self.sp.current_user()
            return True
        except Exception as e:
            print(f"Spotify authentication failed: {e}")
            return False
    
    def get_playlists(self) -> List[Dict]:
        """
        Get all user playlists.
        
        Returns:
            List of playlist dictionaries with id, name, description, and track count
        """
        if not self.sp:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        playlists = []
        offset = 0
        limit = 50
        
        while True:
            results = self.sp.current_user_playlists(limit=limit, offset=offset)
            
            for item in results['items']:
                playlists.append({
                    'id': item['id'],
                    'name': item['name'],
                    'description': item.get('description', ''),
                    'track_count': item['tracks']['total'],
                    'public': item['public'],
                    'collaborative': item['collaborative']
                })
            
            if results['next']:
                offset += limit
            else:
                break
        
        return playlists
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        """
        Get all tracks from a playlist.
        
        Args:
            playlist_id: Spotify playlist ID
            
        Returns:
            List of track dictionaries with title, artist, album, and duration
        """
        if not self.sp:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        tracks = []
        offset = 0
        limit = 100
        
        while True:
            results = self.sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
            
            for item in results['items']:
                if item['track'] and item['track']['id']:  # Skip null tracks
                    track = item['track']
                    tracks.append({
                        'title': track['name'],
                        'artist': ', '.join([artist['name'] for artist in track['artists']]),
                        'album': track['album']['name'],
                        'duration_ms': track['duration_ms'],
                        'spotify_uri': track['uri'],
                        'isrc': track.get('external_ids', {}).get('isrc')  # International Standard Recording Code
                    })
            
            if results['next']:
                offset += limit
            else:
                break
        
        return tracks
    
    def get_user_info(self) -> Dict:
        """
        Get current user information.
        
        Returns:
            Dictionary with user id, display name, and email
        """
        if not self.sp:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        user = self.sp.current_user()
        return {
            'id': user['id'],
            'name': user.get('display_name', user['id']),
            'email': user.get('email')
        }
