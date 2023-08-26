from dotenv import load_dotenv, set_key
import base64
import requests
import json
import time
import os, sys
from urllib.parse import urlencode
import webbrowser
from pprint import pprint
import numpy as np
from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans, SpectralClustering  
from itertools import combinations


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
from Spotify_.SpotifyAPIHelper import SpotifyAPIHelper as SAH
from Bard_.BardAPI import TextAnalysis
from NetScrapper.EveryNoiseScrapper import EveryNoiseScrapper
import Spotify_.SpotifyUtility

INF = Spotify_.SpotifyUtility.ItemInfo()
TXA = TextAnalysis()
ENS = EveryNoiseScrapper()

logger_Data = log_helper("DatasetHelper_log.log", log_level='DEBUG')

class GenreVectorizer:
    def __init__(self, vector_size=100, window=5, min_count=1, workers=4):
        self.vector_size = vector_size
        self.window = window
        self.min_count = min_count
        self.workers = workers
        self.model_file = f'{model_path}/word2vec_model.bin'
       
        self.genre_file_path = f'{genres_path}/search_available_seed_genres.json'
        self.genres_data = read_file(self.genre_file_path)

        
        self.artists_genres_data_file = f'{user_data_path}/artists_genres_data.json'
        self.tracks_genres_data_file = f'{user_data_path}/tracks_genres_data.json'
        self.user_genres_data_file = f'{user_data_path}/user_genres_data.json'
        self.user_genres_cluster_file = f'{user_data_path}/user_genres_cluster.json'
        self.source_genres_cluster_file = f'{model_path}/source_genres_cluster.json'
        
        self.source_genres_cluster = read_file(self.source_genres_cluster_file)
        self.user_genres_data = read_file(self.user_genres_data_file)
        self.artists_genres_data = read_file(self.artists_genres_data_file)
        self.tracks_genres_data = read_file(self.tracks_genres_data_file)
        self.user_genres_cluster = read_file(self.user_genres_cluster_file,default=[])
               
        try:
            self.model = Word2Vec.load(self.model_file)
        except (FileNotFoundError, EOFError) as e:
            # Handle the exception (e.g., log the error, train a new model, etc.)
            logger_Data.log_message("error", f"Error loading Word2Vec model: {e}")
            self.train_word2vec_model()
        
        
    def get_similarity(self, genre1, genre2):
        genre_vector1 = self.get_genre_vector(genre1)
        genre_vector2 = self.get_genre_vector(genre2)

        if not genre_vector1 or not genre_vector2:
            raise ValueError("Genre vectors cannot be empty or None.")

        genre_vector1 = np.array(genre_vector1)
        genre_vector2 = np.array(genre_vector2)

        # Reshape the vectors to be 2D arrays
        genre_vector1 = genre_vector1.reshape(1, -1)
        genre_vector2 = genre_vector2.reshape(1, -1)

        # Calculate the cosine similarity between the two vectors
        similarity_score = cosine_similarity(genre_vector1, genre_vector2)

        return similarity_score[0][0]
    
    def train_word2vec_model(self):
        # Read the genres from the JSON file
        # Preprocess the genres (optional)
        # genres_data = self.preprocess_genres(genres_data)

        # Create a list of lists of genre tokens for training
        logger_Data.log_message("info","Training Model")
        genre_tokens = [genre.split() for genre in self.genres_data]

        # Train the Word2Vec model
        self.model = Word2Vec(
            sentences=genre_tokens,
            vector_size=self.vector_size,
            window=self.window,
            min_count=self.min_count,
            workers=self.workers
        )
        logger_Data.log_message("info","Model Trained")
        
        # Save the model to a file
        self.model.save(self.model_file)
        logger_Data.log_message("info",f"Model saved to {self.model_file}")
        
    def get_genre_vector(self, genre):
        if self.model is None:
            log_helper.log_message("error", "Word2Vec model has not been trained yet.")
            self.train_word2vec_model()

        genre_tokens = genre.split()
        genre_vector = None
        num_tokens = 0
        
        for token in genre_tokens:
            if token in self.model.wv:
                token_vector = self.model.wv[token]
                if genre_vector is None:
                    genre_vector = list(token_vector)
                else:
                    genre_vector = [x + y for x, y in zip(genre_vector, token_vector)]
                num_tokens += 1

        if num_tokens > 0:
            genre_vector = [x / num_tokens for x in genre_vector]
        else:
            log_helper.log_message("warning", "No valid tokens found in the genre. Returning None.")
            return None

        return genre_vector
        
    def cluster_genres(self, num_clusters=10):
        # Ensure that the genre vectors are available
        if not self.model:
            raise ValueError("Word2Vec model has not been trained yet.")

        # Get all genre names
        all_genres = self.genres_data

        # Create genre vectors using the trained Word2Vec model
        genre_vectors = [self.get_genre_vector(genre) for genre in all_genres]

        # Create the K-Means clustering model
        kmeans_model = KMeans(n_clusters=num_clusters, n_init= 15, random_state=42)

        # Fit the model to the genre vectors
        kmeans_model.fit(genre_vectors)

        # Get the cluster labels for each genre
        cluster_labels = kmeans_model.labels_

        # Build a dictionary to store the clusters and their genres
        kmeans_clusters = {}
        for genre, cluster_label in zip(all_genres, cluster_labels):
            if cluster_label not in kmeans_clusters:
                kmeans_clusters[cluster_label] = []
            kmeans_clusters[cluster_label].append(genre)

        kmeans_clusters = {int(key): value for key, value in kmeans_clusters.items()}
        return kmeans_clusters
    

    def build_genre_hierarchy(self, num_clusters_kmeans=10):
        # Cluster genres using K-Means
        kmeans_clusters = self.cluster_genres(num_clusters=num_clusters_kmeans)
        
        combined_clusters= {int(key): value for key, value in kmeans_clusters.items()}
        return combined_clusters
    
    def save_genre_hierarchy(self):        
        dump_file(self.source_genres_cluster_file, self.build_genre_hierarchy())
        logger_Data.log_message("info", f"Successfully saved the source_genres_cluster file to {self.source_genres_cluster_file}")
    

