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

TXA = TextAnalysis()
ENS = EveryNoiseScrapper()


# Setting logger
logger_recommendations = log_helper("SpotifyUtility_log.log", log_level='DEBUG')

# loading environment variables
env_file = f'{project_root}/data/.env'
load_dotenv(env_file)

rec_avail_genre_file = f'{project_root}/data/genres/rec_avail_seed_genres.json'
artists_genres_data_file = f'{project_root}/data/genres/artists_genres_data.json'
tracks_genres_data_file = f'{project_root}/data/genres/tracks_genres_data.json'

available_genre_seeds = read_file(rec_avail_genre_file)
artists_genres_data = read_file(artists_genres_data_file)
tracks_genres_data = read_file(tracks_genres_data_file)

# Urls for getting data from spotify api
recommendations_url = os.getenv('GET_RECOMMENDATIONS')
available_genre_seeds_url = os.getenv('GET_AVAILABLE_GENRE_SEEDS')
current_user_profile_url = os.getenv('GET_CURRENT_USER_PROFILE')
user_top_items_url = os.getenv('GET_USER_TOP_ITEMS')
get_artists_info = os.getenv('GET_ARTISTS_INFO')
current_track_url = os.getenv('GET_CURRENT_TRACK_URL')
playback_state_url = os.getenv('GET_PLAYBACK_STATE_URL')
track_features_url = os.getenv('GET_TRACK_FEATURES_URL')

playlist_description = ""


# Updates environment variables 
def update_env(values=[]):
    if values:
        for key, value in values.items():
            set_key(env_file, key, value)
            

class PlayerInfo:
    @classmethod
    def get_current_track(cls, access_token=SAH.access_token):
        response = requests.get(
            current_track_url,
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )

        if response.status_code == 200:
            json_resp = response.json()
            track_id = json_resp['item']['id']
            track_name = json_resp['item']['name']
            artists = [artist for artist in json_resp['item']['artists']]
            link = json_resp['item']['external_urls']['spotify']
            artist_names = ', '.join([artist['name'] for artist in artists])
            artist_list = [artist['name'] for artist in artists]
            popularity = json_resp['item']['popularity']

            current_track_info = {
                "id": track_id,
                "track_name": track_name,
                "artists": artist_names,
                "link": link,
                "popularity": popularity,
                "artists_list": artist_list
            }
            return current_track_info

        else:
            return None


    @classmethod
    def get_player_state(cls, access_token=SAH.access_token):
        response = requests.get(
            playback_state_url,
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )

        if response.status_code == 200:
            json_resp = response.json()
            playing_state = json_resp.get('is_playing', False)
            return playing_state
        elif response.status_code == 204:
            # The player state is not available or active (paused)
            return False
        else:
            # Handle other status codes here if needed
            return None

    @classmethod
    def get_track_features(cls, track_id, access_token=SAH.access_token):
        response = requests.get(
            f"{track_features_url}{track_id}",
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )
        json_resp = response.json()
        danceability = json_resp['danceability']
        energy = json_resp['energy']
        key = json_resp['key']
        loudness = json_resp['loudness']
        mode = json_resp['mode']
        speechiness = json_resp['speechiness']
        acousticness = json_resp['acousticness']
        instrumentalness = json_resp['instrumentalness']
        liveness = json_resp['liveness']
        valence = json_resp['valence']
        tempo = json_resp['tempo']
        current_track_features = {
            'danceability': danceability,
            'energy': energy,
            'key': key,
            'loudness': loudness,
            'mode': mode,
            'speechiness': speechiness,
            'acousticness': acousticness,
            'instrumentalness': instrumentalness,
            'liveness': liveness,
            'valence': valence,
            'tempo': tempo
        }

        return current_track_features


class StatusMonitor:
    
    def __init__(self, duration_minutes=5):
        self.duration_minutes = duration_minutes
        self.current_track_id = None
        self.last_checked_state = None
        self.start_time = time.perf_counter()
        self.flag = True

    def timer(self):
        if time.perf_counter() - self.start_time > self.duration_minutes * 60:
            self.flag = False

    def status_monitor(self):
        current_track_info = None
        player_state = None

        while self.flag:
            self.timer()

            player_state = PlayerInfo.get_player_state()
            if player_state is None:
                SAH.refresh_or_get_new_tokens
                continue

            if player_state:
                current_track_info = PlayerInfo.get_current_track()
                if current_track_info is None:
                    print("Error in getting current track info")
                    SAH.refresh_or_get_new_tokens()
                    continue
                else:
                    if current_track_info['id'] != self.current_track_id or self.last_checked_state is False:
                        print(f"Playing {current_track_info['track_name']} by {current_track_info['artists']}")
                        self.current_track_id = current_track_info['id']
                    self.last_checked_state = player_state

            if self.last_checked_state is None:
                print("Not playing anything")
                self.last_checked_state = False
            elif not player_state and self.last_checked_state:
                print("Player stopped")
                self.last_checked_state = player_state

            time.sleep(2)


