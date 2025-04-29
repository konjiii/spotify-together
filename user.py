from spotipy.cache_handler import CacheFileHandler
from spotipy.oauth2 import SpotifyOAuth


class User:
    def __init__(self, client_id: str, client_secret: str) -> None:
        self.cache_handler = CacheFileHandler(username=client_id)
        self.auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri="http://127.0.0.1:9090/callback",
            scope="user-read-playback-state,user-modify-playback-state",
            open_browser=False,
            cache_handler=self.cache_handler,
        )

    def get_authorize_url(self) -> str:
        return self.auth_manager.get_authorize_url()

    def save_access_token(self, callback_url) -> None:
        code = self.auth_manager.parse_response_code(callback_url)
        token = self.auth_manager.get_access_token(code)
        self.cache_handler.save_token_to_cache(token)
