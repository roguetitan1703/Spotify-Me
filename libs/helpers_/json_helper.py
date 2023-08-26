import json,os, sys
from pprint import pprint
project_root = os.getcwd()
sys.path.append(f'{project_root}/data')
sys.path.append(f'{project_root}/libs')


def dump_file(file, dump_this):
    # Dump to json
    with open(file, "w") as outfile:
        json.dump(dump_this, outfile,indent=4)

def read_file(file,default={}):
    # Read from json
    if os.path.getsize(file) == 0:
        return default
    
    else:
        with open(file) as data_file:
            data = json.load(data_file)
        return data

def count_data(dataset):
    leng = 0
    for key in dataset.keys():
        leng += len(dataset[key])
    return leng

if __name__ == "__main__":

    artists_genres_data_file = f'{project_root}/data/genres/artists_genres_data.json'
    tracks_genres_data_file = f'{project_root}/data/genres/tracks_genres_data.json'
    user_genres_data_file = f'{project_root}/data/genres/user_genres_data.json'

    artists_genres_data = read_file(artists_genres_data_file)
    tracks_genres_data = read_file(tracks_genres_data_file)
    user_genres_data = read_file(user_genres_data_file)

    print('track_genres_data: ',count_data(tracks_genres_data))
    print('artists_genres_data: ',count_data(artists_genres_data))
    l = 0
    for genre in user_genres_data.values():
        l += len(genre['artists']) if 'artists' in genre else 0
        l += len(genre['tracks']) if 'tracks' in genre else 0        
    print('User_genres_data: ',l)
    
    