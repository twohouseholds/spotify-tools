"""Output the count of songs per artist in a provided playlist (ascending order).

A song is only attributed to its main artist.
"""

from collections import Counter

from scripts.helpers import get_spotify_client, get_tracks

PERMISSIONS = "playlist-read-private playlist-read-collaborative"


def main() -> None:
    """Run the script."""
    playlist_url = input(
        "URL to the playlist you want the artist count of (paste + ENTER): ",
    )
    spotify_client = get_spotify_client(PERMISSIONS)
    tracks = get_tracks(playlist_url, spotify_client)
    main_artists = [track.main_artist for track in tracks]
    artist_counts = Counter(main_artists)
    for artist, count in reversed(artist_counts.most_common()):
        print(f"{artist}: {count}")  # noqa: T201


if __name__ == "__main__":
    main()
