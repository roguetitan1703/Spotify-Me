from dotenv import load_dotenv, set_key
import base64
import requests
import json
import time
import os, sys, threading
from urllib.parse import urlencode
import webbrowser
from pprint import pprint

# Add the project's root directory to the Python path
project_root = os.getcwd()
sys.path.append(f'{project_root}/data')
sys.path.append(f'{project_root}/libs')

bardapi_path = f'{project_root}/data/BardAPI/'
genres_path = f'{project_root}/data/genres/'
model_path = f'{project_root}/data/model/'
spotifyapi_path = f'{project_root}/data/SpotifyAPI/'
track_features_path = f'{project_root}/data/track_features/'
user_data_path = f'{project_root}/data/user_data/'

from helpers_.json_helper import read_file, dump_file
from helpers_.log_helper import log_helper
from Spotify_.SpotifyAPIHelper import SpotifyAPIHelper
from Spotify_.SpotifyUtility import ItemInfo, StaticInfo, DataHandler, PlayerInfo, StatusMonitor
from Bard_.BardAPI import TextAnalysis
from NetScrapper.EveryNoiseScrapper import EveryNoiseScrapper

SAH = SpotifyAPIHelper()
SAH.refresh_or_get_new_tokens()
INF = ItemInfo()
TXA = TextAnalysis()
ENS = EveryNoiseScrapper()

# Setting logger
logger_recommendation = log_helper("RecommendationEngine_log.log", log_level='DEBUG')

# loading environment variables
env_file = f'{spotifyapi_path}/.env'
load_dotenv(env_file)

rec_avail_genre_file = f'{genres_path}/rec_avail_seed_genres.json'
artists_genres_data_file = f'{user_data_path}/artists_genres_data.json'
tracks_genres_data_file = f'{user_data_path}/tracks_genres_data.json'
user_genres_data_file = f'{user_data_path}/user_genres_data.json'

available_genre_seeds = read_file(rec_avail_genre_file)
artists_genres_data = read_file(artists_genres_data_file)
tracks_genres_data = read_file(tracks_genres_data_file)
user_genres_data = read_file(user_genres_data_file)


class RecommendationGenerator():
    def __init__(self) -> None:
        self.done = False
        self.master_playlist = []
        
    def retrieve_playlist(self):
        text = input("Enter the text you want to analyze to get playlists: ")
        
        # loading_thread = threading.Thread(target=self.loading_animation, args=(5,))
        
        # loading_thread.start()
        self.get_recommendation_spotify(self,seed_genres=['edm', 'deep-house', 'dance', 'club', 'house', 'party', 'dancehall', 'electronic', 'techno'])
        self.get_recommendations_everynoise(genres=['deep-house', 'dance', 'edm', 'house', 'pop', 'tropical-house', 'electronic', 'dancehall', 'future-bass', 'progressive-house'])
        self.done = True
        # loading_thread.join()
        # genres = TXA.extract_genres(text)

        # self.get_recommendation_spotify(self,seed_genres=genres['recommendation_available_genres'][:5])
        # self.get_recommendations_everynoise(genre=genres['recommendation_available_genres'])
        
        # combined_genres = genres['recommendation_available_genres'] + genres['search_available_genres']
    
    def get_recommendations_everynoise(self,genres=[], method='from_everynoise'):
        for genre in genres:
            playlist_id = ENS.playlist_id_scrapper(genre)
            playlist = INF.get_playlist_info(method=method, playlist_id=playlist_id)
            self.master_playlist.extend(playlist)
            

    def get_recommendation_spotify(self,method='from_spotify',seed_genres=[],seed_artists=[], seed_tracks=[]):
        for i in range(0,len(seed_genres),5):
            playlist = INF.get_recommendations_spotify(method=method, seed_artist=seed_artists[i:i+5], seed_genres=seed_genres, seed_tracks=seed_tracks)
            self.master_playlist.extend(playlist)
        

    def get_recommendation_user(self,method='from_user',genres=[]):
        for genre in genres:
            if genre in user_genres_data:
                user_genres_data[genre]
                
            
    def loading_animation(self, seconds):
        max_dots = 5  # Maximum number of trailing dots
        while not self.done:
            for dots_count in range(max_dots + 1):
                print("Loading" + "." * dots_count, end="\r")
                time.sleep(0.5)  # Adjust the delay as needed
            for dots_count in range(max_dots - 1, 0, -1):
                print("Loading" + "." * dots_count, end="\r")
                time.sleep(0.5)  # Adjust the delay as needed
            print("Loading" + " " * max_dots, end="\r")  # Clear the line
            time.sleep(0.5)  # Wait before restarting    
            
    def get_playlist(self):
        return self.master_playlist

RE = RecommendationGenerator()
RE.retrieve_playlist()
print(RE.get_playlist())
# get_recommendations_everynoise('pop')
# method='from_spotify',seed_genres=['synth-pop,country','edm','pop'],seed_artists=['5pUo3fmmHT8bhCyHE52hA6'], seed_tracks='4Dvkj6JhhA12EX05fT7y2e,6RUKPb4LETWmmr3iAEQktW')