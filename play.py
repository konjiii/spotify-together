import os
import sqlite3

import spotipy
from spotipy.cache_handler import CacheFileHandler
from spotipy.oauth2 import SpotifyOAuth

con = sqlite3.connect("secret_sharing_is_caring.db")
cur = con.cursor()
res = cur.execute("SELECT client_id, client_secret FROM users WHERE id='test'")
client_id, client_secret = res.fetchone()

redirect_uri = "http://127.0.0.1:9090/callback"
scope = "user-read-playback-state,user-modify-playback-state"

cache_handler = CacheFileHandler(username=os.getenv("SPOTIFY_CLIENT_ID"))

auth_manager = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    open_browser=False,
    cache_handler=cache_handler,
)
sp = spotipy.Spotify(auth_manager=auth_manager)

devices = sp.devices()
print(devices)
device_id = devices["devices"][0]["id"]


def play_song(query: str) -> None:
    results = sp.search(query)
    if results is None:
        return

    tracks = results["tracks"]["items"]

    for track in tracks:
        print("################")
        print(track["name"])
        print(track["uri"])

    first = tracks[0]["uri"]

    sp.start_playback(device_id=device_id, uris=[first])


query = input("query: ")

play_song(query)
