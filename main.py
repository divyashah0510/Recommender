import numpy as np
import pandas as pd
from flask import Flask, render_template, request
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import bs4 as bs
import urllib.request
import pickle
import requests
from flask import url_for
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
# import movie_recommendation_model
# import pickle
# model = movie_recommendation_model.MovieRecommendationModel('user_rating_matrix.csv')
from movie_recommendation_model import MovieRecommendationModel
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# load the nlp model and tfidf vectorizer from disk
filename = 'nlp_model.pkl'
clf = pickle.load(open(filename, 'rb'))
vectorizer = pickle.load(open('tranform.pkl','rb'))

app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this in production
app.config['MONGO_URI'] = 'mongodb+srv://akshayrathod205:pichi777@akshaycluster.ajwgb90.mongodb.net/recommend'  # Replace this with your MongoDB Atlas connection URI

jwt = JWTManager(app)   
mongo = PyMongo(app)

# Load the movie recommendation model
# with open('movie_recommendation_model.pkl', 'rb') as f:
#     loaded_model = pickle.load(f)

loaded_model = MovieRecommendationModel('user_rating_matrix.csv')

# Define the registration schema
registration_schema = {
    'username': str,
    'password': str,
    'ratings': dict,
    'new_user_id': int
}


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    ratings={}
    new_user_id=0
    confirm_password = data.get('confirm_password')

    if not username or not password or not confirm_password:
        return jsonify({'message': 'All fields are required'}), 400

    if password != confirm_password:
        return jsonify({'message': 'Passwords do not match'}), 400

    if mongo.db.users.find_one({'username': username}):
        return jsonify({'message': 'Username already exists'}), 400

    hashed_password = generate_password_hash(password)
    mongo.db.users.insert_one({'username': username, 'password': hashed_password ,'ratings':ratings,'new_user_id':new_user_id})

    return jsonify({'message': 'User created successfully'}), 201



# @app.route('/register', methods=['POST'])
# def register():
#     data = request.get_json()
    
#     # Validate the registration data against the schema
#     for field, field_type in registration_schema.items():
#         if field not in data or not isinstance(data[field], field_type):
#             return jsonify({'message': f'Field "{field}" is required and must be of type {field_type}'}), 400

#     # Check if the username already exists
#     if mongo.db.users.find_one({'username': data['username']}):
#         return jsonify({'message': 'Username already exists'}), 400

#     # Hash the password
#     hashed_password = generate_password_hash(data['password'])

#     # Insert the user document into the database
#     user_data = {
#         'username': data['username'],
#         'password': hashed_password,
#         'ratings': data['ratings'],
#         'new_user_id': data['new_user_id']
#     }
#     mongo.db.users.insert_one(user_data)

#     return jsonify({'message': 'User created successfully'}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    user = mongo.db.users.find_one({'username': username})

    if not user or not check_password_hash(user['password'], password):
        return jsonify({'message': 'Invalid username or password'}), 401

    access_token = create_access_token(identity=str(user['_id']))
    return jsonify({'access_token': access_token}), 200

# @app.route('/ratings', methods=['POST'])
# @jwt_required()
# def add_ratings():
#     current_user_id = get_jwt_identity()
#     data = request.get_json()
#     ratings = data.get('ratings')

#     if not ratings:
#         return jsonify({'message': 'No ratings provided'}), 400

#     # Determine the new user ID based on the existing user IDs in the user-item matrix
#     if not loaded_model.matrix.empty:
#         max_user_id = loaded_model.matrix.index.max()
#         new_ser_id = int(max_user_id) + 1
#     else:
#         new_user_id = 1



#     existing_document = mongo.db.users.find_one({'_id':current_user_id})
#     if existing_document:
#         # Add new fields to the existing document
#         existing_document['new_user_id'] = new_user_id
#         existing_document['ratings'] = ratings
#         # Update the existing document
#         mongo.db.users.update_one({'_id': existing_document['_id']}, {'$set': existing_document},upsert=True)

