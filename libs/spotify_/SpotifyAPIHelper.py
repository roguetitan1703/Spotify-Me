from dotenv import load_dotenv, set_key
import base64
import requests
import json
import time
import os, sys
from urllib.parse import urlencode
import webbrowser
import http.server
import socketserver, threading


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

from helpers_.json_helper import read_file
from helpers_.log_helper import log_helper

class SpotifyAPIHelper:
    # Load environment variables and initialize logger
    env_file = f'{spotifyapi_path}/.env'
    load_dotenv(env_file)

    # Urls used in connecting to Spotify API
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')  
    redirect_uri = os.getenv('REDIRECT_URI')
    auth_code_url = os.getenv('GET_AUTHORIZATION_CODE_URL')
    auth_code = os.getenv('AUTHORIZATION_CODE')

    # Access scopes for modifying user's data or reading it 
    access_scopes = read_file(f'{spotifyapi_path}/modify_scopes.json')
    scope = ' '.join(access_scopes['MODIFY_PLAYBACK_LISTENING_PLUS'] + 
                     access_scopes["MODIFY_LIBRARY_PLAYLIST_PLUS"] + 
                     access_scopes["MODIFY_FOLLOW_PLUS"])

    # Urls for getting data from Spotify API
    access_token_url = os.getenv('GET_ACCESS_TOKEN_URL')
    current_track_url = os.getenv('GET_CURRENT_TRACK_URL')
    playback_state_url = os.getenv('GET_PLAYBACK_STATE_URL')
    track_features_url = os.getenv('GET_TRACK_FEATURES_URL')

    # Tokens
    refresh_token = os.getenv('REFRESH_TOKEN')
    access_token = os.getenv('ACCESS_TOKEN')

    # Logger initialization
    logger_api = log_helper("SpotifyAPIHelper_log.log", log_level='DEBUG')

    
    @classmethod
    def start_local_server(cls):
        PORT = 8000
        Handler = http.server.SimpleHTTPRequestHandler

        # Create a custom handler to capture the authorization code
        class CustomHandler(Handler):
            def log_request(self, code='-', size='-'):
                # Override log_request method to disable logging of incoming requests
                pass
        
        
            def do_GET(self):
                # Extract the authorization code from the URL
                redirected_url = self.path
                cls.auth_code = cls.extract_auth_code(redirected_url)
                cls.logger_api.log_message('info', f'Authorization code is set: {cls.auth_code[:15]}--truncated')
                set_key(cls.env_file, 'AUTHORIZATION_CODE', cls.auth_code)

                # Respond to the user with a success message
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'Authorization code captured successfully. You can now close this window.')

        # Start the local web server
        with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
            print("Local web server started on port", PORT)
            cls.logger_api.log_message('info', 'Local web server started. Waiting for the authorization code.')

            # Open the browser to get the authorization code
            cls.get_authorization_code()

            # Wait for the redirected URL and handle it with a timeout
            httpd_thread = threading.Thread(target=httpd.handle_request)
            httpd_thread.start()
            httpd_thread.join(timeout=30)  # Set the timeout to 30 seconds

            if httpd_thread.is_alive():
                # If the thread is still alive, the server request timed out
                httpd.shutdown()
                print("Server request timed out.")
                cls.logger_api.log_message('error', 'Server request timed out.')
                # Handle the error and proceed with the authentication process accordingly
                # For example, you can retry or display an error message to the user.


    @classmethod
    def refresh_or_get_new_tokens(cls):
        cls.logger_api.log_message('info', 'Getting access token')
        token = cls.refresh_access_token()

        if token.get('error') == 'invalid_grant':  # Means expired refresh token or invalid refresh token
            cls.logger_api.log_message('error', 'Refresh token is invalid or expired. Need to get new authorization code.')
            # Getting new tokens, first we have to renew auth code

            cls.start_local_server()  # Start the local web server to capture the authorization code

            # Now we can proceed to get the access token
            token = cls.get_access_token()

            if token.get('error') == 'invalid_grant':
                cls.logger_api.log_message('error', token.get('error_description'))
        
            else:
                cls.set_tokens(token)
        else:
            cls.set_tokens(token, refresh=False)


    @classmethod
    def get_authorization_code(cls):
        # Paste the link in your browser and get the code
        url = cls.auth_code_url
        headers = {
            'client_id': cls.client_id,
            'response_type': 'code',
            'redirect_uri': cls.redirect_uri,
            'scope': cls.scope
        }
        post_url = url + urlencode(headers)
        webbrowser.open(post_url)
    
    
    @classmethod
    def extract_auth_code(cls, redirected_link):
        code = redirected_link.split('?code=')[1]
        cls.logger_api.log_message('info', f'Authorization code is extracted')
        return code

    @classmethod
    def get_access_token(cls):
        response = requests.post(
            cls.access_token_url,
            data={
                'code': cls.auth_code,
                'redirect_uri': cls.redirect_uri,
                'grant_type': 'authorization_code'
            },
            headers={
                'Authorization': 'Basic ' + base64.b64encode((cls.client_id + ':' + cls.client_secret).encode('utf-8')).decode('utf-8')
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

    @classmethod
    def refresh_access_token(cls):
        response = requests.post(
            cls.access_token_url,
            data={
                'grant_type': 'refresh_token',
                'refresh_token': cls.refresh_token
            },
            headers={
                'Authorization': 'Basic ' + base64.b64encode((cls.client_id + ':' + cls.client_secret).encode('ascii')).decode('ascii')
            }
        )

        if response.status_code == 200:
            resp_json = response.json()
            access_token = resp_json['access_token']
            return {'access_token': access_token}
        else:
            response_dict = json.loads(response.text)
            return response_dict

    @classmethod
    def set_tokens(cls, token, access=True, refresh=True):
        if token:
            if access:
                cls.access_token = token['access_token']
                cls.logger_api.log_message('info', 'Access token is set.')
                set_key(cls.env_file, 'ACCESS_TOKEN', cls.access_token)
            if refresh:
                cls.refresh_token = token['refresh_token']
                cls.logger_api.log_message('info', 'Refresh token is set.')
                set_key(cls.env_file, 'REFRESH_TOKEN', cls.refresh_token)

    @classmethod
    def current_access_token(self):
        return os.getenv('ACCESS_TOKEN')



if __name__ == '__main__':
    print("Getting tokens")
    SpotifyAPIHelper.refresh_or_get_new_tokens()
    print("\n")
    print("Successfully retrieved tokens")
