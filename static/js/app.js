// Application State
const state = {
  spotifyConnected: false,
  youtubeConnected: false,
  playlists: [],
  selectedPlaylistIds: new Set(),
  migrating: false
};

// Initialize app on page load
window.addEventListener('DOMContentLoaded', () => {
  // Check URL parameters for OAuth redirects
  const urlParams = new URLSearchParams(window.location.search);

  if (urlParams.get('spotify') === 'connected') {
    checkSpotifyStatus();
    window.history.replaceState({}, document.title, '/');
  }

  if (urlParams.get('youtube') === 'auth') {
    // Prompt for YouTube Music authentication
    promptYouTubeAuth();
    window.history.replaceState({}, document.title, '/');
  }

  // Check authentication status on load
  checkSpotifyStatus();
  checkYouTubeStatus();
});

// Spotify Functions
function connectSpotify() {
  window.location.href = '/auth/spotify';
}

async function checkSpotifyStatus() {
  try {
    const response = await fetch('/api/spotify/status');
    const data = await response.json();

    if (data.authenticated) {
      state.spotifyConnected = true;
      updateSpotifyUI(true, data.user.name);
      loadSpotifyPlaylists();
    } else {
      updateSpotifyUI(false);
    }
  } catch (error) {
    console.error('Error checking Spotify status:', error);
    updateSpotifyUI(false);
  }
}

function updateSpotifyUI(connected, userName = '') {
  const statusEl = document.getElementById('spotify-status');
  const authSection = document.getElementById('spotify-auth-section');
  const playlistsSection = document.getElementById('spotify-playlists-section');

  if (connected) {
    statusEl.innerHTML = `
            <span class="status status-connected">
                <span class="status-dot"></span>
                Connected${userName ? ` as ${userName}` : ''}
            </span>
        `;
    authSection.style.display = 'none';
    playlistsSection.style.display = 'block';
  } else {
    statusEl.innerHTML = `
            <span class="status status-disconnected">
                <span class="status-dot"></span>
                Disconnected
            </span>
        `;
    authSection.style.display = 'block';
    playlistsSection.style.display = 'none';
  }

  updateMigrateButton();
}

async function loadSpotifyPlaylists() {
  try {
    const response = await fetch('/api/spotify/playlists');
    const data = await response.json();

    if (data.playlists) {
      state.playlists = data.playlists;
      renderPlaylists(data.playlists);
    }
  } catch (error) {
    console.error('Error loading playlists:', error);
    document.getElementById('playlist-count').textContent = 'Error loading playlists';
  }
}

function renderPlaylists(playlists) {
  const listEl = document.getElementById('playlist-list');
  const countEl = document.getElementById('playlist-count');

  countEl.textContent = `${playlists.length} playlist${playlists.length !== 1 ? 's' : ''} found`;

  if (playlists.length === 0) {
    listEl.innerHTML = '<div class="empty-state">No playlists found</div>';
    return;
  }

  listEl.innerHTML = playlists.map(playlist => `
        <div class="playlist-item" onclick="togglePlaylist('${playlist.id}')" id="playlist-${playlist.id}">
            <input 
                type="checkbox" 
                class="playlist-checkbox" 
                id="checkbox-${playlist.id}"
                onclick="event.stopPropagation(); togglePlaylist('${playlist.id}')"
            >
            <div class="playlist-info">
                <div class="playlist-name">${escapeHtml(playlist.name)}</div>
                <div class="playlist-meta">${playlist.track_count} tracks</div>
            </div>
        </div>
    `).join('');
}

function togglePlaylist(playlistId) {
  const checkbox = document.getElementById(`checkbox-${playlistId}`);
  const item = document.getElementById(`playlist-${playlistId}`);

  if (state.selectedPlaylistIds.has(playlistId)) {
    state.selectedPlaylistIds.delete(playlistId);
    checkbox.checked = false;
    item.classList.remove('selected');
  } else {
    state.selectedPlaylistIds.add(playlistId);
    checkbox.checked = true;
    item.classList.add('selected');
  }

  updateSelectionCount();
  updateMigrateButton();
}

function selectAll() {
  const allSelected = state.selectedPlaylistIds.size === state.playlists.length;

  if (allSelected) {
    // Deselect all
    state.selectedPlaylistIds.clear();
    state.playlists.forEach(p => {
      const checkbox = document.getElementById(`checkbox-${p.id}`);
      const item = document.getElementById(`playlist-${p.id}`);
      if (checkbox) checkbox.checked = false;
      if (item) item.classList.remove('selected');
    });
    document.getElementById('select-all-btn').querySelector('span').textContent = 'Select All';
  } else {
    // Select all
    state.playlists.forEach(p => {
      state.selectedPlaylistIds.add(p.id);
      const checkbox = document.getElementById(`checkbox-${p.id}`);
      const item = document.getElementById(`playlist-${p.id}`);
      if (checkbox) checkbox.checked = true;
      if (item) item.classList.add('selected');
    });
    document.getElementById('select-all-btn').querySelector('span').textContent = 'Deselect All';
  }

  updateSelectionCount();
  updateMigrateButton();
}

function updateSelectionCount() {
  document.getElementById('selection-count').textContent = state.selectedPlaylistIds.size;
}

// YouTube Music Functions
function connectYouTube() {
  window.location.href = '/auth/youtube';
}

