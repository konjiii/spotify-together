# SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET needed and everyone needs the same redirect_uri = "http://127.0.0.1:9090/callback"

import os
import spotipy
from dotenv import load_dotenv
from spotipy.cache_handler import CacheFileHandler
from spotipy.oauth2 import SpotifyOAuth
from threading import Event


load_dotenv()

redirect_uri = "http://127.0.0.1:9090/callback"
scope = "user-read-playback-state,user-modify-playback-state"

cache_handler = CacheFileHandler(username=os.getenv("SPOTIFY_CLIENT_ID"))

auth_manager = SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=redirect_uri,
    scope=scope,
    open_browser=False,
    cache_handler=cache_handler,
)
# authenticate user
sp = spotipy.Spotify(auth_manager=auth_manager)

def get_current_device(currently_listening_to_a_track: bool =True) -> str:
    if not currently_listening_to_a_track:
        raise ValueError("not currently_listening_to_a_track")
    devices = sp.devices()
    for elem in devices["devices"]:
        if elem["is_active"]:
            current_device = elem["id"]
            return current_device
    print("No music is playing, there is no device...")


def add_to_env(current_device:str) -> None: 
    with open(".env", "w") as env_file:
        env_file.write(f"""SPOTIFY_CLIENT_ID = {os.getenv("SPOTIFY_CLIENT_ID")}
SPOTIFY_CLIENT_SECRET = {os.getenv("SPOTIFY_CLIENT_SECRET")}
CURRENT_DEVICE = {current_device}""")
        
# add_to_env(get_current_device())



# get device from .env
current_device = os.getenv("CURRENT_DEVICE")

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
    
    sp.start_playback(uris=[first])

# query = input("query: ")

# play_song(query)

def get_playlist():
    playlists = sp.current_user_playlists(limit=5, offset=0)
    while playlists:
        for i, playlist in enumerate(playlists['items']):
            # print("%4d %s %s" % (i + 1 + playlists['offset'], playlist['uri'],  playlist['name']))
            pass
        if playlists['next']:
            playlists = sp.next(playlists)
        else:
            playlists = None
    return playlist['uri']

def play_playlist(playlist_uri,current_device=current_device):
    play_list = sp.playlist_tracks(playlist_id=playlist_uri)
    tracks = [item["track"]["uri"] for item in play_list["items"]]
    sp.start_playback(device_id=current_device ,uris=tracks)

# play_playlist(get_playlist())

def play_song_from_playlist(playlist_uri:str,idx:int,current_device:int=current_device) -> None:
    """
    Play a song with the corresponding index in a playlist
    """
    try:
        play_list = sp.playlist_tracks(playlist_id=playlist_uri) 
    except:
        raise TypeError("no good url, no playlist found")
    tracks = [item["track"]["uri"] for item in play_list["items"]] # get all songs in a playlist (list)
    if idx >= len(tracks) or idx <0:
        idx = 0
    track = [tracks[idx]]
    sp.start_playback(device_id=current_device ,uris=track)
    
def get_playlist_length(playlist_uri:str):
    """Return: playlist length"""
    try:
        play_list = sp.playlist_tracks(playlist_id=playlist_uri) 
    except:
        raise TypeError("no good url, no playlist found")
    tracks = [item["track"]["uri"] for item in play_list["items"]] # get all songs in a playlist (list)
    return len(tracks)

def get_uri(url: str) -> list:
    qm = url.find("?")
    if qm == -1:
        qm = None
    slash = url.rfind("/")

    return "spotify:playlist:" + url[slash + 1 : qm]

def get_current_duration_and_trackname(display=False) -> float:
    current = sp.current_playback()
    if current and current.get("item"):
        track = current["item"]
        duration_ms = track["duration_ms"]
        duration_sec = duration_ms / 1000
        if display:
            print(f"Current song: {track['name']}")
            print(f"Duration: {duration_sec:.3f} seconds")
        return duration_sec
    else:
        print("No track currently playing.")

# duration_sec = get_current_duration_and_trackname()
# print(type(duration_sec))

exit = Event()

import threading
from threading import Event

class MusicPlayer:
    def __init__(self):
        self.index = 0
        self.exit = Event()
        self.active = False
        self.t1 = None

    def loop(self):
        """the song-selection loop, loop through the songs in the playlist"""

        while not self.exit.is_set():
            # playlist_uri = "spotify:playlist:4YApAkBZf2sjhA4FXMoiTU"
            play_song_from_playlist(self.playlist_uri,self.index)
            duration_sec = get_current_duration_and_trackname()
            self.exit.wait(duration_sec)
            self.index += 1
            if self.index >= get_playlist_length(self.playlist_uri):
                self.index = 0


    def choose_playlist(self):
        self.input = input("give playlist url")
        self.playlist_uri = get_uri(self.input)


    def start(self):
        """starts the song-selection loop"""
        self.exit.clear()
        self.t1 = threading.Thread(target=self.loop)
        self.t1.start()
        

    def stop(self):
        """stops the song-selection loop"""
        self.exit.set()
        self.active = False
        if not self.t1 is None:
            self.t1.join()



if __name__ == "__main__":
    app_on=True
    music_start = True
    musicplayer = MusicPlayer()
    musicplayer.choose_playlist()
    musicplayer.start()
    exit.wait(20)
    musicplayer.stop()
    print("done")



