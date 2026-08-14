#!/usr/bin/env python3
"""Create an intersection playlist with the common tracks of the provided playlists."""

import argparse
import logging
from argparse import Namespace
from pathlib import Path

import yaml
from pydantic import BaseModel
from spotipy import Spotify

from scripts.helpers import create_playlist, get_spotify_client, get_tracks

PERMISSIONS = "playlist-read-private playlist-read-collaborative playlist-modify-public"

_logger = logging.getLogger(__name__)


class PlaylistIntersectionConfig(BaseModel):
    """Configuration for the playlist intersection script."""

    output_playlist_name: str
    """Name of the playlist to create."""
    playlist_urls: list[str]
    """Playlist URLs to intersect."""
    setminus_playlist_url: str | None = None
    """Optional playlist URL to subtract from the intersection."""


def main() -> None:
    """Run the script."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args()
    spotify_client = get_spotify_client(PERMISSIONS)
    config = get_config(args)
    intersection_track_uris = get_intersection_track_uris(
        config.playlist_urls,
        config.setminus_playlist_url,
        spotify_client,
    )
    create_playlist(
        config.output_playlist_name,
        intersection_track_uris,
        spotify_client,
        _logger,
    )


def parse_args() -> Namespace:
    """Parse CLI arguments.

    :returns: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        dest="config_path",
        type=Path,
        default=None,
        nargs="?",
        help="Path to the YAML config file.",
    )
    return parser.parse_args()


def get_config(args: Namespace) -> PlaylistIntersectionConfig:
    """Load configuration from a YAML file or prompt interactively.

    :param args: Parsed command-line arguments.
    :returns: Validated script configuration.
    :raises ValueError: If the config file contents do not match
        :class:`PlaylistIntersectionConfig`.
    """
    if args.config_path:
        return PlaylistIntersectionConfig.model_validate(
            yaml.safe_load(args.config_path.read_text()),
        )
    print(  # noqa: T201
        "Paste the URLs to the playlists you want the intersection of",
        "(paste + ENTER to add, ENTER to continue):",
    )
    playlist_urls = []
    while True:
        if url := input():
            playlist_urls.append(url)
        else:
            break
    return PlaylistIntersectionConfig(
        output_playlist_name=input("Name the output playlist: "),
        playlist_urls=playlist_urls,
        setminus_playlist_url=None,
    )


def get_intersection_track_uris(
    playlist_urls: list[str],
    setminus_playlist_url: str | None,
    spotify_client: Spotify,
) -> list[str]:
    """Compute the intersection of multiple playlists and return URIs.

    Tracks are compared using :class:`Track` semantics (main artist + name).
    If ``setminus_playlist_url`` is provided, its tracks are removed from the
    intersection.

    :param playlist_urls: Playlist URLs to intersect.
    :param setminus_playlist_url: Optional playlist URL whose tracks should
        be removed from the result.
    :param spotify_client: Authenticated Spotify client.
    :returns: Sorted track URIs from the intersection.
    """
    if not playlist_urls:
        return []
    _logger.info("Reading playlists")
    tracks_by_playlist = [
        get_tracks(playlist_url, spotify_client) for playlist_url in playlist_urls
    ]
    _logger.info("Computing intersection")
    intersection_tracks = set.intersection(*tracks_by_playlist)
    if setminus_playlist_url:
        intersection_tracks -= get_tracks(setminus_playlist_url, spotify_client)
    return [track.uri for track in sorted(intersection_tracks)]


if __name__ == "__main__":
    main()
