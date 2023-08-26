
        # Normalize the co-occurrence matrix
        normalized_co_occurrence = co_occurrence_matrix / co_occurrence_matrix.sum(axis=1, keepdims=True)

        # Use graph algorithms (e.g., spectral clustering) to identify clusters of genres
        num_clusters_co_occurrence = 3  # Adjust the number of clusters as needed
        spectral_clustering_model = SpectralClustering(n_clusters=num_clusters_co_occurrence, affinity='precomputed', random_state=42)
        co_occurrence_clusters = spectral_clustering_model.fit_predict(normalized_co_occurrence)

        # Map genres to their respective co-occurrence clusters
        genres_co_occurrence_clusters = {}
        for genre, cluster_label in zip(all_genres, co_occurrence_clusters):
            if cluster_label not in genres_co_occurrence_clusters:
                genres_co_occurrence_clusters[cluster_label] = []
            genres_co_occurrence_clusters[cluster_label].append(genre)

        return genres_co_occurrence_clusters

