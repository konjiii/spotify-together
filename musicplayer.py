# SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET needed and everyone needs the same redirect_uri = "http://127.0.0.1:9090/callback"
import sys
import os
import spotipy
from dotenv import load_dotenv
from spotipy.cache_handler import CacheFileHandler
from spotipy.oauth2 import SpotifyOAuth
import threading
from threading import Event

class MusicPlayer:
    def __init__(self, host):
    # def __init__(self,users):
        self.users = dict() #list of user objects, used to get the user sp
        self.host = host
        self.queue_number_is_playing = False
        self.queue = []
        # self.current_device hier, haal het uit de user per user
        self.index = 0
        self.progress_sec = 0
        self.exit = Event()
        self.t1 = None
        self.choose_playlist()

    def add_user(self, user):
        self.users[user.username] = user

    def remove_user(self, username):
        self.users.pop(username)



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
                if musicplayer.is_playing():
                    print("~~~~~~~~~~~~~~~~~~~PLAYLIST PAUSED~~~~~~~~~~~~~~~~~~")
                else:
                    print("~~~~~~~~~~~~~~PLAYLIST STARTED PLAYING~~~~~~~~~~~~~~")
                musicplayer.play_or_pause()
            case "3":
                musicplayer.skip()
                print("~~~~~~~~~~~~~~PLAYLIST STARTED PLAYING~~~~~~~~~~~~~~")
            case "4":
                musicplayer.add_to_queue()
            case "5":
                musicplayer.stop()
                print("~~~~~~~~~~~~~PLAYLIST NO LONGER LOOPING~~~~~~~~~~~~~")
            case "q":
                musicplayer.stop()
                print("quitting program..")
                app_on = False
            case _:
                print(f"The input: {chosen_option}, is not a valid command, try again!")

    print("done")



