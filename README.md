# Spotify Tools

Tools for Spotify features that are currently not supported.

## Setup

1. Clone the repository.
2. Install Python 3.12 or newer.
3. Install `uv` (e.g., via `winget install --id=astral-sh.uv  -e`).
4. Switch to the directory of the clone and run `uv sync`.
5. Rename `.env.template` to `.env` and enter your Spotify Web API credentials:
   1. Log in to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
   2. Create an app with the `Redirect URIs` set to `http://127.0.0.1:8888/callback` and `Which API/SDKs are you planning to use?` set to `Web API`.
   3. Copy the `Client ID` and `Client Secret` to the respective environment variables in `.env`.

## Tools

### Playlist Intersection

Create an intersection playlist with the common tracks of the provided playlists.

```bash
uv run --env-file .env -m scripts.playlist_intersection
```

By default, the tool asks for the input configuration details (playlist URLs etc.) via stdin.

The tool can also be configured via a YAML file, though.
This enables additional features like `setminus_playlist_url`.
To do so, provide the path to a config YAML file at the end of the command.

### Playlist Artist Count

Output the count of songs per artist in the provided playlist (descending order).

```bash
uv run --env-file .env -m scripts.playlist_artist_counts
```

The tool asks for the input playlist URL via stdin.

## Troubleshooting

- When running a tool's script for the first time, a browser popup will ask for the necessary Spotify permissions for that tool. This is expected.
- A tool's script may fail with `403 Forbidden`, denying access to a playlist even though said playlist should be accessible through the given Spotify account. In this case, try using a personal copy:
  1. Navigate to the playlist
  2. Click the three dots
  3. `Add to other playlist`
  4. `New playlist`
  5. Use the URL to the personal copy
