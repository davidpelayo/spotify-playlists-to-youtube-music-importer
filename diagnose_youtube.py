from utils.youtube_client import YouTubeClient

from dotenv import load_dotenv
import os
import json
import traceback

load_dotenv()


def check_youtube_status():
    print("🔍 Starting YouTube Music Diagnostic...")
    
    # 1. Check for token.json file
    token_file = 'token.json'
    
    if not os.path.exists(token_file):
        print("❌ Error: No token.json file found!")
        print("   Please authenticate first by running the web app or CLI script.")
        print("   The authentication flow will create a token.json file automatically.")
        return
    
    print(f"✅ Found token.json file: {token_file}")
    
    # 2. Initialize YouTubeClient
    try:
        print(f"📝 Authenticating with {token_file}...")
        yt = YouTubeClient()
        if not yt.authenticate(token_file):
            print("❌ Failed to authenticate YouTube client.")
            return
        print("✅ YouTubeClient initialized and authenticated successfully.")
    except Exception as e:
        print(f"❌ Error initializing YouTubeClient: {e}")
        traceback.print_exc()
        return

    # 3. Check User/Channel
    library_ready = False
    try:
        # Try to get playlists to verify auth and channel
        playlists = yt.get_playlists()
        print("✅ Successfully fetched playlists.")
        print(f"   Found {len(playlists)} playlists.")
        library_ready = True
    except Exception as e:
        print(f"❌ Error fetching playlists (Possible missing channel?): {e}")
        traceback.print_exc()
        print("   If you've never created a YouTube channel, visit https://www.youtube.com and create one before retrying.")
    
    # 4. Try Create Playlist
    if not library_ready:
        print("⚠️ Skipping playlist creation until your YouTube channel / library access is available.")
        return

    try:
        print("📝 Attempting to create test playlist...")
        title = "Test-Playlist-Diagnostic"
        desc = "Created by diagnostic script"
        res = yt.create_playlist(title=title, description=desc, privacy_status="PRIVATE")
        print(f"✅ Successfully created playlist! ID: {res}")
        
        # Clean up
        print("🧹 Deleting test playlist...")
        yt.delete_playlist(res)
        print("✅ Deleted test playlist.")
        
    except Exception as e:
        print(f"❌ Failed to create playlist: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    check_youtube_status()