class PreClusteredGenreAnalyzer:
    def __init__(self):
        self.user_genres_cluster_file = f'{user_data_path}/user_genres_cluster.json'
        self.user_genre_co_occurence_matrix_file = f'{model_path}/user_genre_co_occurence_matrix.json'
        
        self.user_genre_co_occurence_matrix = read_file(self.user_genre_co_occurence_matrix_file, {})
        self.user_genres_cluster = read_file(self.user_genres_cluster_file, [])

    def _calculate_num_clusters(self):
        num_genres_per_cluster = [len(cluster) for cluster in self.user_genres_cluster]
        avg_genres_per_cluster = sum(num_genres_per_cluster) / len(num_genres_per_cluster)
        num_clusters_co_occurrence = int(np.ceil(avg_genres_per_cluster))
        return num_clusters_co_occurrence

    def genre_co_occurrence_analysis(self):
        all_genres = set()
        for genres_list in self.user_genres_cluster:
            all_genres.update(genres_list)

        all_genres = list(all_genres)
        co_occurrence_matrix = np.zeros((len(all_genres), len(all_genres)), dtype=int)

        for genres in self.user_genres_cluster:
            if len(genres) >= 2:
                for i in range(len(genres)):
                    genre1 = genres[i]
                    index1 = list(all_genres).index(genre1)
                    for j in range(i + 1, len(genres)):
                        genre2 = genres[j]
                        index2 = all_genres.index(genre2)
                        co_occurrence_matrix[index1][index2] += 1
                        co_occurrence_matrix[index2][index1] += 1

        co_occurrence_matrix = co_occurrence_matrix.tolist()

        genre_co_occurrence_dict = {}
        for i, genre in enumerate(all_genres):
            genre_co_occurrence_dict[genre] = {}
            for j, co_occurrence_count in enumerate(co_occurrence_matrix[i]):
                if co_occurrence_count > 0:
                    co_occurrence_genre = all_genres[j]
                    genre_co_occurrence_dict[genre][co_occurrence_genre] = co_occurrence_count

        return genre_co_occurrence_dict

    def find_most_frequent_co_occurrences(self, genre, num_most_frequent=1):
        if genre not in self.user_genre_co_occurence_matrix:
            return None  # Return None if the specified genre is not found in the matrix

        row = self.user_genre_co_occurence_matrix[genre]
        most_frequent_genres = sorted(row.items(), key=lambda x: x[1], reverse=True)[:num_most_frequent]
        return most_frequent_genres

    def save_genre_co_occurrence_matrix(self):
        dump_file(self.user_genre_co_occurence_matrix_file, self.genre_co_occurrence_analysis())
        logger_Data.log_message("info", f"Successfully saved the user_genre_co_occurence_matrix file to {self.user_genre_co_occurence_matrix_file}")    
    
    
def save_model_genre_hierarchy(model=False, genre_heirarchy=False):
    gv = GenreVectorizer()
    if model:
        gv.train_word2vec_model()
    if genre_heirarchy:
        gv.save_genre_hierarchy()

def save_user_data(user_model_data=False):
    if user_model_data:
        pa.save_genre_co_occurrence_matrix()

if __name__ == "__main__":
    # Create an instance of GenreVectorizer
    SAH.refresh_or_get_new_tokens()
    # save_model_genre_hierarchy(model=False, genre_heirarchy=False)
    # save_user_data(user_model_data=True)
    pa = PreClusteredGenreAnalyzer()
    print(pa.find_most_frequent_co_occurrences('sped up'))
    
    
    
    
    