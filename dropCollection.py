from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["parking_db"]

# Specify the name of the collection you want to drop
collection_name = "parking_spaces"

# Drop the collection
db[collection_name].drop()
