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
logger_recommendations = log_helper("get_recommendations_log.log", log_level='DEBUG')

# loading environment variables
env_file = f'{project_root}/data/.env'
load_dotenv(env_file)

genres_data_file = f'{project_root}/data/genres_data.json'
genres_data = read_file(genres_data_file)

rec_avail_genre_file = f'{project_root}/data/genres/rec_avail_seed_genres.json'
available_genre_seeds = read_file(rec_avail_genre_file)

# Urls for getting data from spotify api
available_genre_seeds_url = os.getenv('GET_AVAILABLE_GENRE_SEEDS')
recommendations_url = os.getenv('GET_RECOMMENDATIONS')
current_user_profile_url = os.getenv('GET_CURRENT_USER_PROFILE')
user_top_items_url = os.getenv('GET_USER_TOP_ITEMS')
get_artists_info = os.getenv('GET_ARTISTS_INFO')

playlist_description = ""

# Updates environment variables 
def update_env(values=[]):
    if values:
        for key, value in values.items():
            set_key(env_file, key, value)


# Gets available genre seeds
def get_available_genre_seeds(access_token):
    global available_genre_seeds
    
    response = requests.get(
        available_genre_seeds_url,
        headers={
            'Authorization': f"Bearer {access_token}"
        }

    )

    if response.status_code == 200:
        logger_recommendations.log_message('info',"Successfully retrieved available genre seeds")
        json_resp = response.json()
        
        available_genre_seeds = json_resp['genres']
        # Saving the available genre seeds to a file
        dump_file(available_genre_seeds,rec_avail_genre_file)        


    elif response.status_code == 401:
        # invalid access token
        json_resp = response.json()

        logger_recommendations.log_message('error', json_resp['error']['message'])
    

# Get current user's id and name
def get_current_users_id(access_token):
    global user_id,user_name

    logger_recommendations.log_message('info',"Retrieving user's profile")
    
    # Getting current user's profile
    response = requests.get(
        current_user_profile_url,
        headers={
            'Authorization': f"Bearer {access_token}"
        }
    )

    if response.status_code == 200:
        logger_recommendations.log_message('info',"Successfully retrieved user's profile")
        json_resp = response.json()
        
        user_id = json_resp['id']
        user_name = json_resp['display_name']

        user = {
            'USER_ID': user_id,
            'USER_NAME': user_name
        }

        update_env(user)
        logger_recommendations.log_message('info',f"Successfully updated environment variables with user's id and name")

    elif response.status_code == 401:
        # invalid access token
        json_resp = response.json()

        logger_recommendations.log_message('error', json_resp['error']['message'])
    
# To get an artist genres
def get_artists_genres(access_token, artist_ids):
    ids = ','.join(artist_ids)
    
    response = requests.get(
        get_artists_info,
        headers={
            'Authorization': f"Bearer {access_token}"
        },
        params={
            'ids' : ids
        }
    )
    
    if response.status_code == 200:
        logger_recommendations.log_message('info',"Successfully retrieved artists genres")
        json_resp = response.json()
        
        artists_genres = []
        for artist in json_resp['artists']:
            artists_genres += artist['genres']
        
        return artists_genres
    
    elif response.status_code == 401:
        json_resp = response.json()
        logger_recommendations.log_message('error', json_resp['error']['message'])
        
        return []

    
# To get the Top artists and tracks
def get_top_items(access_token, type, time_range="medium_term", limit=15, offset=0):
    response = requests.get(
        user_top_items_url.format(type=type),
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
        logger_recommendations.log_message('info',f"Successfully retrieved user's top {type}")
        json_resp = response.json()
        
        
        if type == 'artists':
            artists,artist = [],{}
            for item in json_resp['items']:
                artist={
                    'artists_id' : item['id'],
                    'artists_name' : item['name'],
                    'artists_popularity' : item['popularity'],
                    'artists_genres' : item['genres']

                }           
                artists.append(artist)     
        
            return {
                'artists' : artists,
                'error' : None
            }
        
        elif type == 'tracks':
         
            tracks,track = [],{}

            for item in json_resp['items']:
                #  Getting the artists of the tracks
                artists, artist, artists_array = [],{},[]
                for item_ in item['artists']:
                    
                    
                    artists_array.append(item_['id'])  

                # getting tracks
                track={ 
                    'track_id' : item['id'],
                    'track_name' : item['name'],
                    'popularity' : item['popularity'],
                    'artists_ids' : artists_array
                }

                tracks.append(track)     
        
            return {
                'tracks' : tracks,
                'error' : None
            }

    elif response.status_code == 401:
        # invalid access token
        json_resp = response.json()

        logger_recommendations.log_message('error', json_resp['error']['message'])

        return {
            f'{type}' : None,
            'error' : json_resp['error']['message']
        }


#  Method to get artists and tracks at the same time also saving it to the code
def get_top_artists_and_tracks(access_token):
    global user_top_artists,user_top_tracks
    
    
    # getting artists
    response = get_top_items(access_token, 'artists',limit=50)
    if not response['error']:
        user_top_artists = response['artists']
    else:
        user_top_artists = None
    # getting tracks
    response = get_top_items(access_token, 'tracks',limit=50)
    if not response['error']:
        user_top_tracks = response['tracks']
    else:
        user_top_tracks = None



