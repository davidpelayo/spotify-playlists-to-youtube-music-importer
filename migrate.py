#!/usr/bin/env python3
"""
CLI script for migrating Spotify playlists to YouTube Music.
"""
import os
import sys
from dotenv import load_dotenv
from utils.spotify_client import SpotifyClient
from utils.youtube_client import YouTubeClient
from utils.matcher import migrate_playlist


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_progress(current, total, track_name, status):
    """Print migration progress."""
    status_icons = {
        'searching': '🔍',
        'matched': '✅',
        'unmatched': '❌'
    }
    icon = status_icons.get(status, '⏳')
    percentage = (current / total) * 100
    print(f"{icon} [{current}/{total}] ({percentage:.1f}%) {track_name}")


def select_playlists(playlists):
    """
    Interactive playlist selection.
    
    Args:
        playlists: List of playlist dictionaries
        
    Returns:
        List of selected playlist IDs
    """
    print("\nYour Spotify Playlists:")
    print("-" * 60)
    
    for i, playlist in enumerate(playlists, 1):
        track_info = f"{playlist['track_count']} tracks"
        print(f"{i}. {playlist['name']} ({track_info})")
    
    print("\nEnter playlist numbers to migrate (comma-separated, or 'all'):")
    print("Example: 1,3,5 or all")
    
    while True:
        selection = input("\nSelection: ").strip()
        
        if selection.lower() == 'all':
            return [p['id'] for p in playlists]
        
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            
            # Validate indices
            if all(0 <= i < len(playlists) for i in indices):
                return [playlists[i]['id'] for i in indices]
            else:
                print("Invalid playlist number. Please try again.")
        except ValueError:
            print("Invalid input. Please enter numbers separated by commas.")


def main():
    """Main CLI application."""
    load_dotenv()
    
    print_header("Spotify to YouTube Music Playlist Migrator")
    
    # Step 1: Authenticate with Spotify
    print_header("Step 1: Connect to Spotify")
    spotify = SpotifyClient()
    
    print("Opening browser for Spotify authentication...")
    if not spotify.authenticate():
        print("❌ Failed to authenticate with Spotify.")
        return 1
    
    user = spotify.get_user_info()
    print(f"✅ Connected as: {user['name']}")
    
    # Step 2: Get playlists
    print_header("Step 2: Fetch Your Playlists")
    print("Loading playlists from Spotify...")
    
    playlists = spotify.get_playlists()
    
    if not playlists:
        print("❌ No playlists found.")
        return 1
    
    print(f"✅ Found {len(playlists)} playlists")
    
    # Step 3: Select playlists
    selected_ids = select_playlists(playlists)
    selected_playlists = [p for p in playlists if p['id'] in selected_ids]
    
    print(f"\n✅ Selected {len(selected_playlists)} playlist(s) for migration")
    
    # Step 4: Authenticate with YouTube Music
    print_header("Step 4: Connect to YouTube Music")
    youtube = YouTubeClient()
    
    print("Setting up YouTube Music authentication...")
    print("Note: You will need to visit a URL and enter a code.\n")
    
    if not youtube.authenticate():
        print("❌ Failed to authenticate with YouTube Music.")
        return 1
    
    print("✅ Connected to YouTube Music")
    
    # Step 5: Migrate playlists
    print_header("Step 5: Migrating Playlists")
    
    migration_summary = {
        'total_playlists': len(selected_playlists),
        'successful': 0,
        'failed': 0,
        'total_tracks': 0,
        'matched_tracks': 0,
        'unmatched_tracks': 0
    }
    
    for i, playlist in enumerate(selected_playlists, 1):
        print(f"\n{'─' * 60}")
        print(f"Playlist {i}/{len(selected_playlists)}: {playlist['name']}")
        print(f"{'─' * 60}")
        
        # Get tracks from Spotify
        print(f"📥 Fetching {playlist['track_count']} tracks from Spotify...")
        tracks = spotify.get_playlist_tracks(playlist['id'])
        
        if not tracks:
            print("⚠️  No tracks found in this playlist. Skipping.")
            migration_summary['failed'] += 1
            continue
        
        print(f"✅ Loaded {len(tracks)} tracks")
        
        # Create playlist on YouTube Music
        print(f"📝 Creating playlist on YouTube Music...")
        yt_playlist_id = youtube.create_playlist(
            title=f"spotify-{playlist['name']}",
            description=playlist['description'] or f"Migrated from Spotify",
            privacy_status="PRIVATE"
        )
        
        if not yt_playlist_id:
            print("❌ Failed to create playlist on YouTube Music")
            migration_summary['failed'] += 1
            continue
        
        print(f"✅ Created playlist")
        
        # Match and migrate tracks
        print(f"\n🔍 Matching tracks on YouTube Music...\n")
        
        results = migrate_playlist(tracks, youtube, progress_callback=print_progress)
        
        # Add matched tracks to playlist
        if results['videoIds']:
            print(f"\n📤 Adding {len(results['videoIds'])} matched tracks to playlist...")
            youtube.add_songs_to_playlist(yt_playlist_id, results['videoIds'])
            print("✅ Tracks added successfully")
        
        # Update summary
        migration_summary['successful'] += 1
        migration_summary['total_tracks'] += results['total']
        migration_summary['matched_tracks'] += results['matched']
        migration_summary['unmatched_tracks'] += results['unmatched']
        
        # Show unmatched tracks
        if results['unmatched_tracks']:
            print(f"\n⚠️  {len(results['unmatched_tracks'])} tracks could not be matched:")
            for track in results['unmatched_tracks'][:5]:  # Show first 5
                print(f"   - {track}")
            if len(results['unmatched_tracks']) > 5:
                print(f"   ... and {len(results['unmatched_tracks']) - 5} more")
    
    # Final summary
    print_header("Migration Complete!")
    print(f"Playlists migrated: {migration_summary['successful']}/{migration_summary['total_playlists']}")
    print(f"Total tracks processed: {migration_summary['total_tracks']}")
    print(f"Tracks matched: {migration_summary['matched_tracks']} ({migration_summary['matched_tracks'] / max(migration_summary['total_tracks'], 1) * 100:.1f}%)")
    print(f"Tracks unmatched: {migration_summary['unmatched_tracks']}")
    print("\n✅ All done! Check your YouTube Music library for the migrated playlists.\n")
    
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