#     # Store new user ID in a separate collection
#     # mongo.db.users.update_one(
#     #     {'_id': current_user_id},  
#     #     {'$addToSet': {'ratings': ratings}, '$set': {'new_user_id': new_user_id}},
       
#     # )

#     # Update user ratings in the model
#     loaded_model.update_user_ratings(new_user_id, ratings)

#     return jsonify({'message': 'Ratings added successfully'}), 201



@app.route('/ratings', methods=['POST'])
@jwt_required()
def add_ratings():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    ratings = data.get('ratings')

    if not ratings:
        return jsonify({'message': 'No ratings provided'}), 400

    # Determine the new user ID based on the existing user IDs in the user-item matrix
    if not loaded_model.matrix.empty:
        max_user_id = loaded_model.matrix.index.max()
        new_user_id = int(max_user_id) + 1
    else:
        new_user_id = 1

    existing_document = mongo.db.users.find_one({'_id': ObjectId(current_user_id)})
    if existing_document:
        # Add new fields to the existing document
        # existing_document['new_user_id'] = new_user_id
        # existing_document['ratings'] = ratings
        # Update the existing document
       
        mongo.db.users.update_one({'_id': ObjectId(current_user_id)}, {'$set': {'ratings':ratings,'new_user_id':new_user_id}})
    else:
        return jsonify({'message' : 'update fail'})
        # Create a new document for the user
        # mongo.db.users.insert_one({'_id': current_user_id, 'new_user_id': new_user_id, 'ratings': ratings})

    # Update user ratings in the model
    loaded_model.update_user_ratings(new_user_id, ratings)

    return jsonify({'message': 'Ratings added successfully'}), 201

 

@app.route('/recommend', methods=['POST'])
@jwt_required()
def recommend():
    current_user_id = get_jwt_identity()

    # Retrieve the new_user_id of the currently logged-in user
    user = mongo.db.users.find_one({'_id': ObjectId(current_user_id)})
    if user:
        new_user_id = user.get('new_user_id')
        if new_user_id:
            # Call the recommend_movies function with the new_user_id
            recommended_movies = loaded_model.recommend_movies(user_id=2)
            return jsonify({'recommended_movies': recommended_movies}), 200
        else:
            return jsonify({'message': 'New user ID not found for the current user'}), 400
    else:
        return jsonify({'message': 'User not found'}), 404

    

# Example protected route
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    return jsonify({'message': 'You are authorized'}), 200



def create_similarity():
    data = pd.read_csv('main_data.csv')
    # creating a count matrix
    cv = CountVectorizer()
    count_matrix = cv.fit_transform(data['comb'])
    # creating a similarity score matrix
    similarity = cosine_similarity(count_matrix)
    return data,similarity

def rcmd(m):
    m = m.lower()
    try:
        data.head()
        similarity.shape
    except:
        data, similarity = create_similarity()
    if m not in data['movie_title'].unique():
        return('Sorry! The movie you requested is not in our database. Please check the spelling or try with some other movies')
    else:
        i = data.loc[data['movie_title']==m].index[0]
        lst = list(enumerate(similarity[i]))
        lst = sorted(lst, key = lambda x:x[1] ,reverse=True)
        lst = lst[1:11] # excluding first item since it is the requested movie itself
        l = []
        for i in range(len(lst)):
            a = lst[i][0]
            l.append(data['movie_title'][a])
        return l
    
# converting list of string to list (eg. "["abc","def"]" to ["abc","def"])
def convert_to_list(my_list):
    my_list = my_list.split('","')
    my_list[0] = my_list[0].replace('["','')
    my_list[-1] = my_list[-1].replace('"]','')
    return my_list

def get_suggestions():
    data = pd.read_csv('main_data.csv')
    return list(data['movie_title'].str.capitalize())



@app.route("/")
def index():
    json_url = url_for('static', filename='movie.json')
    return render_template('index.html', json_url=json_url)
@app.route("/home")
def home():
    suggestions = get_suggestions()
    return render_template('home.html',suggestions=suggestions)

