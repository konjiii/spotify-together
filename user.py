import sys

import spotipy
from spotipy.cache_handler import CacheFileHandler
from spotipy.oauth2 import SpotifyOAuth

from database import get_db_users


class User:
    def __init__(self, client_id: str, client_secret: str, username: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.curr_device = None
        self.cache_handler = CacheFileHandler(username=username)
        self.auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri="http://127.0.0.1:9090/callback",
            scope="user-read-playback-state,user-modify-playback-state",
            open_browser=False,
            cache_handler=self.cache_handler,
        )
        self.sp = spotipy.Spotify(auth_manager=self.auth_manager)

    def get_authorize_url(self) -> str:
        return self.auth_manager.get_authorize_url()

    def save_access_token(self, callback_url) -> None:
        code = self.auth_manager.parse_response_code(callback_url)
        token = self.auth_manager.get_access_token(code)
        self.cache_handler.save_token_to_cache(token)

    def get_current_device(self) -> str | None:
        currently_listening_to_a_track = self.sp.currently_playing()

        if not currently_listening_to_a_track:
            print("not currently_listening_to_a_track", file=sys.stderr)
            return
        devices = self.sp.devices()
        for elem in devices["devices"]:
            if elem["is_active"]:
                current_device = elem["id"]
                self.curr_device = current_device
                return current_device
        print("No music is playing, there is no device...", file=sys.stderr)

    def __repr__(self):
        return f"User(client_id: {self.client_id}, client_secret: {self.client_secret})"


def get_users() -> dict[str, User]:
    """
    gets the users from the database and creates a dictionary

    params:
        None
    returns:
        dictionary: key = username, value = User() instance
    """
    users = dict()

    # username | client_id | client_secret | device
    data = get_db_users()

    if data is None:
        raise ValueError("failed to get users")

    for entry in data:
        users[entry[0]] = User(entry[1], entry[2], entry[0])

    return users
