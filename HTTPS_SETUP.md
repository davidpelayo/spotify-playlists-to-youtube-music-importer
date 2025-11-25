# HTTPS Configuration Update

## Changes Made

### ✅ Self-Signed SSL Certificate Generation

Created [generate_cert.py](file:///Users/davidpelayo/Projects/github/nexoapex/playlists/generate_cert.py) to automatically generate SSL certificates for local HTTPS development.

**Features:**
- Generates RSA 2048-bit key pair
- Creates X.509 certificate valid for 1 year
- Includes Subject Alternative Names (localhost, 127.0.0.1)
- Interactive prompts if certificates already exist
- Clear user instructions

### ✅ Flask Application Updates

Updated [app.py](file:///Users/davidpelayo/Projects/github/nexoapex/playlists/app.py) to run with HTTPS:

**Changes:**
- Auto-generates SSL certificates if missing
- Runs Flask with SSL context `(cert.pem, key.pem)`
- User-friendly startup messages explaining the self-signed certificate warning
- Server now runs at `https://playlists.migrate:5000`

### ✅ Configuration Updates

**Environment Variables** ([.env.example](file:///Users/davidpelayo/Projects/github/nexoapex/playlists/.env.example)):
- `SPOTIFY_REDIRECT_URI`: Changed from `http://` to `https://playlists.migrate:5000/auth/spotify/callback`
- `YOUTUBE_REDIRECT_URI`: Changed from `http://` to `https://playlists.migrate:5000/auth/youtube/callback`

**Dependencies** ([requirements.txt](file:///Users/davidpelayo/Projects/github/nexoapex/playlists/requirements.txt)):
- Added `pyopenssl==24.0.0` for SSL certificate generation

**Git Ignore** ([.gitignore](file:///Users/davidpelayo/Projects/github/nexoapex/playlists/.gitignore)):
- Added `cert.pem` and `key.pem` to prevent committing certificates

### ✅ Documentation Updates

Updated [README.md](file:///Users/davidpelayo/Projects/github/nexoapex/playlists/README.md):

1. **Setup Section**: Added step 5 for SSL certificate generation
2. **Spotify Credentials**: Emphasized HTTPS requirement for redirect URI
3. **Web App Usage**: Updated URL to `https://playlists.migrate:5000`
4. **Browser Warning**: Added clear explanation about self-signed certificate security warnings
5. **Troubleshooting**: Added section on browser security warnings

## How It Works

1. **First Run**: When you start `python app.py`, it checks for SSL certificates
2. **Auto-Generation**: If certificates don't exist, it runs `generate_cert.py` automatically
3. **HTTPS Server**: Flask starts with SSL context on `https://playlists.migrate:5000`
4. **Browser Warning**: Users will see a security warning (expected with self-signed certs)
5. **OAuth Flow**: Spotify OAuth works correctly with HTTPS callback

## User Instructions

### Initial Setup
```bash
# Install dependencies (includes pyopenssl)
pip install -r requirements.txt

# Generate SSL certificates (optional - app does this automatically)
python3 generate_cert.py
```

### Configure Spotify App
In your Spotify Developer Dashboard:
- Set Redirect URI to: `https://playlists.migrate:5000/auth/spotify/callback` ⚠️ **Must be HTTPS**

### Start the App
```bash
python app.py
```

Visit `https://playlists.migrate:5000` (note the **https://**)

### Handle Browser Warning
When you first visit the site, you'll see a security warning:

**Chrome/Edge:**
1. Click "Advanced"
2. Click "Proceed to localhost (unsafe)"

**Firefox:**
1. Click "Advanced"
2. Click "Accept the Risk and Continue"

**Safari:**
1. Click "Show Details"
2. Click "visit this website"

This is normal and safe for local development with self-signed certificates.

## Why HTTPS is Required

Spotify's OAuth 2.0 implementation requires HTTPS redirect URIs for security reasons, even in local development. This prevents:
- Man-in-the-middle attacks
- Token interception
- Unauthorized access

Self-signed certificates are the standard solution for local HTTPS development.
