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

from helpers_.json_helper import read_file
from helpers_.log_helper import log_helper

# Setting logger
logger_api = log_helper("api_helper_log.log", log_level='DEBUG')

# loading environment variables
env_file = f'{project_root}/data/.env'
load_dotenv(env_file)

# Urls used in connecting to spotify api
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')  
redirect_uri = os.getenv('REDIRECT_URI')
auth_code_url = os.getenv('GET_AUTHORIZATION_CODE_URL')
auth_code = os.getenv('AUTHORIZATION_CODE')

# Access scopes for modifying user's data or reading it 
access_scopes = read_file(f'{project_root}/data/modify_scopes.json')
scope = ' '.join(access_scopes['MODIFY_PLAYBACK_LISTENING_PLUS']+access_scopes["MODIFY_LIBRARY_PLAYLIST_PLUS"]+access_scopes["MODIFY_FOLLOW_PLUS"])

# Urls for getting data from spotify api
access_token_url = os.getenv('GET_ACCESS_TOKEN_URL')
current_track_url = os.getenv('GET_CURRENT_TRACK_URL')
playback_state_url = os.getenv('GET_PLAYBACK_STATE_URL')
track_features_url = os.getenv('GET_TRACK_FEATURES_URL')

# Tokens
refresh_token = os.getenv('REFRESH_TOKEN')
access_token = os.getenv('ACCESS_TOKEN')



# Function to get the authorization code from the user
def get_authorization_code():
    # Paste the link in your browser and get the code

    url = auth_code_url
    headers = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': scope
    }
    post_url = url + urlencode(headers)
    print('Opening your browser to get authorization code in 2 seconds..')
    time.sleep(2)
    webbrowser.open(post_url)


# Function to extract the authorization code from the redirected link
def extract_auth_code(redirected_link):
    code = redirected_link.split('?code=')[1]
    return code


# Function to get the access token and refresh token from the authorization code
def get_access_token():
    response = requests.post(
        access_token_url,
        data={
            'code': auth_code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        },
        headers={
            'Authorization': 'Basic ' + base64.b64encode((client_id + ':' + client_secret).encode('utf-8')).decode('utf-8')
        }
    )

    if response.status_code == 200:
        json_resp = response.json()
        access_token = json_resp['access_token']
        refresh_token = json_resp['refresh_token']
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'error': None
        }
    else:
        response_dict = json.loads(response.text)
        return response_dict
    

# Function to refresh the access token using the refresh token
def refresh_access_token():
    response = requests.post(
        access_token_url,
        data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        },
        headers={
            'Authorization': 'Basic ' + base64.b64encode((client_id + ':' + client_secret).encode('ascii')).decode('ascii')
        }
    )

    if response.status_code == 200:
        resp_json = response.json()
        access_token = resp_json['access_token']
        return {'access_token': access_token}
    else:
        response_dict = json.loads(response.text)
        return response_dict


# Function to set the access and refresh tokens
def set_tokens(token, access=True, refresh=True):
    if token:
        global access_token, refresh_token
        if access:
            access_token = token['access_token']
            logger_api.log_message('info', 'Access token is set.')
            set_key(env_file, 'ACCESS_TOKEN', access_token)
        if refresh:
            refresh_token = token['refresh_token']
            logger_api.log_message('info', 'Refresh token is set.')
            set_key(env_file, 'REFRESH_TOKEN', refresh_token)


# Function to refresh tokens or get new tokens if needed
def refresh_or_get_new_tokens():
    global auth_code
    token = refresh_access_token()

    if token.get('error') == 'invalid_grant':  # Means expired refresh token or invalid refresh token
        logger_api.log_message('error', 'Refresh token is invalid or expired. Please get new authorization code.')
        # Getting new tokens, first we have to renew auth code

        while True:
            get_authorization_code()
            redirected_url = input("Enter the link from your browser: ")
            auth_code = extract_auth_code(redirected_url)
            set_key(env_file, 'AUTHORIZATION_CODE', auth_code)
            logger_api.log_message('info', 'Authorization code is set.')
            token = get_access_token()

            if token.get('error') == 'invalid_grant':
                if token.get('error_description') in ['Invalid authorization code', 'Authorization code expired']:
                    logger_api.log_message('error', token.get('error_description'))
                    continue

            set_tokens(token)
            break
    else:
        set_tokens(token,refresh=False)


if __name__ == '__main__':
    print("Getting tokens")
    refresh_or_get_new_tokens()
    print("\n")
    print("Successfully retrieved tokens")
    
