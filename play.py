import sqlite3
import threading

import spotipy
from spotipy.cache_handler import CacheFileHandler
from spotipy.oauth2 import SpotifyOAuth

con = sqlite3.connect("secret_sharing_is_caring.db")
cur = con.cursor()
res = cur.execute("SELECT * FROM users")
user_data = res.fetchall()

redirect_uri = "http://127.0.0.1:9090/callback"
scope = "user-read-playback-state,user-modify-playback-state"

auth_managers = []
sp_list = []

for user in user_data:
    username = user[0]
    client_id = user[1]
    client_secret = user[2]
    curr_device = user[3]

    cache_handler = CacheFileHandler(username=username)

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        open_browser=False,
        cache_handler=cache_handler,
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)

    auth_managers.append(auth_manager)
    sp_list.append(sp)


def start_playback_threaded(sp_obj, device_id, uri):
    """Helper function to start playback in a thread."""
    try:
        sp_obj.start_playback(device_id=device_id, uris=[uri])
        print(f"Started playback on device {device_id}")  # Optional: Add some feedback
    except Exception as e:
        print(
            f"Error starting playback on device {device_id}: {e}"
        )  # Optional: Add error handling


def play_song(query: str) -> None:
    results = sp.search(query)
    if results is None:
        print("No results found.")  # Added feedback for no results
        return

    tracks = results["tracks"]["items"]

    if not tracks:  # Added check if tracks list is empty
        print("No tracks found in results.")
        return

    print("Found Tracks:")  # Added header for clarity
    for track in tracks:
        print("################")
        print(f"Name: {track['name']}")  # Formatted output
        print(f"URI: {track['uri']}")  # Formatted output

    first = tracks[0]["uri"]

    threads = []
    for i in range(len(sp_list)):
        sp_obj = sp_list[i]
        device_id = user_data[i][3]
        uri = first
        thread = threading.Thread(
            target=start_playback_threaded, args=(sp_obj, device_id, uri)
        )
        threads.append(thread)

    for thread in threads:
        thread.start()

    # Optional: Wait for all threads to complete if needed
    for thread in threads:
        thread.join()


query = input("query: ")

play_song(query)
