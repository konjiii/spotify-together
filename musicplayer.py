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
    def __init__(self):
        self.users = dict() #list of user objects, used to get the user sp
        self.host = None
        
        # NOTES:
        # to find host user info do:
        # self.host.username, self.host.sp
        # to find all users info in this party
        # for k in self.users.keys():
        #     print(self.users[str(k)].username, self.users[str(k)].sp)
        
        self.queue_number_is_playing = False
        self.queue = []
        self.index = 0
        self.progress_sec = 0
        self.exit = Event()
        self.t1 = None
        # self.choose_playlist() #uncommented cause this function is missing rn

    def add_user(self, user):
        # The first user that is in the music player
        # is the first user that joined the party.
        # The first user is selected as the host:
        if len(self.users) == 0:
            self.host = user
        self.users[user.username] = user
        

    def remove_user(self, username):
        amount_of_users = len(self.users)
        # update self.host
        if list(self.users.keys())[0] == username:
            if amount_of_users >1:
                self.host = list(self.users.keys())[1] # host is the 2nd oldest party member if the host leaves           
            else:   
                self.host = None
        
        # remove user from playlist
        self.users.pop(username)

        # # close the music player !!!
        # if amount_of_users == 0:
           





if __name__ == "__main__":
    musicplayer = MusicPlayer()
    musicplayer.show_controls()
    app_on=True
    while app_on:
        chosen_option=input()
        match chosen_option:
            case "1":
                musicplayer.previous_or_beginning()
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



