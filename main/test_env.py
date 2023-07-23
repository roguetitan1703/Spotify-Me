import sys
import os, re

# Get the absolute path to the project's root directory
project_root = os.getcwd()
# print(f'Project root: {project_root}')
# Add the project's root directory to the Python path
sys.path.append(f'{project_root}/data')
sys.path.append(f'{project_root}/libs')

from helpers_ import json_helper as j
from helpers_ import log_helper as l

s = """
Sure, here are the relevant track features that I would set for the user\'s playlist:\n\n```\n{\n    "danceability": 0.9,\n    "energy": 0.9,\n    "valence": 0.9,\n    "tempo": 120,\n    "popularity": 80\n}\n```\n\nI would set these features based on the following information from the user\'s description:\n\n* They want the playlist to be upbeat and high energy, so I would set the danceability, energy, and valence features to high values.\n* They want the playlist to be uplifting, so I would also set the valence feature to a high value.\n* They want to dance around in their room and pretend they\'re a main character in a rom com, so I would set the tempo feature to a high value.\n* They don\'t specify a preference for popularity, so I would set the popularity feature to an average value.\n\nI would also consider the following factors when setting the track features:\n\n* The genre of music that the user typically listens to.\n* The specific songs that the user has liked or saved in the past.\n* The time of day that the user will be listening to the playlist.\n\nBy taking all of these factors into account, I can generate a playlist that is personalized to the user\'s preferences and will help them to achieve their desired mood.\n\nHere are some additional notes about the track features that I set:\n\n* Danceability is a measure of how suitable a track is for dancing. A track with a high danceability score will have a strong beat and a clear rhythm.\n* Energy is a measure of how active and exciting a track is. A track with a high energy score will be loud, fast, and have a lot of dynamic range.\n* Valence is a measure of how positive or negative a track sounds. A track with a high valence score will sound happy and upbeat, while a track with a low valence score will sound sad or angry.\n* Tempo is the speed of a track. A track with a high tempo will be fast, while a track with a low tempo will be slow.\n* Popularity is a measure of how popular a track is. A track with a high popularity score will have been listened to by a lot of people.\n\nI hope this helps!"""

import ast
import re

class test:
    def __init__(self):
        self.rec_avail_genre_list = ''
        self.rec_avail_genre_list = ''


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


test = test()

print(test.parser(s,is_dict=True))