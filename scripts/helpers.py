"""Common helper functions used in the tool's scripts."""

import os
import re
from dataclasses import dataclass
from functools import total_ordering
from logging import Logger
from typing import Any, cast, override

from spotipy import Spotify, SpotifyOAuth

PERMISSIONS = "playlist-read-private playlist-read-collaborative playlist-modify-public"
REDIRECT_URI = "http://127.0.0.1:8888/callback"


def extract_playlist_id(playlist_url: str) -> str:
    """Extract the playlist ID from a playlist URL.

    Accepts typical ``open.spotify.com/playlist/<id>`` URLs.

    :param playlist_url: The playlist URL.
    :returns: The playlist identifier.
    :raises ValueError: If the URL does not contain a valid playlist ID.
    """
    match = re.search("open.spotify.com/playlist/([a-zA-Z0-9]+)", playlist_url)
    if not match:
        msg = f"{playlist_url} is not a valid playlist URL"
        raise ValueError(msg)
    return match.group(1)


def get_spotify_client() -> Spotify:
    """Create an authenticated Spotify client.

    The client is configured using environment variables.

    :returns: An authenticated Spotify client.
    :raises ValueError: If either required environment variable is missing.
    """
    if not (client_id := os.getenv("SPOTIFY_CLIENT_ID")):
        msg = "Environment variable 'SPOTIFY_CLIENT_ID' is not set."
        raise ValueError(msg)
    if not (client_secret := os.getenv("SPOTIFY_CLIENT_SECRET")):
        msg = "Environment variable 'SPOTIFY_CLIENT_SECRET' is not set."
        raise ValueError(msg)
    return Spotify(
        auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=REDIRECT_URI,
            scope=PERMISSIONS,
        ),
    )


@dataclass(frozen=True)
@total_ordering
class Track:
    """Track in a playlist."""

    uri: str
    """Track URI."""
    name: str
    """Track name."""
    main_artist: str
    """Primary artist name."""

    @override
    def __eq__(self, other: object) -> bool:
        """Compare tracks by main artist and name only.

        :param other: Object to compare against.
        :returns: ``True`` when both tracks share the same main artist and
            name.
        """
        if not isinstance(other, Track):
            return NotImplemented
        return self.main_artist == other.main_artist and self.name == other.name

    @override
    def __hash__(self) -> int:
        """Hash tracks by main artist and name only.

        :returns: Hash value derived from main artist and track name.
        """
        return hash((self.main_artist, self.name))

    def __lt__(self, other: object) -> bool:
        """Compare tracks by main artist, then by name.

        :param other: Object to compare against.
        :returns: ``True`` when this track sorts before ``other``.
        """
        if not isinstance(other, Track):
            return NotImplemented
        if self.main_artist == other.main_artist:
            return self.name.lower() < other.name.lower()
        return self.main_artist.lower() < other.main_artist.lower()


def get_tracks(
    playlist_url: str,
    spotify_client: Spotify,
) -> set[Track]:
    """Fetch all tracks from a playlist.

    The Spotify Web API paginates playlist tracks; this function requests
    pages of up to 100 items until no more pages remain. Each returned item
    is normalized into a :class:`Track` instance.

    :param playlist_url: Playlist URL.
    :param spotify_client: Authenticated Spotify client.
    :returns: Unique tracks from the playlist.
    :raises ValueError: If ``playlist_url`` does not contain a valid playlist
        identifier.
    """
    tracks: set[Track] = set()
    playlist_id = extract_playlist_id(playlist_url)
    offset = 0
    limit = 100
    has_next_page = True
    while has_next_page:
        raw_items = cast(
            "dict[str, Any]",
            spotify_client.playlist_tracks(playlist_id, offset=offset, limit=limit),
        )
        items = cast("list[dict[str,Any]]", raw_items["items"])
        for item_dict in items:
            item = cast("dict[str, Any]", item_dict["item"])
            uri = str(item["uri"])
            name = re.sub(r" \(feat\. .*\)", "", item["name"])
            artist_dicts = cast("list[dict[str, Any]]", item["artists"])
            main_artist = str(artist_dicts[0]["name"])
            tracks.add(
                Track(
                    uri=uri,
                    name=name,
                    main_artist=main_artist,
                ),
            )
        has_next_page = len(items) == limit
        offset += limit
    return tracks


def create_playlist(
    name: str,
    track_uris: list[str],
    spotify_client: Spotify,
    logger: Logger,
) -> None:
    """Create a playlist and add tracks to it.

    :param name: Name of the playlist to create.
    :param track_uris: Track URIs to add to the playlist.
    :param spotify_client: Authenticated Spotify client.
    :returns: None.
    """
    logger.info("Creating playlist '%s'", name)
    response_dict = cast(
        "dict[str, Any]",
        spotify_client.current_user_playlist_create(name),
    )
    playlist_id = str(response_dict["id"])
    for offset in range(0, len(track_uris), 100):
        spotify_client.playlist_add_items(
            playlist_id,
            track_uris[offset : offset + 100],
        )
