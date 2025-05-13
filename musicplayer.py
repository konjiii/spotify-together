# SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET needed and everyone needs the same redirect_uri = "http://127.0.0.1:9090/callback"
import sys
import os
import spotipy
from dotenv import load_dotenv
from spotipy.cache_handler import CacheFileHandler
from spotipy.oauth2 import SpotifyOAuth
import threading
from threading import Event
import asyncio

""" User intended functions:
------------------THE MUSIC PLAYER------------------
Choose option:
1: previous
2: play/pause
3: skip
4: search and add to queue
5: stop
q: quit
----------------------------------------------------"""


class MusicPlayer:
    def __init__(self):
        self.users = dict() #list of user objects, used to get the user sp
        self.host = None
        # Needed for sending messages on behalf of the party
        self.ctx_dict = dict() # all ctx's of the self.users
        self.main_loop = asyncio.get_event_loop() # get main loop to be able to fire and forget in say_to_party

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
        self.playlist_uri = "spotify:playlist:4YApAkBZf2sjhA4FXMoiTU" # default playlist
        
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

        # close the music player !!!
        if amount_of_users == 0:
            self.stop()

    def add_ctx(self, username, ctx):
        """needed for sending messages to the discord on behalf of the party"""
        self.ctx_dict[username] = ctx

    def remove_ctx(self, username):
        self.ctx_dict.pop(username)


    def add_to_queue_bot(self, chosen_track):
        """discord-bot version of add to queue: Add songs to the self.queue"""
        self.queue.append(chosen_track)

    @staticmethod
    def get_uri(url: str) -> str:
        qm = url.find("?")
        if qm == -1:
            qm = None
        slash = url.rfind("/")
        return "spotify:playlist:" + url[slash + 1 : qm]

    def choose_playlist(self, url):
        # self.input = input("give playlist url")
        self.playlist_uri = self.get_uri(url)
        
    def get_playlist_length(self, playlist_uri:str):
        """Return: playlist length"""
        try:
            play_list = self.host.sp.playlist_tracks(playlist_id=playlist_uri) 
        except Exception as e:
            print(e, file=sys.stderr)
            raise TypeError("no good url, no playlist found")
        tracks = [item["track"]["uri"] for item in play_list["items"]] # get all songs in a playlist (list)
        return len(tracks)

    def is_playing(self):
        """Return True if the host is playing something, else: Return False"""
        playback = self.host.sp.current_playback()
        if playback and playback['is_playing']:
            return True
        else:
            return False
        
    def play_song(self, track_uri, progress_sec:int = 0):
        
        for k in self.users.keys():
            try:
                self.users[str(k)].sp.start_playback(device_id=self.users[str(k)].curr_device ,uris=[track_uri], position_ms=progress_sec*1000)
            except Exception as e:
                print("No device, YOUR SPOTIFY IS CLOSED! OPEN IT NOWWW!!! "+e, file=sys.stderr)

    def play_song_from_playlist(self,playlist_uri:str,idx:int, progress_sec:int = 0) -> None:
        """
        Play a song with the corresponding index in a playlist
        """
        try:
            play_list = self.host.sp.playlist_tracks(playlist_id=playlist_uri) 
        except:
            raise TypeError("no good url, no playlist found")
        tracks = [item["track"]["uri"] for item in play_list["items"]] # get all songs in a playlist <list>
        if idx >= len(tracks) or idx <0:
            idx = 0
        track_uri = tracks[idx]
        
        self.play_song(track_uri=track_uri, progress_sec=progress_sec)


    def say_to_party(self, response:str):
        asyncio.run_coroutine_threadsafe(self.ctx_dict[list(self.ctx_dict.keys())[0]].send(response), self.main_loop)

    def get_playlist_info(self,playlist_uri:str, display=False):
        """Print all the tracks and artists of the playlist."""
        if display:    
            try:
                results = self.host.sp.playlist_items(playlist_uri)
            except:
                raise TypeError("no good url, no playlist found")
            # Extract track names
            tracks = results['items']
            while results['next']:
                results = self.host.sp.next(results)
                tracks.extend(results['items'])
            response = ""
            for idx, playback in enumerate(tracks):
                track = playback['track']
                response += f"{idx+1}. {track['name']} by {track['artists'][0]['name']}\n"
            self.say_to_party(response)
                
    def get_current_song_info(self, idx:int=0, display=False, details=False, pause=False) -> float:
        """Get the currently playing song info, return the song duration and where you are in the song
        -------
        Return: duration_sec: float, progress_sec: float"""
        playback = self.host.sp.current_playback()
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
                    self.say_to_party(f"Now pausing: {idx+1}. {song_name} by {artist_name}")
                    # print(f"\nNow pausing: {idx+1}. {song_name} by {artist_name}")
                else:
                    self.say_to_party(f"Now playing: {idx+1}. {song_name} by {artist_name}")
                    # print(f"\nNow playing: {idx+1}. {song_name} by {artist_name}")
                if details:
                    self.say_to_party(f"Progress: {progress_ms / 1000:.2f} seconds\nDuration: {duration_sec:.3f} seconds")
                    # print(f"Progress: {progress_ms / 1000:.2f} seconds")
                    # print(f"Duration: {duration_sec:.3f} seconds")
            return duration_sec, progress_sec
        else:
            print("No song currently playing",file = sys.stderr)


    def loop(self):
        """START looping, loop through the songs in the playlist"""
        while not self.exit.is_set():
            if self.queue: # if there is a song in the queue 
                #play queue song
                self.queue_number_is_playing = True
                self.play_song(track_uri=self.queue[0], progress_sec=self.progress_sec)
            else:
                self.queue_number_is_playing=False
                # playlist_uri = "spotify:playlist:4YApAkBZf2sjhA4FXMoiTU"
                if self.index >= self.get_playlist_length(self.playlist_uri):
                    self.index = 0
                elif self.index < 0:
                    self.index = self.get_playlist_length(self.playlist_uri)-1
                self.play_song_from_playlist(playlist_uri=self.playlist_uri, idx=self.index, progress_sec=self.progress_sec)
                self.get_playlist_info(playlist_uri=self.playlist_uri, display=True)
            if self.is_running:
                # wait one second, in order to not get the: 
                # "there is no track currently playing" error
                self.exit.wait(1)
                duration_sec,progress_sec = self.get_current_song_info(idx=self.index, display=True)
                self.exit.wait(duration_sec-progress_sec) # wait for the rest of the song duration
            # if is_running, update the progress in the song for the next song
            # and update the index sothat the next song is played in the next loop, 
            # else: not running so do not update it
            if self.is_running:
                if self.queue_number_is_playing:
                    self.progress_sec = 0
                    self.queue.pop(0)
                else:
                    self.progress_sec = 0
                    self.index += 1


    def previous_or_beginning(self):
        if self.is_playing():
            _,self.progress_sec = self.get_current_song_info(idx=self.index, display=True)
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
 
    def play_or_pause(self):
        # check if playing a song
        if self.is_playing():
            _,self.progress_sec = self.get_current_song_info(idx=self.index, display=True,pause = True)
            self.stop()
        else:
            # self.progress_sec = self.progress_sec
            self.start()

    def skip(self):
        self.progress_sec = 0
        if self.queue_number_is_playing:
            self.queue.pop(0)
        else:
            self.index +=1
        self.start()
        
    def start(self):
        """starts the song-selection loop"""
        self.stop() # stop the looping of the playlist first, sothat only one loop is on in the background instead of multiple
        self.exit.clear()
        self.t1 = threading.Thread(target= self.loop, daemon=True)
        self.is_running = True
        self.t1.start()
        
    def stop(self):
        """stops the song-selection loop"""
        if self.is_playing():
            for k in self.users.keys():
                try:
                    self.users[str(k)].sp.pause_playback(device_id=self.users[str(k)].curr_device)
                except Exception as e:
                    print(f"user:{k}, No device, YOUR SPOTIFY IS CLOSED! OPEN IT NOWWW!!! "+e, file=sys.stderr)
        self.exit.set()
        self.is_running = False
        if not self.t1 is None:
            self.t1.join()


