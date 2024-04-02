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
CORS(app)

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this in production
app.config['MONGO_URI'] = ''  # Replace this with your MongoDB Atlas connection URI

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
#         new_user_id = int(max_user_id) + 1
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

if __name__ == '__main__':
    app.run(debug=True)
