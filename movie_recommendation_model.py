import pandas as pd
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
import pickle

class MovieRecommendationModel:
    def __init__(self, matrix_path):
        self.matrix_path = matrix_path
        # Load existing user-item matrix or create a new one
        try:
            self.matrix = pd.read_csv(matrix_path).set_index('userId')
        except FileNotFoundError:
            self.matrix = pd.DataFrame(columns=['userId'], dtype=int)

        # Initialize SVD algorithm
        self.svd = TruncatedSVD(n_components=100, random_state=42)

        if not self.matrix.empty:
            # Fit SVD to the existing user-item matrix
            self.svd.fit(self.matrix)

    def update_user_ratings(self, user_id, ratings):
        """
        Update user ratings in the model.

        Parameters:
            user_id (int): User ID.
            ratings (dict): Dictionary containing movie ratings, where keys are movie titles and values are ratings.
        """
        if user_id not in self.matrix.index:
            # # Add new user to the dataset
            # new_user_ratings = pd.DataFrame(ratings, index=[user_id])
            # self.matrix = pd.concat([self.matrix, new_user_ratings])

            # # Save updated matrix to file
            # user_rating_matrix.to_csv('user_rating_matrix.csv', index_label='userId')

            # Add new user to the dataset
            new_user_ratings = pd.DataFrame(ratings, index=[user_id])
            self.matrix = pd.concat([self.matrix, new_user_ratings])

            # Fill missing values with 0
            self.matrix = self.matrix.fillna(0)

            # Save updated matrix to file
            self.matrix.to_csv(self.matrix_path, index_label='userId')

        else:
            # Update existing user's ratings
            for movie, rating in ratings.items():
                self.matrix.at[user_id, movie] = rating

            # Re-fit SVD to the updated user-item matrix
            self.svd.fit(self.matrix)

    def recommend_movies(self, user_id):
        """
        Generate movie recommendations for the specified user.

        Parameters:
            user_id (int): User ID.

        Returns:
            list: List of recommended movie titles.
        """
        if user_id not in self.matrix.index:
            return []  # No recommendations available for new user

        # User similarity threshold
        user_similarity_threshold = 0.3

        # Number of similar users
        n = 10

        # Get user index
        user_index = self.matrix.index.get_loc(user_id)

        # Compute latent user-item matrix
        latent_matrix = self.svd.transform(self.matrix)

        # Calculate similarity between users
        user_similarity = cosine_similarity(latent_matrix)

        # Get similar users
        similar_users = user_similarity[user_similarity[:, user_index] > user_similarity_threshold][:n]

        # Calculate predicted ratings for unrated movies
        predicted_ratings = np.dot(latent_matrix[user_index], latent_matrix.T)

        # Filter out movies already watched by the user
        unwatched_movies_indices = np.where(self.matrix.iloc[user_index] == 0)[0]

        # Ensure unwatched_movies_indices are valid
        valid_indices = np.intersect1d(unwatched_movies_indices, np.arange(len(predicted_ratings)))

        if len(valid_indices) == 0:
            return []  # No recommendations available

        # Get predicted ratings for unwatched movies
        unwatched_movies_predicted_ratings = predicted_ratings[valid_indices]

        # Get indices of top recommended movies
        m = 10  # Number of top movies to recommend
        top_movie_indices = valid_indices[np.argsort(unwatched_movies_predicted_ratings)[-m:]]

        # Get titles of top recommended movies
        top_movies = self.matrix.columns[top_movie_indices]

        return top_movies.tolist()
    
model = MovieRecommendationModel('user_rating_matrix.csv')
    
with open('movie_recommendation_model.pkl', 'wb') as f:
    pickle.dump(model, f)