"""
YouTube Music API client wrapper for playlist operations using the official YouTube Data API v3.
"""
import os
import json
import traceback
from typing import List, Dict, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request

# Scopes required for managing playlists and searching videos
SCOPES = ["https://www.googleapis.com/auth/youtube"]

class YouTubeClient:
    """Wrapper class for YouTube Data API operations.

    Handles OAuth authentication, playlist creation, searching for songs,
    adding tracks to playlists, and retrieving existing playlists.
    """

    def __init__(self, client_id: str = None, client_secret: str = None, redirect_uri: str = None):
        """Initialize the client.

        Args:
            client_id: Google OAuth client ID (optional, can be read from env).
            client_secret: Google OAuth client secret (optional, can be read from env).
            redirect_uri: OAuth redirect URI (optional, can be read from env).
        """
        self.client_id = client_id or os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/auth/youtube/callback")
        self.creds: Optional[Credentials] = None
        self.youtube = None

    # ---------------------------------------------------------------------
    # Authentication helpers
    # ---------------------------------------------------------------------
    def get_authorization_url(self) -> str:
        """Generate the OAuth authorization URL for the user to visit.
        
        Returns the URL that users should visit to authorize the application.
        """
        from urllib.parse import urlencode
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(SCOPES),
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return auth_url

    def exchange_code_for_token(self, code: str) -> bool:
        """Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            True if successful, False otherwise
        """
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        import requests
        
        try:
            # Exchange code for token
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                'code': code,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri,
                'grant_type': 'authorization_code'
            }
            
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            # Create credentials object
            self.creds = Credentials(
                token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token'),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=SCOPES
            )
            
            # Save credentials to file
            with open("token.json", "w") as token_file:
                token_file.write(self.creds.to_json())
            
            # Build YouTube service
            self.youtube = build("youtube", "v3", credentials=self.creds)
            return True
            
        except Exception as e:
            print(f"❌ Failed to exchange code for token: {e}")
            traceback.print_exc()
            return False

    def _load_credentials(self, token_path: str = "token.json") -> Optional[Credentials]:
        """Load existing credentials from token_path and refresh if needed.

        Returns credentials if successful, None otherwise.
        """
        creds = None
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception as e:
                print(f"⚠️ Failed to load credentials: {e}")
                return None
                
        # If credentials exist but are expired, try to refresh
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed credentials
                with open(token_path, "w") as token_file:
                    token_file.write(creds.to_json())
            except Exception as e:
                print(f"⚠️ Failed to refresh token: {e}")
                return None
                
        return creds if creds and creds.valid else None

    def authenticate(self, token_path: str = "token.json") -> bool:
        """Load existing credentials and initialize the YouTube service.

        Args:
            token_path: Path to the token file
            
        Returns:
            True if authenticated successfully, False otherwise
        """
        try:
            self.creds = self._load_credentials(token_path)
            if not self.creds:
                return False
                
            self.youtube = build("youtube", "v3", credentials=self.creds)
            return True
        except Exception as e:
            print(f"❌ YouTube authentication failed: {e}")
            traceback.print_exc()
            return False

    # ---------------------------------------------------------------------
    # Core API methods
    # ---------------------------------------------------------------------
    def search_song(self, title: str, artist: str, limit: int = 5) -> List[Dict]:
        """Search for a song on YouTube.

        Returns a list of video dictionaries containing ``videoId`` and basic
        metadata. The YouTube Data API does not provide a dedicated *music*
        endpoint, so we perform a regular video search with a combined query.
        """
        if not self.youtube:
            raise Exception("Not authenticated. Call authenticate() first.")
        query = f"{title} {artist}"
        try:
            request = self.youtube.search().list(
                part="snippet",
                q=query,
                type="video",
                maxResults=limit,
                videoCategoryId="10",  # Category 10 = Music
            )
            response = request.execute()
            results = []
            for item in response.get("items", []):
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                results.append({
                    "videoId": video_id,
                    "title": snippet.get("title"),
                    "description": snippet.get("description"),
                    "channelTitle": snippet.get("channelTitle"),
                })
            return results
        except HttpError as e:
            print(f"❌ Error searching for '{title}' by {artist}: {e}")
            return []

    def create_playlist(self, title: str, description: str = "", privacy_status: str = "PRIVATE") -> Optional[str]:
        """Create a new YouTube playlist.

        Args:
            title: Playlist title.
            description: Playlist description.
            privacy_status: ``PRIVATE``, ``PUBLIC`` or ``UNLISTED``.
        Returns:
            The newly created playlist ID or ``None`` on failure.
        """
        if not self.youtube:
            raise Exception("Not authenticated. Call authenticate() first.")
        try:
            request = self.youtube.playlists().insert(
                part="snippet,status",
                body={
                    "snippet": {"title": title, "description": description},
                    "status": {"privacyStatus": privacy_status.lower()},
                },
            )
            response = request.execute()
            return response.get("id")
        except HttpError as e:
            print(f"❌ Error creating playlist '{title}': {e}")
            traceback.print_exc()
            return None

    def get_playlists(self) -> List[Dict]:
        """Retrieve the authenticated user's playlists.

        Returns a list of dictionaries with ``id``, ``title`` and ``count``.
        """
        if not self.youtube:
            raise Exception("Not authenticated. Call authenticate() first.")
        try:
            playlists = []
            request = self.youtube.playlists().list(
                part="snippet,contentDetails",
                mine=True,
                maxResults=50,
            )
            while request:
                response = request.execute()
                for item in response.get("items", []):
                    playlists.append({
                        "id": item.get("id"),
                        "title": item["snippet"].get("title"),
                        "count": int(item["contentDetails"].get("itemCount", 0)),
                    })
                request = self.youtube.playlists().list_next(request, response)
            return playlists
        except HttpError as e:
            print(f"❌ Error fetching playlists: {e}")
            traceback.print_exc()
            return []

    def add_songs_to_playlist(self, playlist_id: str, video_ids: List[str]) -> bool:
        """Add a list of video IDs to an existing playlist.

        The API requires one ``playlistItem`` insertion per video. We batch the
        calls to stay within quota limits.
        """
        if not self.youtube:
            raise Exception("Not authenticated. Call authenticate() first.")
        try:
            for video_id in video_ids:
                request = self.youtube.playlistItems().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "playlistId": playlist_id,
                            "resourceId": {
                                "kind": "youtube#video",
                                "videoId": video_id,
                            },
                        }
                    },
                )
                request.execute()
            return True
        except HttpError as e:
            print(f"❌ Error adding videos to playlist {playlist_id}: {e}")
            traceback.print_exc()
            return False

    def delete_playlist(self, playlist_id: str) -> bool:
        """Delete a playlist by ID.

        Returns True on success, False otherwise.
        """
        if not self.youtube:
            raise Exception("Not authenticated. Call authenticate() first.")
        try:
            request = self.youtube.playlists().delete(id=playlist_id)
            request.execute()
            return True
        except HttpError as e:
            print(f"❌ Error deleting playlist {playlist_id}: {e}")
            traceback.print_exc()
            return False
