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

bardapi_path = f'{project_root}/data/BardAPI/'
genres_path = f'{project_root}/data/genres/'
model_path = f'{project_root}/data/model/'
spotifyapi_path = f'{project_root}/data/SpotifyAPI/'
track_features_path = f'{project_root}/data/track_features/'
user_data_path = f'{project_root}/data/user_data/'

from helpers_.json_helper import read_file, dump_file
from helpers_.log_helper import log_helper
from Spotify_.SpotifyAPIHelper import SpotifyAPIHelper
from Bard_.BardAPI import TextAnalysis
from NetScrapper.EveryNoiseScrapper import EveryNoiseScrapper
SAH = SpotifyAPIHelper
TXA = TextAnalysis()
ENS = EveryNoiseScrapper()

# Setting logger
logger_utility = log_helper("SpotifyUtility_log.log", log_level='DEBUG')

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
        

# Urls for getting data from spotify api
recommendations_url = os.getenv('GET_RECOMMENDATIONS')
available_genre_seeds_url = os.getenv('GET_AVAILABLE_GENRE_SEEDS')
current_user_profile_url = os.getenv('GET_CURRENT_USER_PROFILE')
user_top_items_url = os.getenv('GET_USER_TOP_ITEMS')
get_recommendations_url = os.getenv('GET_RECOMMENDATIONS')
get_artists_url = os.getenv('GET_ARTISTS_INFO')
current_track_url = os.getenv('GET_CURRENT_TRACK_URL')
playback_state_url = os.getenv('GET_PLAYBACK_STATE_URL')
track_features_url = os.getenv('GET_TRACK_FEATURES_URL')
current_user_playlists_url = os.getenv('GET_CURRENT_USER_PLAYLISTS')
user_playlists_url = os.getenv('GET_USER_PLAYLISTS')
playlist_items_url = os.getenv('GET_PLAYLIST_ITEMS')
get_playlist_url = os.getenv('GET_PLAYLIST')
playlist_tracks_url = os.getenv('GET_PLAYLIST_TRACKS')
playlist_description = ""


# Updates environment variables 
def update_env(values=[]):
    if values:
        for key, value in values.items():
            set_key(env_file, key, value)
            

