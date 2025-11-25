# Release Notes

## Version 1.0.0 - Initial Release
**Release Date:** November 25, 2024

### 🎉 Overview

First stable release of the Spotify to YouTube Music Playlist Migrator! This tool enables seamless migration of your Spotify playlists to YouTube Music through both a web interface and command-line interface.

### ✨ Features

#### Core Functionality
- **Playlist Migration**: Migrate playlists from Spotify to YouTube Music with intelligent song matching
- **Dual Interface**: Choose between a modern web application or CLI script
- **Smart Matching**: Advanced fuzzy matching algorithm with configurable search limits (15 results per song)
- **Real-time Progress**: Live migration status updates via Server-Sent Events in the web app
- **Selective Migration**: Choose which playlists to migrate with checkbox selection

#### Authentication
- **Spotify OAuth**: Standard OAuth 2.0 flow for Spotify authentication
- **YouTube OAuth**: Web Application OAuth flow using official YouTube Data API v3
- **Token Management**: Automatic token refresh and persistent authentication via `token.json`

#### Web Application
- **Modern UI**: Clean, responsive interface with side-by-side playlist view
- **Progress Tracking**: Real-time track-by-track migration status
- **Error Handling**: Graceful handling of unmatched songs with detailed logging

#### CLI Script
- **Interactive Mode**: Step-by-step guided migration process
- **Batch Processing**: Migrate multiple playlists in one session
- **Progress Indicators**: Clear console output with migration statistics

### 🔧 Technical Details

#### APIs & Libraries
- **Spotify Integration**: Official Spotify Web API via `spotipy`
- **YouTube Integration**: Official YouTube Data API v3 via `google-api-python-client`
- **Authentication**: `google-auth-oauthlib` for OAuth 2.0 flows
- **Web Framework**: Flask with Server-Sent Events for real-time updates

#### Configuration
- **Environment Variables**: All credentials managed via `.env` file
- **HTTP Support**: Simplified setup with HTTP (no SSL certificates required)
- **Flexible Redirect URIs**: Configurable OAuth redirect URIs for both Spotify and YouTube

### 📋 Requirements

- Python 3.8 or higher
- Spotify account
- YouTube/Google account
- Spotify Developer credentials
- Google Cloud project with YouTube Data API v3 enabled

### 🚀 Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure OAuth credentials in Google Cloud Console and Spotify Developer Dashboard
4. Set up `.env` file with your credentials
5. Run the web app: `python3 app.py` or CLI: `python3 migrate.py`

### ⚙️ Configuration Highlights

**Default Settings:**
- Search limit: 15 results per song (increased for better matching)
- Playlist privacy: Private by default
- Server: HTTP on `127.0.0.1:5000`
- OAuth redirect URIs: `http://127.0.0.1:5000/auth/{spotify|youtube}/callback`

### 📊 API Quota Considerations

**YouTube Data API v3 Quotas:**
- Default daily quota: 10,000 units
- Search operation: ~100 units per request
- Playlist creation: ~50 units
- Add to playlist: ~50 units per song

**Estimated Capacity:**
- ~50-100 songs per day with default quota
- Consider requesting quota increase for large migrations

### 🐛 Known Limitations

1. **API Quota**: YouTube Data API v3 has daily quota limits that may restrict large migrations
2. **Matching Accuracy**: Song matching is based on title and artist; some songs may not match perfectly
3. **Rate Limiting**: Large playlists may hit rate limits
4. **YouTube Premium**: Recommended for best results

### 🔒 Security

- All OAuth credentials stored in `.env` file (gitignored)
- Token files (`token.json`) automatically managed and gitignored
- No hardcoded credentials in source code
- Secure OAuth 2.0 flows for both Spotify and YouTube

### 📝 License

GNU General Public License v3.0 (GPLv3)

### 🙏 Acknowledgments

- Built with official Spotify Web API and YouTube Data API v3
- Uses `spotipy` for Spotify integration
- Uses `google-api-python-client` for YouTube integration

### 📖 Documentation

Full documentation available in [README.md](README.md)

### 🔄 Migration from Beta

This is the first stable release. No migration steps required.

---

**Download:** [Release v1.0.0](https://github.com/nexoapex/playlists/releases/tag/v1.0.0)

**Feedback:** Please report issues on [GitHub Issues](https://github.com/nexoapex/playlists/issues)
