"""
Song matching utilities for finding YouTube Music equivalents of Spotify tracks.
"""
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher


def normalize_string(s: str) -> str:
    """
    Normalize a string for comparison.
    
    Args:
        s: String to normalize
        
    Returns:
        Lowercase string with extra whitespace removed
    """
    return ' '.join(s.lower().strip().split())


def calculate_similarity(s1: str, s2: str) -> float:
    """
    Calculate similarity ratio between two strings.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Similarity ratio between 0 and 1
    """
    return SequenceMatcher(None, normalize_string(s1), normalize_string(s2)).ratio()


def match_song(spotify_track: Dict, youtube_results: List[Dict]) -> Tuple[Optional[Dict], float]:
    """
    Find the best matching YouTube Music song for a Spotify track.
    
    Args:
        spotify_track: Spotify track dictionary with 'title' and 'artist'
        youtube_results: List of YouTube Music search results
        
    Returns:
        Tuple of (best_match, confidence_score)
        best_match is None if no good match found
    """
    if not youtube_results:
        return None, 0.0
    
    spotify_title = spotify_track['title']
    spotify_artist = spotify_track['artist']
    
    best_match = None
    best_score = 0.0
    
    for yt_song in youtube_results:
        yt_title = yt_song.get('title', '')
        yt_artists = yt_song.get('artists', '')
        
        # Calculate title similarity
        title_similarity = calculate_similarity(spotify_title, yt_title)
        
        # Calculate artist similarity
        artist_similarity = calculate_similarity(spotify_artist, yt_artists)
        
        # Weighted score (title is more important)
        score = (title_similarity * 0.6) + (artist_similarity * 0.4)
        
        # Bonus if both title and artist are good matches
        if title_similarity > 0.8 and artist_similarity > 0.7:
            score += 0.1
        
        if score > best_score:
            best_score = score
            best_match = yt_song
    
    # Only return match if confidence is reasonable
    if best_score < 0.6:
        return None, best_score
    
    return best_match, best_score


def find_youtube_match(spotify_track: Dict, youtube_client) -> Optional[str]:
    """
    Find YouTube Music video ID for a Spotify track.
    
    Args:
        spotify_track: Spotify track dictionary
        youtube_client: YouTubeClient instance
        
    Returns:
        YouTube video ID if found, None otherwise
    """
    # Search YouTube Music
    results = youtube_client.search_song(
        title=spotify_track['title'],
        artist=spotify_track['artist'],
        limit=5
    )
    
    # Find best match
    match, confidence = match_song(spotify_track, results)
    
    if match:
        return match['videoId']
    
    return None


def migrate_playlist(spotify_tracks: List[Dict], youtube_client, progress_callback=None) -> Dict:
    """
    Migrate a list of Spotify tracks to YouTube Music.
    
    Args:
        spotify_tracks: List of Spotify track dictionaries
        youtube_client: YouTubeClient instance
        progress_callback: Optional callback function(current, total, track_name, status)
        
    Returns:
        Dictionary with migration statistics
    """
    results = {
        'total': len(spotify_tracks),
        'matched': 0,
        'unmatched': 0,
        'videoIds': [],
        'unmatched_tracks': []
    }
    
    for i, track in enumerate(spotify_tracks):
        track_name = f"{track['title']} - {track['artist']}"
        
        if progress_callback:
            progress_callback(i + 1, len(spotify_tracks), track_name, 'searching')
        
        video_id = find_youtube_match(track, youtube_client)
        
        if video_id:
            results['videoIds'].append(video_id)
            results['matched'] += 1
            
            if progress_callback:
                progress_callback(i + 1, len(spotify_tracks), track_name, 'matched')
        else:
            results['unmatched'] += 1
            results['unmatched_tracks'].append(track_name)
            
            if progress_callback:
                progress_callback(i + 1, len(spotify_tracks), track_name, 'unmatched')
    
    return results