class PlayerInfo:
    @classmethod
    def get_current_track(cls, access_token=SAH.current_access_token()):
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

        elif response.status_code == 204:
            return {'error' : 'No track is currently playing'}
        elif response.status_code == 401:
            return {'error' : json_resp['error']['message ']}

        else:
            return {'error' : json_resp['error']['message ']}

    @classmethod
    def get_player_state(cls, access_token=SAH.current_access_token()):
        response = requests.get(
            playback_state_url,
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )

        if response.status_code == 204:
            # The player state is not available or active
            return {'state': None}
        
        
        json_resp = response.json()
        
        if response.status_code == 200:
            json_resp = response.json()
            playing_state = json_resp.get('is_playing', False)
            return {'state': playing_state}

        
        elif response.status_code == 401:
            return {'error' : json_resp['error']['message']}
        
        else:
            return {'error' : json_resp['error']}

    @classmethod
    def get_track_features(cls, track_id, access_token=SAH.current_access_token()):
        response = requests.get(
            f"{track_features_url}{track_id}",
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )
        json_resp = response.json()
        
        if response.status_code == 200:
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
            track_features = {
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

            return track_features

        elif response.status_code == 401:
            return {'error' : json_resp['error']['message ']}


class StatusMonitor:
    
    def __init__(self, duration_minutes=5):
        self.duration_minutes = duration_minutes
        self.current_track_id = None
        self.session_state = None
        self.previous_state = False
        self.start_time = time.perf_counter()
        self.flag = True

    def timer(self,duration_minutes):
        if time.perf_counter() - self.start_time > duration_minutes * 60:
            self.flag = False

    def status_monitor(self,duration_mintutes=None, loop=False):
        duration_mintutes = self.duration_minutes if not duration_mintutes else duration_mintutes
        current_track_info = None

        while self.flag:
            self.timer(duration_mintutes)

            player_state = PlayerInfo.get_player_state()
            
            if 'error' in player_state:
                logger_utility.log_message('error', player_state['error'])
                SAH.refresh_or_get_new_tokens()
                continue
            
            else:
                if player_state['state']:
                    current_track_info = PlayerInfo.get_current_track()
                    if 'error' in current_track_info:
                        logger_utility.log_message('error', current_track_info['error'])
                        SAH.refresh_or_get_new_tokens()
                        continue
                    else:
                        if current_track_info['id'] != self.current_track_id or self.previous_state is False:
                            print(f"Playing {current_track_info['track_name']} by {current_track_info['artists']}")
                            self.current_track_id = current_track_info['id']
                        self.previous_state = player_state['state']
                        self.session_state = player_state['state']

                elif player_state['state'] is False and self.previous_state is True:
                    self.previous_state = player_state['state']
                    print("Player paused")
                    
                elif player_state['state'] is None:
                    if self.session_state is None:
                        print("No active session")
                        logger_utility.log_message('info', "session not started yet")
                        self.session_state = False
                    
                    elif self.session_state is True:
                        print("Session ended")
                        self.session_state = None
                        self.current_track_id = None
                        if not loop:
                            break
            time.sleep(2)


class StaticInfo:
    
    @classmethod
    def get_available_genre_seeds(cls, access_token=SAH.current_access_token()):
        response = requests.get(
            os.getenv('GET_AVAILABLE_GENRE_SEEDS'),
            headers={'Authorization': f"Bearer {access_token}"} 
        )

        if response.status_code == 200:
            logger_utility.log_message('info', "Successfully retrieved available genre seeds")
            json_resp = response.json()
                
            available_genre_seeds = json_resp['genres']
            # Saving the available genre seeds to a file
            dump_file(rec_avail_genre_file, available_genre_seeds)   
                 
        elif response.status_code == 401:
            # Invalid access token
            json_resp = response.json()
            logger_utility.log_message('error', json_resp['error']['message'])

    @classmethod
    def get_current_user_profile(cls, access_token=SAH.current_access_token()):
        logger_utility.log_message('info', "Retrieving user's profile")
        response = requests.get(
            os.getenv('GET_CURRENT_USER_PROFILE'),
            headers={'Authorization': f"Bearer {access_token}"}
        )

        if response.status_code == 200:
            logger_utility.log_message('info', "Successfully retrieved user's profile")
            json_resp = response.json()
            
            user_id = json_resp['id']
            user_name = json_resp['display_name']

            user = {
                'USER_ID': user_id,
                'USER_NAME': user_name
            }

            update_env(user)
            logger_utility.log_message('info', f"Successfully updated environment variables with user's id and name")

        elif response.status_code == 401:
            # Invalid access token
            json_resp = response.json()
            logger_utility.log_message('error', json_resp['error']['message'])

            
class ItemInfo:

    @staticmethod
    def get_artists_genres(artist_ids_concat, access_token=SAH.current_access_token()):
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
            logger_utility.log_message('info', "Successfully retrieved artists genres")
            json_resp = response.json()
            
            artists_genres = []
            for artist in json_resp['artists']:
                artists_genres += artist['genres']
            
            return artists_genres
        
        elif response.status_code == 401:
            json_resp = response.json()
            logger_utility.log_message('error', json_resp['error']['message'])
        
            return []

    @staticmethod
    def get_top_items( type, time_range="medium_term", limit=15, offset=0, access_token=SAH.current_access_token()):
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
            logger_utility.log_message('info', f"Successfully retrieved user's top {type}")
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
            logger_utility.log_message('error', json_resp['error']['message'])
            
        return {
            f'{type}': None,
            'error': 'Unknown error occurred.'
        }

    @staticmethod
    def get_top_artists_and_tracks(limit=50, access_token=SAH.current_access_token()):

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

    @staticmethod
    def scrape_playlists_for_genres(user_id=os.getenv('USER_ID'), limit=50, offset=0, access_token=SAH.current_access_token()):
        playlist_ids = ItemInfo.get_users_playlists(user_id)
        tracks = []

        for playlist_id in playlist_ids:
            response = requests.get(
                playlist_items_url.format(playlist_id=playlist_id),
                headers={
                    'Authorization': f"Bearer {access_token}"
                },
                params={
                    'fields': 'items(track(id,name,artists(id,name)))',
                    'limit': limit,
                    'offset': offset
                }
            )

            if response.status_code == 200:
                logger_utility.log_message('info', f"Successfully retrieved playlist's items {response.json}")
                json_resp = response.json()

                
                for item in json_resp['items']:
                    artist_id = []
                    if not item['track']:
                        logger_utility.log_message('info', f"Item's track is None, prev item: {track_info}")
                        continue
                    
                    for artist in item['track']['artists']:
                        artist_id.append(artist['id'])

                    track_info = {
                        'track_id': item['track']['id'],
                        'artists_ids': artist_id
                    }

                    # Store the track information in the tracks dictionary
                    tracks.append(track_info)
        DH = DataHandler()
        DH.make_dataset(tracks=tracks)
    
    
    @staticmethod
    def get_users_playlists(user_id=None, limit=50, offset=0, access_token=SAH.current_access_token()):
        playlists_url = user_playlists_url.format(user_id=user_id) if user_id else current_user_playlists_url
        logger_utility.log_message('info', "Retrieving user's playlists")
        response = requests.get(
            playlists_url,
            headers={
                'Authorization': f"Bearer {access_token}"
            },
            params={
                'limit': limit,
                'offset': offset
            }
        )

        if response.status_code == 200:
            logger_utility.log_message('info', f"Successfully retrieved user's {user_id} playlists")
            json_resp = response.json()
            
            playlist_ids = [item['id'] for item in json_resp['items']]
            
            return playlist_ids
        
        elif response.status_code == 401:
            # Invalid access token
            json_resp = response.json()
            logger_utility.log_message('error', json_resp['error']['message'])
            
            return []
        
        else:
            json_resp = response.json()
            logger_utility.log_message('error', json_resp['error']['message'])
            
            return []
            
    
    @staticmethod        
    def get_playlist_info(playlist_id='',method='', limit=50, offset=0, access_token=SAH.current_access_token()):
        tracks = []
        response = requests.get(
            playlist_items_url.format(playlist_id=playlist_id),
            headers={
                'Authorization': f"Bearer {access_token}"
            },
            params={
                # 'fields': 'items(track(id,name,artists(id,name)))',
                'limit': limit,
                'offset': offset
            }
        )

        if response.status_code == 200:
            logger_utility.log_message('info', f"Successfully retrieved playlist's items {response.json}, method= {method}")
            json_resp = response.json()

            
            for item in json_resp['items']:
                artist_id = []
                if not item['track']:
                    logger_utility.log_message('info', f"Item's track is None, prev item: {track_info}")
                    continue
                
                for artist in item['track']['artists']:
                    artist_id.append(artist['id'])

                track_info = {
                    'track_id': item['track']['id'],
                    'track_popularity': item['track']['popularity'],
                    'track_name': item['track']['name'],
                    'artists_ids': artist_id
                }
                tracks.append(track_info)
                
            return tracks
             
        elif response.status_code == 401:
            # Invalid access token
            json_resp = response.json()
            logger_utility.log_message('error', json_resp['error']['message'])
            
            return []
        
        else:
            json_resp = response.json()
            logger_utility.log_message('error', json_resp['error']['message'])
            
            return []
                                    
    @staticmethod          
    def get_recommendations_spotify(method='',limit=50, seed_artist=[],seed_genres=[], seed_tracks=[],access_token=SAH.current_access_token()): 
        response = requests.get(
            os.getenv('GET_RECOMMENDATIONS'),
            headers={
                'Authorization': f'Bearer {access_token}' 
            }, 
            params={
                'limit': limit,
                'seed_artist': seed_artist,
                'seed_genres': seed_genres,
                'seed_tracks': seed_tracks
            }
        )
        
        if response.status_code == 200:
            logger_utility.log_message('info', f"Successfully retrieved recommendations playlists, method: {method}")
            json_resp = response.json()
            
            playlist = []
            
            for track in json_resp['tracks']:
                track = {
                    'track_name': track['name'],
                    'track_id': track['id'],
                    'track_populalrity': track['popularity'],
                    'artists': [{'artist_name' : artist['name'], 'artist_id': artist['id']} for artist in track['artists']]                
                }
                playlist.append(track)
            
            return playlist
             
        elif response.status_code == 401:
            # Invalid access token
            json_resp = response.json()
            logger_utility.log_message('error', json_resp['error']['message'])
            
            return []
        
        else:
            json_resp = response.json()
            logger_utility.log_message('error', json_resp['error']['message'])
            
            return []
                    

class DataHandler:

    def __init__(self):

        # Loading Data
        self.artists_genres_data_file = f'{user_data_path}/artists_genres_data.json'
        self.tracks_genres_data_file = f'{user_data_path}/tracks_genres_data.json'
        self.user_genres_data_file = f'{user_data_path}/user_genres_data.json'
        self.user_genres_cluster_file = f'{user_data_path}/user_genres_cluster.json'
        # 
        self.user_genres_data = read_file(self.user_genres_data_file)
        self.artists_genres_data = read_file(self.artists_genres_data_file)
        self.tracks_genres_data = read_file(self.tracks_genres_data_file)
        self.user_genres_cluster = read_file(self.user_genres_cluster_file,default=[])
        
        self.top_items = ItemInfo.get_top_artists_and_tracks()
        self.user_top_artists = self.top_items['user_top_artists']
        self.user_top_tracks = self.top_items['user_top_tracks']

        # Dummy data for demonstration purposes
        self.search_seed_genres = {'vaporwave', 'dream pop', 'synthwave', 'lofi hip hop', 'chillwave'}
        self.recommend_seed_genres = {'groove', 'funk', 'soul', 'chill'}


    def make_dataset(self, tracks='', artists=False):
        artists_array = None
        if not tracks:
            tracks_array = self.user_top_tracks
            
        else:
            tracks_array = tracks
        # Adding top tracks' genres to dataset
        track_genres_data_local = {}
        user_genres_cluster_local = []
        artist_genres_data_local = {}
        
        if tracks_array:
            for track in tracks_array:
                if track['track_id'] in self.tracks_genres_data:
                    track_genres = self.tracks_genres_data[track['track_id']]
                else:
                    artist_ids_concat = ','.join([artist_id for artist_id in track['artists_ids']])
                    track_genres = set(ItemInfo.get_artists_genres(artist_ids_concat))

                    # adding the ids whose data is not present to the local database
                    track_genres_data_local[track['track_id']] = list(track_genres)

                for genre in track_genres:
                    if genre in self.user_genres_data:
                        if 'tracks' not in self.user_genres_data[genre]:
                            self.user_genres_data[genre]['tracks'] = []
                        if track['track_id'] not in self.user_genres_data[genre]['tracks']:
                            self.user_genres_data[genre]['tracks'].append(track['track_id'])
                    else:
                        self.user_genres_data[genre] = {'tracks': [track['track_id']]}

                # Add genre to user_genres_cluster for the current track
                if track_genres:
                    user_genres_cluster_local.append(list(track_genres))

        if artists:
            # Adding top artists' genres to dataset
            for artist in artists_array:
                artists_genres = set(artist['artists_genres'])
                # adding artists genres to local database
                artist_genres_data_local[artist['artists_id']] = list(artists_genres)

                for genre in artists_genres:
                    if genre in self.user_genres_data:
                        if 'artists' not in self.user_genres_data[genre]:
                            self.user_genres_data[genre]['artists'] = []
                        if artist['artists_id'] not in self.user_genres_data[genre]['artists']:
                            self.user_genres_data[genre]['artists'].append(artist['artists_id'])
                    else:
                        self.user_genres_data[genre] = {'artists': [artist['artists_id']]}
            self.artists_genres_data.update(artist_genres_data_local)
            dump_file(self.artists_genres_data_file, self.artists_genres_data)
            logger_utility.log_message('info',f'Successfully dumped the artists_genres_data to {self.artists_genres_data_file}')

        # updating the tracks_genres_data with the local_database
        # updating the artists_genres_data with the local_database
        self.tracks_genres_data.update(track_genres_data_local)
        self.user_genres_cluster.extend(user_genres_cluster_local)

        # dumping the updated data to the local files 
        dump_file(self.tracks_genres_data_file, self.tracks_genres_data)
        logger_utility.log_message('info',f'Successfully dumped the track_genres_data to {self.tracks_genres_data_file}')
        dump_file(self.user_genres_data_file, self.user_genres_data)
        logger_utility.log_message('info',f'Successfully dumped the user_genres_data to {self.user_genres_data_file}')
        dump_file(self.user_genres_cluster_file, self.user_genres_cluster)
        logger_utility.log_message('info',f'Successfully dumped the user_genres_cluster to {self.user_genres_cluster_file}') 
        
        
    def save_dataset(self, user_data=False):
        if user_data:
            self.make_dataset()
            
         
             
if __name__ == '__main__':
    # Running all the functions:
    SAH.refresh_or_get_new_tokens()
    # s = StatusMonitor()
    # s.status_monitor(5)
    # It = ItemInfo()
    # pprint(It.get_recommendations_spotify(seed_genres= 'classical,country,jazz'))
    ItemInfo.scrape_playlists_for_genres()