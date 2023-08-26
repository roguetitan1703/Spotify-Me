import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import os, sys

project_root = os.getcwd()
sys.path.append(f'{project_root}/data')
sys.path.append(f'{project_root}/libs')

from helpers_.log_helper import log_helper

class EveryNoiseScrapper:
    def __init__(self):
        self.base_url = "https://everynoise.com/"
        self.embedded_playlist_url = "https://embed.spotify.com/?uri=spotify:playlist:"
        self.logger = log_helper("EverNoiseScrapper_log.log", log_level='DEBUG')

    def get_uri_parameter(self, src_url):
        parsed_url = urlparse(src_url)
        query_params = parse_qs(parsed_url.query)
        if 'uri' in query_params:
            return query_params['uri'][0]
        return None

    def playlist_id_scrapper(self, genre):
        # Prepare the URL for the given genre
        url = f"{self.base_url}everynoise1d.cgi"
        params = {'root': genre, 'scope': 'all'}

        # Send a request to the website
        response = requests.get(
            url = f"{self.base_url}everynoise1d.cgi",
            params={
                'root': genre,
                'scope': 'all'
            }
        )
        
        # Error handling based on response status code
        if response.status_code == 200:
            self.logger.log_message("info", f"Successfully fetched data for genre '{genre}'")
            
            # Parse the HTML content to extract the embedded playlist URL
            soup = BeautifulSoup(response.content, 'html.parser')
            iframe_tag = soup.find('iframe', id='spotify')

            if iframe_tag:
                src = iframe_tag['src']
                uri_parameter = self.get_uri_parameter(src)
                if uri_parameter:
                    playlist_id = uri_parameter.split(":")[-1]
                    self.logger.log_message("info", f"Successfully extracted playlist ID for genre '{genre}', id:'{playlist_id}'")
                    return playlist_id
                else:
                    self.logger.log_message("error", f"URI parameter not found for genre '{genre}'")
                    return None
            else:
                self.logger.log_message("error", f"No embedded playlist found for genre '{genre}'")
                return None

        # if status_code == 401 or something like that 
        else: 
            self.logger.log_message("error", f"Failed to fetch data for genre '{genre}'")
            return None

if __name__ == '__main__':
    
    genre = input("Enter Genre")
    every_noise_scrapper = EveryNoiseScrapper()
    playlist_id = every_noise_scrapper.playlist_id_scrapper(genre)
    if playlist_id:
        embedded_playlist_url = f"{every_noise_scrapper.embedded_playlist_url}{playlist_id}"
        every_noise_scrapper.logger.log_message("info", f"Playlist ID: {playlist_id}")
        every_noise_scrapper.logger.log_message("info", f"Embedded Playlist URL: {embedded_playlist_url}")