async function promptYouTubeAuth() {
  const confirmed = confirm(
    'YouTube Music authentication requires OAuth setup.\n\n' +
    'This will open a new window for authentication. Continue?'
  );

  if (confirmed) {
    try {
      const response = await fetch('/api/youtube/authenticate', {
        method: 'POST'
      });

      if (response.ok) {
        state.youtubeConnected = true;
        updateYouTubeUI(true);
      } else {
        alert('YouTube Music authentication failed. Please check console for details.');
      }
    } catch (error) {
      console.error('Error authenticating with YouTube:', error);
      alert('Authentication error. See console for details.');
    }
  }
}

async function checkYouTubeStatus() {
  try {
    const response = await fetch('/api/youtube/status');
    const data = await response.json();

    if (data.authenticated) {
      state.youtubeConnected = true;
      updateYouTubeUI(true);
    } else {
      updateYouTubeUI(false);
    }
  } catch (error) {
    console.error('Error checking YouTube status:', error);
    updateYouTubeUI(false);
  }
}

function updateYouTubeUI(connected) {
  const statusEl = document.getElementById('youtube-status');
  const authSection = document.getElementById('youtube-auth-section');
  const readySection = document.getElementById('youtube-ready-section');

  if (connected) {
    statusEl.innerHTML = `
            <span class="status status-connected">
                <span class="status-dot"></span>
                Connected
            </span>
        `;
    authSection.style.display = 'none';
    readySection.style.display = 'block';
  } else {
    statusEl.innerHTML = `
            <span class="status status-disconnected">
                <span class="status-dot"></span>
                Disconnected
            </span>
        `;
    authSection.style.display = 'block';
    readySection.style.display = 'none';
  }

  updateMigrateButton();
}

// Migration Functions
function updateMigrateButton() {
  const btn = document.getElementById('migrate-btn');
  const canMigrate = state.spotifyConnected &&
    state.youtubeConnected &&
    state.selectedPlaylistIds.size > 0 &&
    !state.migrating;

  btn.disabled = !canMigrate;
}

async function startMigration() {
  if (state.migrating) return;

  const count = state.selectedPlaylistIds.size;
  const confirmed = confirm(
    `You are about to migrate ${count} playlist${count !== 1 ? 's' : ''} to YouTube Music.\n\n` +
    'This may take several minutes. Continue?'
  );

  if (!confirmed) return;

  state.migrating = true;
  updateMigrateButton();

  // Show progress section
  const progressSection = document.getElementById('progress-section');
  progressSection.classList.add('active');

  // Reset progress
  document.getElementById('current-playlist').textContent = '0';
  document.getElementById('matched-tracks').textContent = '0';
  document.getElementById('unmatched-tracks').textContent = '0';
  document.getElementById('progress-log').innerHTML = '';

  try {
    const response = await fetch('/api/migrate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        playlist_ids: Array.from(state.selectedPlaylistIds)
      })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let totalPlaylists = 0;
    let currentPlaylist = 0;
    let totalMatched = 0;
    let totalUnmatched = 0;

    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.substring(6));

          switch (data.type) {
            case 'start':
              totalPlaylists = data.total_playlists;
              document.getElementById('total-playlists').textContent = totalPlaylists;
              addLogEntry('🚀 Starting migration...', 'info');
              break;

            case 'playlist_start':
              currentPlaylist = data.index + 1;
              document.getElementById('current-playlist').textContent = currentPlaylist;
              addLogEntry(`📂 Migrating: ${data.playlist.name}`, 'info');
              break;

            case 'tracks_loaded':
              addLogEntry(`📥 Loaded ${data.count} tracks`, 'info');
              break;

            case 'playlist_created':
              addLogEntry('✅ Playlist created on YouTube Music', 'info');
              break;

            case 'track_progress':
              if (data.status === 'matched') {
                totalMatched++;
                document.getElementById('matched-tracks').textContent = totalMatched;
                addLogEntry(`✅ ${data.track_name}`, 'matched');
              } else if (data.status === 'unmatched') {
                totalUnmatched++;
                document.getElementById('unmatched-tracks').textContent = totalUnmatched;
                addLogEntry(`❌ ${data.track_name}`, 'unmatched');
              } else if (data.status === 'searching') {
                addLogEntry(`🔍 ${data.track_name}`, 'searching');
              }
              break;

            case 'playlist_complete':
              addLogEntry(`✨ Playlist complete! ${data.matched} matched, ${data.unmatched} unmatched`, 'info');
              break;

            case 'complete':
              addLogEntry('🎉 Migration complete!', 'info');
              document.getElementById('progress-title').textContent = 'Migration Complete!';
              state.migrating = false;
              updateMigrateButton();
              break;

            case 'error':
              addLogEntry(`❌ Error: ${data.message}`, 'unmatched');
              state.migrating = false;
              updateMigrateButton();
              break;
          }
        }
      }
    }
  } catch (error) {
    console.error('Migration error:', error);
    addLogEntry(`❌ Error: ${error.message}`, 'unmatched');
    state.migrating = false;
    updateMigrateButton();
  }
}

function addLogEntry(message, type = 'info') {
  const logEl = document.getElementById('progress-log');
  const entry = document.createElement('div');
  entry.className = `log-entry ${type}`;
  entry.textContent = message;
  logEl.appendChild(entry);

  // Auto-scroll to bottom
  logEl.scrollTop = logEl.scrollHeight;

  // Keep only last 100 entries
  while (logEl.children.length > 100) {
    logEl.removeChild(logEl.firstChild);
  }
}

// Utility Functions
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