class StaticInfo:
    
    @classmethod
    def get_available_genre_seeds(cls, access_token=SAH.access_token):
        response = requests.get(
            os.getenv('GET_AVAILABLE_GENRE_SEEDS'),
            headers={'Authorization': f"Bearer {access_token}"}
        )

        if response.status_code == 200:
            logger_recommendations.log_message('info', "Successfully retrieved available genre seeds")
            json_resp = response.json()
                
            available_genre_seeds = json_resp['genres']
            # Saving the available genre seeds to a file
            dump_file(rec_avail_genre_file, available_genre_seeds)   
                 
        elif response.status_code == 401:
            # Invalid access token
            json_resp = response.json()
            logger_recommendations.log_message('error', json_resp['error']['message'])

    @classmethod
    def get_current_user_profile(cls, access_token=SAH.access_token):
        logger_recommendations.log_message('info', "Retrieving user's profile")
        response = requests.get(
            os.getenv('GET_CURRENT_USER_PROFILE'),
            headers={'Authorization': f"Bearer {access_token}"}
        )

        if response.status_code == 200:
            logger_recommendations.log_message('info', "Successfully retrieved user's profile")
            json_resp = response.json()
            
            user_id = json_resp['id']
            user_name = json_resp['display_name']

            user = {
                'USER_ID': user_id,
                'USER_NAME': user_name
            }

            update_env(user)
            logger_recommendations.log_message('info', f"Successfully updated environment variables with user's id and name")

        elif response.status_code == 401:
            # Invalid access token
            json_resp = response.json()
            logger_recommendations.log_message('error', json_resp['error']['message'])

            
class ItemInfo:

    @staticmethod
    def get_artists_genres(artist_ids_concat, access_token=SAH.access_token):
        # emitting the ids whose data is already present

        response = requests.get(
            os.getenv('GET_ARTISTS_INFO'),
            headers={
                'Authorization': f"Bearer {access_token}"
                },
            params={
                'ids': artist_ids_concat
                }
        )

        if response.status_code == 200:
            logger_recommendations.log_message('info', "Successfully retrieved artists genres")
            json_resp = response.json()
            
            artists_genres = []
            for artist in json_resp['artists']:
                artists_genres += artist['genres']
            
            return artists_genres
        
        elif response.status_code == 401:
            json_resp = response.json()
            logger_recommendations.log_message('error', json_resp['error']['message'])
        
            return []

    @staticmethod
    def get_top_items( type, time_range="medium_term", limit=15, offset=0, access_token=SAH.access_token):
        response = requests.get(
            os.getenv('GET_USER_TOP_ITEMS').format(type=type),
            headers={
                'Authorization': f"Bearer {access_token}"
            },
            params={
                'time_range': time_range,
                'limit': limit,
                'offset': offset
            }
        )

        if response.status_code == 200:
            logger_recommendations.log_message('info', f"Successfully retrieved user's top {type}")
            json_resp = response.json()

            if type == 'artists':
                artists, artist = [], {}
                for item in json_resp['items']:
                    artist = {
                        'artists_id': item['id'],
                        'artists_name': item['name'],
                        'artists_popularity': item['popularity'],
                        'artists_genres': item['genres']
                    }
                    artists.append(artist)
                    
                return {
                    'artists': artists,
                    'error': None
                }
                
            elif type == 'tracks':
                
                tracks, track = [], {}
                for item in json_resp['items']:
                    # Getting the artists of the tracks
                    artists, artist, artists_array = [], {}, []
                    for item_ in item['artists']:
                        artists_array.append(item_['id'])

                    # Getting tracks
                    track = {
                        'track_id': item['id'],
                        'track_name': item['name'],
                        'popularity': item['popularity'],
                        'artists_ids': artists_array
                    }

                    tracks.append(track)

                return {
                    'tracks': tracks,
                    'error': None
                }
                
        elif response.status_code == 401:
            # Invalid access token
            json_resp = response.json()
            logger_recommendations.log_message('error', json_resp['error']['message'])
            
        return {
            f'{type}': None,
            'error': 'Unknown error occurred.'
        }

    @staticmethod
    def get_top_artists_and_tracks(limit=50, access_token=SAH.access_token):

        # Getting artists
        response = ItemInfo.get_top_items('artists', limit=limit)
        user_top_artists = response['artists'] if not response['error'] else None

        # Getting tracks
        response = ItemInfo.get_top_items('tracks', limit=limit)
        user_top_tracks = response['tracks'] if not response['error'] else None

        return {
            'user_top_artists' : user_top_artists,
            'user_top_tracks' : user_top_tracks
        }

if __name__ == '__main__':
    # Running all the functions:
    print("TETSTING...")
    StatusMonitor(1).status_monitor()
    StaticInfo.get_available_genre_seeds()
    StaticInfo.get_current_user_profile()
    ItemInfo.get_top_artists_and_tracks()
    ItemInfo.get_artists_genres(['0oSGxfWSnnOXhD2fKuz2Gy'])
    ItemInfo.get_top_items('artists', limit=50)
    
    