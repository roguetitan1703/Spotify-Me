from dotenv import load_dotenv, set_key
import base64
import requests
import json
import time
import os, sys
from urllib.parse import urlencode
import webbrowser
from pprint import pprint

# Add the project's root directory to the Python path
project_root = os.getcwd()
sys.path.append(f'{project_root}/data')
sys.path.append(f'{project_root}/libs')

from helpers_.json_helper import read_file, dump_file
from helpers_.log_helper import log_helper
from SpotifyAPIHelper import SpotifyAPIHelper as SAH
from Bard_.bard_api import TextAnalysis
from NetScrapper.EveryNoiseScrapper import EveryNoiseScrapper
import SpotifyUtility

INF = SpotifyUtility.ItemInfo()
TXA = TextAnalysis()
ENS = EveryNoiseScrapper()


class SpotifyDataHandler:

    def __init__(self):
        # Setting logger
        self.logger_Data = log_helper("SpotifyDataHandler_log.log", log_level='DEBUG')

        # loading environment variables
        self.env_file = f'{project_root}/data/.env'
        load_dotenv(self.env_file)

        # Loading Data
        self.user_genres_data_file = f'{project_root}/data/genres/user_genres_data.json'
        self.artists_genres_data_file = f'{project_root}/data/genres/artists_genres_data.json'
        self.tracks_genres_data_file = f'{project_root}/data/genres/tracks_genres_data.json'
        
        # 
        self.user_genres_data = read_file(self.user_genres_data_file)
        self.artists_genres_data = read_file(self.artists_genres_data_file)
        self.tracks_genres_data = read_file(self.tracks_genres_data_file)
        
        self.top_items = INF.get_top_artists_and_tracks()
        self.user_top_artists = self.top_items['user_top_artists']
        self.user_top_tracks = self.top_items['user_top_tracks']

        # Dummy data for demonstration purposes
        self.search_seed_genres = {'vaporwave', 'dream pop', 'synthwave', 'lofi hip hop', 'chillwave'}
        self.recommend_seed_genres = {'groove', 'funk', 'soul', 'chill'}

    
    def make_dataset(self):
        
        # Adding top tracks' genres to dataset
        track_genres_data_local = {}
        for track in self.user_top_tracks:
            # emitting the track if it already has the data in the database
            if track['track_id'] in self.tracks_genres_data:
                track_genres = self.tracks_genres_data[track['track_id']]
                
            else:
                artist_ids_concat = ','.join([artist_id for artist_id in track['artists_ids']])
                track_genres = set(INF.get_artists_genres(artist_ids_concat))
            
                # adding the ids whose data is not present to the local database
                track_genres_data_local[track['track_id']] = list(track_genres)
            

            for genre in track_genres:
                if genre in self.user_genres_data:
                    if 'tracks' in self.user_genres_data[genre]:
                        self.user_genres_data[genre]['tracks'].append(track['track_id'])
                    else:
                        self.user_genres_data[genre]['tracks'] = [track['track_id']]
                else:
                    self.user_genres_data[genre] = {'tracks': [track['track_id']]}
            

        # updating the tracks_genres_data with the local_database 
        self.tracks_genres_data.update(track_genres_data_local)
        dump_file(self.tracks_genres_data_file, self.tracks_genres_data)

        # Adding top artists' genres to dataset
        artist_genres_data_local = {}
        for artist in self.user_top_artists:
            artists_genres = set(artist['artists_genres'])
            # adding artists genres to local database
            artist_genres_data_local[artist['artists_id']] = list(artists_genres)
            
            for genre in artists_genres:
                if genre in self.user_genres_data:
                    if 'artists' in self.user_genres_data[genre]:
                        self.user_genres_data[genre]['artists'].append(artist['artists_id'])
                    else:
                        self.user_genres_data[genre]['artists'] = [artist['artists_id']]
                else:
                    self.user_genres_data[genre] = {'artists': [artist['artists_id']]}

        self.artists_genres_data.update(artist_genres_data_local)
        dump_file(self.artists_genres_data_file, self.artists_genres_data)
        dump_file(self.user_genres_data_file, self.user_genres_data)

if __name__ == "__main__":
    text = "I want a playlist which has cool aesthetic types songs which are groovy nut loud but reverb or slowed types still with good music which you can jam on by yourself"
    SAH.refresh_or_get_new_tokens()
    handle = SpotifyDataHandler()
    handle.make_dataset()
    pprint(handle.user_genres_data, indent = 4)
    
    # extract_and_group_items(SAH.access_token, text)
    # make_recommendation_batches()
