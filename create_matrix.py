import pandas as pd

# Load movies and ratings CSV files
ratings = pd.read_csv('ratings.csv')
movies = pd.read_csv('movies.csv')

# Merge movies and ratings datasets
merged_data = pd.merge(ratings, movies, on='movieId', how='inner')

# Pivot the merged data to create the user-rating matrix
user_rating_matrix = merged_data.pivot_table(index='userId', columns='title', values='rating', fill_value=0)

# Save the user-rating matrix to a CSV file
user_rating_matrix.to_csv('user_rating_matrix.csv')

# Display the user-rating matrix
print(user_rating_matrix)