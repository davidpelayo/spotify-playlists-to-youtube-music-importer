"""
YouTube Music API client wrapper for playlist operations.
"""
from ytmusicapi import YTMusic
from ytmusicapi.auth.oauth.credentials import OAuthCredentials
import os
import json
from typing import List, Dict, Optional


class YouTubeClient:
    """Wrapper class for YouTube Music API operations."""
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        """
        Initialize YouTube Music client.
        
        Args:
            client_id: YouTube Data API OAuth client ID
            client_secret: YouTube Data API OAuth client secret
        """
        self.client_id = client_id or os.getenv('YOUTUBE_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('YOUTUBE_CLIENT_SECRET')
        self.ytmusic = None
    
    def authenticate(self, oauth_path: str = 'oauth.json') -> bool:
        """
        Authenticate with YouTube Music using OAuth.
        
        Args:
            oauth_path: Path to store OAuth credentials
            
        Returns:
            True if authentication successful
        """
        try:
            # Check if oauth.json already exists
            if os.path.exists(oauth_path):
                # Try to use existing credentials
                try:
                    self.ytmusic = YTMusic(
                        oauth_path,
                        oauth_credentials=OAuthCredentials(
                            client_id=self.client_id,
                            client_secret=self.client_secret
                        )
                    )
                    return True
                except Exception:
                    # If existing credentials are invalid, delete and re-authenticate
                    os.remove(oauth_path)
            
            # Setup new OAuth credentials using the setup_oauth function
            print("\n=== YouTube Music Authentication ===")
            print("Setting up OAuth authentication...")
            print("This will open your browser for authentication.\n")
            
            # Import setup_oauth function
            from ytmusicapi import setup_oauth
            
            # Setup OAuth with client credentials (client_id and client_secret are keyword-only params)
            setup_oauth(
                filepath=oauth_path,
                open_browser=True,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            # Initialize YTMusic with the oauth file and credentials
            self.ytmusic = YTMusic(
                oauth_path,
                oauth_credentials=OAuthCredentials(
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
            )
            
            return True
        except Exception as e:
            print(f"YouTube Music authentication failed: {e}")
            return False
    
    def search_song(self, title: str, artist: str, limit: int = 5) -> List[Dict]:
        """
        Search for a song on YouTube Music.
        
        Args:
            title: Song title
            artist: Artist name
            limit: Maximum number of results
            
        Returns:
            List of matching songs with videoId, title, and artists
        """
        if not self.ytmusic:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            # Search with combined query
            query = f"{title} {artist}"
            results = self.ytmusic.search(query, filter='songs', limit=limit)
            
            songs = []
            for result in results:
                songs.append({
                    'videoId': result.get('videoId'),
                    'title': result.get('title'),
                    'artists': ', '.join([artist['name'] for artist in result.get('artists', [])]),
                    'album': result.get('album', {}).get('name') if result.get('album') else None,
                    'duration': result.get('duration'),
                    'duration_seconds': result.get('duration_seconds')
                })
            
            return songs
        except Exception as e:
            print(f"Error searching for '{title}' by {artist}: {e}")
            return []
    
    def create_playlist(self, title: str, description: str = "", privacy_status: str = "PRIVATE") -> Optional[str]:
        """
        Create a new playlist on YouTube Music.
        
        Args:
            title: Playlist title
            description: Playlist description
            privacy_status: Privacy setting (PRIVATE, PUBLIC, or UNLISTED)
            
        Returns:
            Playlist ID if successful, None otherwise
        """
        if not self.ytmusic:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            playlist_id = self.ytmusic.create_playlist(
                title=title,
                description=description,
                privacy_status=privacy_status
            )
            return playlist_id
        except Exception as e:
            print(f"Error creating playlist '{title}': {e}")
            return None
    
    def add_songs_to_playlist(self, playlist_id: str, video_ids: List[str]) -> bool:
        """
        Add songs to a playlist.
        
        Args:
            playlist_id: YouTube Music playlist ID
            video_ids: List of video IDs to add
            
        Returns:
            True if successful
        """
        if not self.ytmusic:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            # Filter out None values
            valid_ids = [vid for vid in video_ids if vid]
            
            if not valid_ids:
                return False
            
            # Add songs in batches to avoid rate limiting
            batch_size = 50
            for i in range(0, len(valid_ids), batch_size):
                batch = valid_ids[i:i + batch_size]
                self.ytmusic.add_playlist_items(playlist_id, batch)
            
            return True
        except Exception as e:
            print(f"Error adding songs to playlist: {e}")
            return False
    
    def get_playlists(self) -> List[Dict]:
        """
        Get user's playlists.
        
        Returns:
            List of playlist dictionaries
        """
        if not self.ytmusic:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            playlists = self.ytmusic.get_library_playlists(limit=None)
            
            result = []
            for playlist in playlists:
                result.append({
                    'id': playlist.get('playlistId'),
                    'title': playlist.get('title'),
                    'count': playlist.get('count', 0)
                })
            
            return result
        except Exception as e:
            print(f"Error fetching playlists: {e}")
            return []
