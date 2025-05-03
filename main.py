# SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET needed and everyone needs the same redirect_uri = "http://127.0.0.1:9090/callback"
import sys
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
    print("No music is playing, there is no device...", file=sys.stderr)


def add_to_env(current_device:str) -> None: 
    with open(".env", "w") as env_file:
        env_file.write(f"""SPOTIFY_CLIENT_ID = {os.getenv("SPOTIFY_CLIENT_ID")}
SPOTIFY_CLIENT_SECRET = {os.getenv("SPOTIFY_CLIENT_SECRET")}
CURRENT_DEVICE = {current_device}""")
        
# add_to_env(get_current_device())

# get device from .env
current_device = os.getenv("CURRENT_DEVICE")
print(current_device)

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
    sp.start_playback(device_id=current_device,uris=[first])

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


def get_playlist_length(playlist_uri:str):
    """Return: playlist length"""
    try:
        play_list = sp.playlist_tracks(playlist_id=playlist_uri) 
    except:
        raise TypeError("no good url, no playlist found")
    tracks = [item["track"]["uri"] for item in play_list["items"]] # get all songs in a playlist (list)
    return len(tracks)

def get_uri(url: str) -> str:
    qm = url.find("?")
    if qm == -1:
        qm = None
    slash = url.rfind("/")

    return "spotify:playlist:" + url[slash + 1 : qm]

def is_playing():
    playback = sp.current_playback()
    if playback and playback['is_playing']:
        return True
    else:
        return False

def play_song_from_playlist(playlist_uri:str,idx:int,current_device:int=current_device, progress_sec:int = 0) -> None:
    """
    Play a song with the corresponding index in a playlist
    """
    try:
        play_list = sp.playlist_tracks(playlist_id=playlist_uri) 
    except:
        raise TypeError("no good url, no playlist found")
    tracks = [item["track"]["uri"] for item in play_list["items"]] # get all songs in a playlist <list>
    if idx >= len(tracks) or idx <0:
        idx = 0
    track = [tracks[idx]]
    
    #hier
    # for user in self.users:
    #     try:
    #         user.sp.start_playback(device_id=current_device ,uris=track, position_ms=progress_sec*1000)
    # except:
    #     print("No device, YOUR SPOTIFY IS CLOSED! OPEN IT NOWWW!!!", file=sys.stderr)

    try:# hier # remove this\/
        sp.start_playback(device_id=current_device ,uris=track, position_ms=progress_sec*1000)
    except:
        print("No device, YOUR SPOTIFY IS CLOSED! OPEN IT NOWWW!!!", file=sys.stderr)
    
def get_playlist_info(playlist_uri:str, display=False):
    """Print all the tracks and artists of the playlist."""
    if display:    
        try:
            results = sp.playlist_items(playlist_uri)
        except:
            raise TypeError("no good url, no playlist found")
        # Extract track names
        tracks = results['items']
        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])
        for idx, playback in enumerate(tracks):
            track = playback['track']
            print(f"{idx+1}. {track['name']} by {track['artists'][0]['name']}")

def get_current_song_info(idx:int=0, display=False, details=False, pause=False) -> float:
    """Get the currently playing song info, return the song duration and where you are in the song
    -------
    Return: duration_sec: float, progress_sec: float"""
    playback = sp.current_playback()
    if playback and playback['is_playing']:
        track = playback['item']
        progress_ms = playback['progress_ms']
        progress_sec = progress_ms / 1000
        duration_ms = track['duration_ms']
        duration_sec = duration_ms / 1000
        song_name = track['name']
        artist_name = track['artists'][0]['name']
        if display:
            if pause:
                print(f"\nNow pausing: {idx+1}. {song_name} by {artist_name}")
            else:
                print(f"\nNow playing: {idx+1}. {song_name} by {artist_name}")
            if details:
                print(f"Progress: {progress_ms / 1000:.2f} seconds")
                print(f"Duration: {duration_sec:.3f} seconds")
        return duration_sec, progress_sec
    else:
        print("No song currently playing",file = sys.stderr)


import threading
from threading import Event