@app.route("/similarity",methods=["POST"])
def similarity():
    movie = request.form['name']
    rc = rcmd(movie)
    if type(rc)==type('string'):
        return rc
    else:
        m_str="---".join(rc)
        return m_str

@app.route("/recommender",methods=["POST"])
def recommender():
    # getting data from AJAX request
    title = request.form['title']
    cast_ids = request.form['cast_ids']
    cast_names = request.form['cast_names']
    cast_chars = request.form['cast_chars']
    cast_bdays = request.form['cast_bdays']
    cast_bios = request.form['cast_bios']
    cast_places = request.form['cast_places']
    cast_profiles = request.form['cast_profiles']
    imdb_id = request.form['imdb_id']
    poster = request.form['poster']
    genres = request.form['genres']
    overview = request.form['overview']
    vote_average = request.form['rating']
    vote_count = request.form['vote_count']
    release_date = request.form['release_date']
    runtime = request.form['runtime']
    status = request.form['status']
    rec_movies = request.form['rec_movies']
    rec_posters = request.form['rec_posters']

    # get movie suggestions for auto complete
    suggestions = get_suggestions()

    # call the convert_to_list function for every string that needs to be converted to list
    rec_movies = convert_to_list(rec_movies)
    rec_posters = convert_to_list(rec_posters)
    cast_names = convert_to_list(cast_names)
    cast_chars = convert_to_list(cast_chars)
    cast_profiles = convert_to_list(cast_profiles)
    cast_bdays = convert_to_list(cast_bdays)
    cast_bios = convert_to_list(cast_bios)
    cast_places = convert_to_list(cast_places)
    
    # convert string to list (eg. "[1,2,3]" to [1,2,3])
    cast_ids = cast_ids.split(',')
    cast_ids[0] = cast_ids[0].replace("[","")
    cast_ids[-1] = cast_ids[-1].replace("]","")
    
    # rendering the string to python string
    for i in range(len(cast_bios)):
        cast_bios[i] = cast_bios[i].replace(r'\n', '\n').replace(r'\"','\"')
    
    # combining multiple lists as a dictionary which can be passed to the html file so that it can be processed easily and the order of information will be preserved
    movie_cards = {rec_posters[i]: rec_movies[i] for i in range(len(rec_posters))}
    
    casts = {cast_names[i]:[cast_ids[i], cast_chars[i], cast_profiles[i]] for i in range(len(cast_profiles))}

    cast_details = {cast_names[i]:[cast_ids[i], cast_profiles[i], cast_bdays[i], cast_places[i], cast_bios[i]] for i in range(len(cast_places))}

    # web scraping to get user reviews from IMDB site
    sauce = urllib.request.urlopen('https://www.imdb.com/title/{}/reviews?ref_=tt_ov_rt'.format(imdb_id)).read()
    soup = bs.BeautifulSoup(sauce,'lxml')
    soup_result = soup.find_all("div",{"class":"text show-more__control"})

    reviews_list = [] # list of reviews
    reviews_status = [] # list of comments (good or bad)
    for reviews in soup_result:
        if reviews.string:
            reviews_list.append(reviews.string)
            # passing the review to our model
            movie_review_list = np.array([reviews.string])
            movie_vector = vectorizer.transform(movie_review_list)
            pred = clf.predict(movie_vector)
            reviews_status.append('Good' if pred else 'Bad')

    # combining reviews and comments into a dictionary
    movie_reviews = {reviews_list[i]: reviews_status[i] for i in range(len(reviews_list))}     

    # passing all the data to the html file
    return render_template('recommend.html',title=title,poster=poster,overview=overview,vote_average=vote_average,
        vote_count=vote_count,release_date=release_date,runtime=runtime,status=status,genres=genres,
        movie_cards=movie_cards,reviews=movie_reviews,casts=casts,cast_details=cast_details)

@app.route("/contact")
def contact():
    return render_template('contact.html')




if __name__ == '__main__':
    app.run(debug=True)
