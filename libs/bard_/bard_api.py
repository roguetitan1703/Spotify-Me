from bardapi import Bard
import re
from dotenv import load_dotenv, set_key
import base64
import requests
import json
import time
from pprint import pprint
import os, sys
from urllib.parse import urlencode
import webbrowser
project_root = os.getcwd()
sys.path.append(f'{project_root}/data')
sys.path.append(f'{project_root}/libs')
from helpers_.json_helper import read_file, dump_file
from helpers_.log_helper import log_helper


# Setting logger

# loading environment variables


# Making a class bard for our functionality 
class bard:
    def __init__(self, bard_api_key=None,language='en'):
       
        # Setting path
        self.project_root = os.getcwd()
        self.data_path = f'{self.project_root}/data'
        self.libs_path = f'{self.project_root}/libs'
        
        # Loading environment variable  
        self.env_file = env_file = f'{self.data_path}/.env'
        load_dotenv(env_file)

        # Loading data files variables
        self.extracted_genres_file = f'{self.data_path}/extracted_genres.json'
        self.bard_prompts = read_file(f'{self.data_path}/bard_prompts.json')
        self.available_genre_seeds = read_file(f'{self.data_path}/available_genre_seeds.json')
        
        # Setting logger
        self.logger_bard_api = log_helper("bard_api_log.log", log_level='DEBUG')

        # Setting bard
        self.bard_api_key = bard_api_key or os.getenv('BARD_API_KEY')
        self.language = language
        self.bard = Bard(self.bard_api_key,language=self.language)



    # A parser for extracting the genres array from the raw_genres text
    def parser(self,raw_data):
        if raw_data:
            '''
            splitting the raw data into a list of strings
            and then removing the '`' and \n from the raw_data seperating the lines
            and then removing empty strings from the list
            and then finds the string bound between 'string'
            and then returns the list of genres
            '''
            
            # removes the '`' and \n from the raw_data seperating the lines
            data = re.split("`|\n",raw_data)

            # removes empty strings from the list
            data = [x for x in data if x]

            # finds the string bound between 'string'
            genres = re.findall("'(.*?)'",data[-1])

            # filtering out the genres that are not in the available_genre_seeds
            # to store the valid genres
            valid_genres = []
            # to store the invalid genres
            invalid_genres = []
            
            for genre in genres:
                if genre in self.available_genre_seeds:
                    valid_genres.append(genre)
                else:
                    invalid_genres.append(genre)
            
            return valid_genres
   

    # to extract the genres from the descriptive text about the playlist
    def extract_genres_from_text(self, text, qty=5):
        # pushing the descriptive text about the playlist into the bard
        prompt1 = self.bard_prompts['TEXT_BREAKDOWN_INTO_GENRES'].format(num_genres=qty, text=text, genres_seeds=self.available_genre_seeds)
        response1 = self.bard.get_answer(prompt1)

        # collecting raw_responses which contains the list of genres extracted along with other amounts text
        raw_responses = [choice['content'][0] for choice in response1['choices']]
        
        # pushing the raw_responses into the bard again to remove information and only get the genres
        prompt2 = self.bard_prompts['GENRES_EXTRACTION'].format(raw_genres=raw_responses[0])
        response2 = self.bard.get_answer(prompt2)

        # parsing the raw_genres text to get the list of genres and dumping it into a file
        raw_genres = [choice['content'][0] for choice in response2['choices']]
        self.extracted_genres = self.parser(raw_genres[0])
        dump_file(self.extracted_genres_file,self.extracted_genres)




if __name__ == '__main__':
    bard_ap = bard()
    text = input('Enter text: ')
    bard_ap.extract_genres_from_text(text)
    print(bard_ap.extracted_genres)