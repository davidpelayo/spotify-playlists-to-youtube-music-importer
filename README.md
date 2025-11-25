# Spotify to YouTube Music Playlist Migrator

Migrate your playlists from Spotify to YouTube Music with ease! This tool provides both a command-line interface for automated migration and a beautiful web application with a side-by-side interface.

## Features

- 🎵 **CLI Script**: Automated playlist migration from command line
- 🌐 **Web Application**: Visual interface showing Spotify playlists on the left, YouTube Music on the right
- ✅ **Selective Migration**: Choose which playlists to migrate
- 🔍 **Smart Matching**: Intelligent song matching between platforms
- 📊 **Progress Tracking**: Real-time migration status updates
- 🎨 **Premium Design**: Modern, dark-mode interface with smooth animations

## Prerequisites

- Python 3.8 or higher
- Spotify account
- YouTube Music account (YouTube Premium subscription)
- Spotify Developer Account
- Google Cloud Account

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click "Create App"
3. Fill in the app details:
   - App name: "Playlist Migrator" (or any name)
   - App description: "Migrate playlists to YouTube Music"
   - Redirect URI: `http://127.0.0.1:5000/auth/spotify/callback` ⚠️ **Must be HTTPS**
4. Save your **Client ID** and **Client Secret**

### 3. YouTube Music API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **YouTube Data API v3**:
   - Go to "APIs & Services" → "Library"
   - Search for "YouTube Data API v3"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "Credentials" → "Create Credentials" → "OAuth client ID"
   - If prompted, configure the OAuth consent screen first (select "External" and fill in required fields)
   - Application type: Select **"Web application"**
   - Name: "YouTube Music Migrator" (or any name)
   - **Authorized redirect URIs**: Add `http://127.0.0.1:5000/auth/youtube/callback`
   - Click "Create"
5. Save your **Client ID** and **Client Secret** for the `.env` file

> **Important:** The redirect URI must match exactly: `http://127.0.0.1:5000/auth/youtube/callback`

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:5000/auth/spotify/callback

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:5000/auth/youtube/callback

FLASK_SECRET_KEY=generate_a_random_secret_key
```

Add the following line to `/etc/hosts`:

```bash
127.0.0.1 playlists.migrator
```

### 5. Generate SSL Certificates

**Important:** Spotify requires HTTPS for OAuth callbacks. Generate self-signed certificates:

```bash
python3 generate_cert.py
```

This creates `cert.pem` and `key.pem` for local HTTPS development.

> **Note:** Your browser will show a security warning when accessing `http://127.0.0.1:5000`. This is normal for self-signed certificates. Click "Advanced" → "Proceed to localhost" to continue.

## Usage

### CLI Script

Run the command-line migration tool:

```bash
python migrate.py
```

Follow the interactive prompts to:
1. Authenticate with Spotify
2. View your playlists
3. Select playlists to migrate
4. Authenticate with YouTube Music
5. Start migration

### Web Application

Launch the web application:

```bash
python app.py
```

The app will automatically generate SSL certificates if they don't exist.

Then open your browser to `http://127.0.0.1:5000`

> **Browser Security Warning:** You'll see a warning about the self-signed certificate. Click "Advanced" and "Proceed to localhost (unsafe)" - this is safe for local development.

1. Click "Connect Spotify" and authorize the app
2. Your Spotify playlists will appear on the left side
3. Click "Connect YouTube Music" and authorize the app
4. Select playlists you want to migrate using checkboxes
5. Click "Migrate Selected Playlists"
6. Watch real-time progress as your playlists are migrated!

## How It Works

1. **Spotify Integration**: Uses the official Spotify Web API via `spotipy` to fetch your playlists and track information
2. **YouTube Music Integration**: Uses the official Google YouTube Data API v3 via `google-api-python-client` to create playlists and add songs
3. **Smart Matching**: For each Spotify track, the tool searches YouTube Music using song title and artist name, then selects the best match
4. **Error Handling**: If a song can't be found, it's logged and skipped, allowing the migration to continue

## Authentication Flow

### First-Time YouTube Setup

When you first authenticate with YouTube:

1. The app will open a browser window for Google OAuth
2. Sign in with your Google account
3. Grant the requested permissions (YouTube data access)
4. A `token.json` file will be created automatically in the project directory
5. This token will be used for future requests and will auto-refresh when needed

> **Note:** The `token.json` file is gitignored and contains your OAuth credentials. Keep it secure and never commit it to version control.

## Verification

To verify everything is working correctly:

```bash
python3 diagnose_youtube.py
```

This diagnostic script will:
- Check for the presence of `token.json`
- Verify authentication with YouTube
- Test playlist fetching
- Create and delete a test playlist

If all checks pass, you're ready to migrate playlists!

## Limitations

- Song matching is based on title and artist; some songs may not match perfectly
- YouTube Premium subscription is recommended for best results
- YouTube Data API v3 has daily quota limits (10,000 units per day by default)
- Rate limiting may occur with very large playlists

## Troubleshooting

### "Invalid client" error
- Double-check your Client ID and Client Secret in `.env`
- Ensure redirect URIs match exactly in both the `.env` file and the app settings
- **Verify redirect URI uses HTTPS:** `http://127.0.0.1:5000/auth/spotify/callback`

### Browser security warning
- This is expected with self-signed certificates
- Click "Advanced" → "Proceed to localhost" to continue
- The warning appears only once per browser session

### Songs not matching
- The tool uses fuzzy matching, but some songs may not be available on YouTube Music
- Check the migration logs for details on unmatched songs

### OAuth errors
- Make sure you've enabled the YouTube Data API v3 in Google Cloud Console
- Verify you selected "Web application" for the OAuth client type
- Ensure the redirect URI is exactly: `http://127.0.0.1:5000/auth/youtube/callback`
- Check that `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correctly set in `.env`
- If `token.json` exists but authentication fails, delete it and re-authenticate

## License

MIT License - feel free to use and modify as needed!

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This tool is not affiliated with Spotify or YouTube. Use at your own risk. Make sure to review YouTube Data API's terms of service and quota limits before heavy usage.
