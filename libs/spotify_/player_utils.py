from dotenv import load_dotenv, set_key
import requests
import time
import os
from helpers_.log_helper import log_helper
current_path = os.getcwd()

# Setting logger
logger_utils = log_helper("player_utils_log.log", log_level='DEBUG')

# loading environment variables
env_file = f'{current_path}/data/.env'
load_dotenv(env_file)


# Urls for getting data from spotify api
current_track_url = os.getenv('GET_CURRENT_TRACK_URL')
playback_state_url = os.getenv('GET_PLAYBACK_STATE_URL')
track_features_url = os.getenv('GET_TRACK_FEATURES_URL')

# Tokens
refresh_token = os.getenv('REFRESH_TOKEN')
access_token = os.getenv('ACCESS_TOKEN')


# gets current track info
def get_current_track():
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


# Getting player state
def get_player_state():
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


# Getting a track feature
def get_track_features(track_id):
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
        'id': current_track_info['id'],
        'name': current_track_info['track_name'],
        'artists': current_track_info['artists_list'],
        'popularity': current_track_info['popularity'],
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

# Sets the flag to false if time exceeds the duration_minutes
def timer(start_time, duration_minutes):
    global flag
    if time.perf_counter() - start_time > duration_minutes * 60:
        flag = False   


# Standby status monitor function
def status_monitor(duration_minutes=5):
    global current_track_info, player_state
    
    current_track_id = None
    last_checked_state = None
    start_time = time.perf_counter()
    
    # Run the while loop until flag
    flag = True
    while flag:
        timer(start_time, duration_minutes)

        player_state = get_player_state()
        if player_state is None:
            refresh_or_get_new_tokens()
            continue

        if player_state:
            current_track_info = get_current_track()
            if current_track_info is None:
                print("Error in getting current track info")
                refresh_or_get_new_tokens()
                continue
            else:
                if current_track_info['id'] != current_track_id or last_checked_state is False:
                    print(f"Playing {current_track_info['track_name']} by {current_track_info['artists']}")
                    current_track_id = current_track_info['id']
                last_checked_state = player_state

        if last_checked_state is None:
            print("Not playing anything")
            last_checked_state = False
        elif not player_state and last_checked_state:
            print("Player stopped")
            last_checked_state = player_state

        time.sleep(2)
