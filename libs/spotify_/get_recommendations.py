from dotenv import load_dotenv, set_key
import base64
import requests
import json
import time
import os, sys
from urllib.parse import urlencode
import webbrowser

# Add the project's root directory to the Python path
project_root = os.getcwd()
sys.path.append(f'{project_root}/data')
sys.path.append(f'{project_root}/libs')

from helpers_.json_helper import read_file, dump_file
from helpers_.log_helper import log_helper

# Setting logger
logger_recommendations = log_helper("get_recommendations_log.log", log_level='DEBUG')

# loading environment variables
env_file = f'{project_root}/data/.env'
load_dotenv(env_file)

genre_file = f'{project_root}/data/available_genre_seeds.json'
available_genre_seeds = read_file(genre_file)

# Urls for getting data from spotify api
available_genre_seeds_url = os.getenv('GET_AVAILABLE_GENRE_SEEDS')
recommendations_url = os.getenv('GET_RECOMMENDATIONS')
current_user_profile_url = os.getenv('GET_CURRENT_USER_PROFILE')
user_id = ''
user_name = ''
# Tokens
access_token = os.getenv('ACCESS_TOKEN')


# Gets available genre seeds
def get_available_genre_seeds():
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
        update_seeds(available_genre_seeds,genre_file)        


    elif response.status_code == 401:
        # invalid access token
        json_resp = response.json()

        logger_recommendations.log_message('error', json_resp['error']['message'])
    
def update_seeds(value,file):
    dump_file(file, value)


# Get current user's id and name
def get_current_users_id():
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
    

# Updates environment variables 
def update_env(values=[]):
    if values:
        for key, value in values.items():
            set_key(env_file, key, value)


get_available_genre_seeds()