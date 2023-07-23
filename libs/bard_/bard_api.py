from bardapi import Bard
import re, ast
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


# Making a class bard for our functionality 
class bard:
    def __init__(self, bard_api_key=None,language='en'):
       
        # Setting path
        self.project_root = os.getcwd()
        self.data_path = f'{self.project_root}/data'
        self.libs_path = f'{self.project_root}/libs'
        self.genres_path = f'{self.data_path}/genres'
        self.track_features_path = f'{self.data_path}/track_features'
        
        # Loading environment variable  
        self.env_file = env_file = f'{self.data_path}/.env'
        load_dotenv(env_file)

        # Loading data files variables
        self.text_extracted_genres_file = f'{self.genres_path}/text_extracted_genre_seeds.json'
        self.search_available_genre_file = f'{self.genres_path}/search_available_genre_seeds.json'

        self.rec_avail_genre_list = read_file(f'{self.genres_path}/rec_avail_genre_seeds.json')
        self.bard_prompts = read_file(f'{self.data_path}/bard_prompts.json')
        self.track_featutes_list = read_file(f'{self.track_features_path}/track_features.json')
        self.track_featutes_meanings = read_file(f'{self.track_features_path}/track_features_meanings.json')
        
        # Setting logger
        self.logger_bard = log_helper("bard_api_log.log", log_level='DEBUG')

        # Setting bard
        self.bard_api_key = bard_api_key or os.getenv('BARD_API_KEY')
        self.language = language
        self.bard = Bard(self.bard_api_key,language=self.language)



    # A parser for extracting the genres array from the raw_genres text
    def parser(self, raw_data, is_array=False, is_dict=False, cross_check=False):
        '''
        This function checks if the genres passed in the function are in the rec_avail_genre list
        '''
        def cross_check_genres(genres):
            if cross_check:
                _genres = []
                for genre in genres:
                    if genre in self.rec_avail_genre_list:
                        _genres.append(genre)
                return _genres
            else:
                return genres

        if raw_data:
            '''
            splitting the raw data into a list of strings
            and then removing the '`' and \n from the raw_data separating the lines
            and then removing empty strings from the list
            and then finds the string bound between 'string'
            and then returns the list of genres
            '''

            # removes the '`' and \n from the raw_data separating the lines
            data = raw_data.split('`')
            data = [line.strip() for line in data if line.strip()]

            semi_parsed = ''.join(data)

            if is_array:
                try:
                    # finds the string bound between []
                    genres = re.findall(r'(\[.*?\])', semi_parsed)
                    return {
                        "parsed_value": cross_check_genres(ast.literal_eval(genres[0])),
                        "error": None
                    }

                except (SyntaxError, ValueError, IndexError):
                    # If there's any error in evaluating the data as a literal, try an alternative approach using find method
                    x = semi_parsed.find("[")
                    y = semi_parsed.find("]", x)
                    try:
                        # Try to evaluate the substring containing the list
                        return {
                            "parsed_value": cross_check_genres(ast.literal_eval(semi_parsed[x:y + 1])),
                            "error": None
                        }

                    except (SyntaxError, ValueError, IndexError):
                        # If still unsuccessful, handle the error or return a default value
                        return {
                            "parsed_value": [],
                            "error": "Error parsing as an array."
                        }

            elif is_dict:
                try:
                    # finds the string bound between {}
                    data_dict = re.findall(r'(\{.*?\})', semi_parsed)
                    return {
                        "parsed_value": cross_check_genres(ast.literal_eval(data_dict[0])),
                        "error": None
                    }

                except (SyntaxError, ValueError, IndexError):
                    # If there's any error in evaluating the data as a literal, try an alternative approach using find method
                    x = semi_parsed.find("{")
                    y = semi_parsed.find("}", x)
                    try:
                        # Try to evaluate the substring containing the dictionary
                        return {
                            "parsed_value": cross_check_genres(ast.literal_eval(semi_parsed[x:y + 1])),
                            "error": None
                        }

                    except (SyntaxError, ValueError, IndexError):
                        # If still unsuccessful, handle the error or return a default value
                        return {
                            "parsed_value": {},
                            "error": "Error parsing as a dictionary."
                        }

        return {
            "parsed_value": None,
            "error": "No data provided or invalid input type."
        }


    # A function to extract the genres recognised by spotify recommendations from the descriptive text
    def extract_rec_avail_genres_from_text(self, text, qty=10):
        # Push the descriptive text about the playlist into the Bard API
        prompt = self.bard_prompts['TEXT_BREAKDOWN_INTO_GENRES'].format(num_genres=qty, text=text, genres_seeds=self.rec_avail_genre_list)
        self.logger_bard.log_message("info", f"Prompt sent to Bard API [RAG]")
        response = self.bard.get_answer(prompt)

        # Check if the response contains valid data
        if 'choices' not in response or not response['choices']:
            self.logger_bard.log_message("error", "Invalid response from Bard API. Unable to extract genres [RAG]")
            return []
             
        # Extract the genres from the response and save them
        raw_genres_text = [choice['content'][0] for choice in response['choices']]
        parsed_data = self.parser(raw_genres_text[0],is_array=True, cross_check=True)
        
        if parsed_data['error']:
            self.logger_bard.log_message("error", f"Error in parsing the genres from the response [RAG]. Error: {parsed_data['error']}")
            return []
        
        self.logger_bard.log_message("info", f"Successfully extracted the genres extracted from the response [RAG]")
        return parsed_data['parsed_value']
    

    # To extract search available genres from the descriptive text
    def extract_search_avail_genres_from_text(self, text, qty=10):
        # Push the descriptive text about the playlist into the Bard API
        prompt = self.bard_prompts['TEXT_BREAKDOWN_INTO_GENRES_FREE_FORM'].format(num_genres=qty, text=text)
        self.logger_bard.log_message("info", f"Prompt sent to Bard API [SAG]")
        response = self.bard.get_answer(prompt)

        # Check if the response contains valid data
        if 'choices' not in response or not response['choices']:
            self.logger_bard.log_message("error", "Invalid response from Bard API. Unable to extract genres [SAG]")
            return []

        # Extract the genres from the response and save them
        raw_genres_text = [choice['content'][0] for choice in response['choices']]
        parsed_data = self.parser(raw_genres_text[0], is_array=True)

        if parsed_data['error']:
            self.logger_bard.log_message("error", f"Error in parsing the genres from the response [SAG]. Error: {parsed_data['error']}")
            return []
        
        self.logger_bard.log_message("info", f"Successfully extracted the genres extracted from the response [SAG]")
        return parsed_data['parsed_value']

    
    def extract_genres_from_text(self, text, qty=10):
        # Extract the genres from the descriptive text using both methods
        self.recommendation_avail_genres = self.extract_rec_avail_genres_from_text(text, qty)
        self.search_avail_genres = self.extract_search_avail_genres_from_text(text, qty)
        
        # Combine the extracted genres into a dictionary
        self.text_extracted_genre_seeds = {
            'recommendation_available_genres': self.recommendation_avail_genres,
            'search_available_genres': self.search_avail_genres
        }

        # Dump the extracted_genres into a file
        self.logger_bard.log_message("info", f"Successfully dumped the extracted_genres into the file")
        dump_file(self.text_extracted_genres_file, self.text_extracted_genre_seeds)


    
    def extract_track_features_from_text(self, text):
        # Extract the track features from the descriptive text
        prompt = self.bard_prompts['TEXT_BREAKDOWN_INTO_TRACK_FEATURES'].format(text=text,track_features=self.track_featutes_list,features_meaning=self.track_featutes_meanings)
        self.logger_bard.log_message("info", f"Prompt sent to Bard API [AF]")
        response = self.bard.get_answer(prompt)

        # check if the response contains valid data
        if 'choices' not in response or not response['choices']:
            self.logger_bard.log_message("error", "Invalid response from Bard API. Unable to extract track features [AF]")
            return {}
        
        # Extract the track features from the response and save them
        raw_features_text = [choice['content'][0] for choice in response['choices']]
        parsed_data = self.parser(raw_features_text[0], is_dict=True)

        if parsed_data['error']:
            self.logger_bard.log_message("error", f"Error in parsing the track features from the response [AF]. Error: {parsed_data['error']}")
            return {}
        
        self.logger_bard.log_message("info", f"Successfully extracted the track features extracted from the response [AF]")
        return parsed_data['parsed_value']

        

if __name__ == '__main__':
    bard_ap = bard()
    text = input('Enter text: ')
    # features = bard_ap.extract_track_features_from_text(text)
    bard_ap.extract_genres_from_text(text)