class MusicPlayer:
    def __init__(self):
    # def __init__(self,users):
        # self.users = users #list of user objects, used to get the user sp
        self.current_device = current_device
        self.index = 0
        self.progress_sec = 0
        self.exit = Event()
        self.t1 = None
        self.choose_playlist()


    def loop(self):
        """START looping, when already looping skipsong the song-selection loop, loop through the songs in the playlist"""
        while not self.exit.is_set():
            # playlist_uri = "spotify:playlist:4YApAkBZf2sjhA4FXMoiTU"
            if self.index >= get_playlist_length(self.playlist_uri):
                self.index = 0
            elif self.index < 0:
                self.index = get_playlist_length(self.playlist_uri)+self.index
            play_song_from_playlist(playlist_uri=self.playlist_uri, idx=self.index, current_device=self.current_device, progress_sec=self.progress_sec)
            get_playlist_info(playlist_uri=self.playlist_uri, display=True)
            # wait one sec, in order to not get the: 
            # "there is no track currently playing" error
            self.exit.wait(1)
            duration_sec,progress_sec = get_current_song_info(idx=self.index, display=True)
            self.show_controls()
            self.exit.wait(duration_sec-progress_sec) # wait for the rest of the song duration
            if self.is_running:
                self.progress_sec = 0
                self.index += 1

    def previous_or_beginning(self):
        if is_playing():
            _,self.progress_sec = get_current_song_info(idx=self.index, display=True)
            if self.progress_sec > 10: # go to start of current song
                self.progress_sec = 0
            else: # go to pervious song
                self.index -=1
                self.progress_sec = 0
            self.start()
        else:
            self.index -=1
            self.progress_sec = 0
            self.start()
 

    def play_or_pause(self): #NOT CONINUEING
        # check if playing a song
        if is_playing():
            _,self.progress_sec = get_current_song_info(idx=self.index, display=True,pause = True)
            self.stop()
        else:
            # self.progress_sec = self.progress_sec
            self.start()

    def skip(self):
        self.index +=1
        self.progress_sec = 0
        self.start()

    def start(self):
        """starts the song-selection loop"""
        self.stop() # stop the looping of the playlist first, sothat only one loop is on in the background instead of multiple
        self.exit.clear()
        self.t1 = threading.Thread(target=self.loop)
        self.is_running = True
        self.t1.start()
        
    def stop(self):
        """stops the song-selection loop"""
        if is_playing():
            sp.pause_playback(device_id=self.current_device)
        self.exit.set()
        self.is_running = False
        if not self.t1 is None:
            self.t1.join()


    @staticmethod
    def show_controls():
        print("""
------------------THE MUSIC PLAYER------------------
Choose option:
1: previous
2: play/pause
3: skip
4: stop
q: quit
----------------------------------------------------""")

    def choose_playlist(self):
        # self.input = input("give playlist url")
        # self.playlist_uri = get_uri(self.input)
        self.playlist_uri = "spotify:playlist:4YApAkBZf2sjhA4FXMoiTU"



if __name__ == "__main__":
    musicplayer = MusicPlayer()
    musicplayer.show_controls()
    app_on=True
    while app_on:
        chosen_option=input()
        match chosen_option:
            case "1":
                musicplayer.previous_or_beginning()
                # mu
                print("~~~~~~~~~~~~~~PLAYLIST STARTED PLAYING~~~~~~~~~~~~~~")
            case "2":
                if is_playing():
                    print("~~~~~~~~~~~~~~~~~~~PLAYLIST PAUSED~~~~~~~~~~~~~~~~~~")
                else:
                    print("~~~~~~~~~~~~~~PLAYLIST STARTED PLAYING~~~~~~~~~~~~~~")
                musicplayer.play_or_pause()
            case "3":
                musicplayer.skip()
                print("~~~~~~~~~~~~~~PLAYLIST STARTED PLAYING~~~~~~~~~~~~~~")
            case "4":
                musicplayer.stop()
                print("~~~~~~~~~~~~~PLAYLIST NO LONGER LOOPING~~~~~~~~~~~~~")
            case "q":
                musicplayer.stop()
                print("quitting program..")
                app_on = False
            case _:
                print(f"The input: {chosen_option}, is not a valid command, try again!")

    print("done")



