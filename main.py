from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
import uuid
import pymongo

app = FastAPI()

origins = [
    "http://localhost:8081",
    "http://localhost:39863",
    "http://localhost:5000",
    "http://localhost:8000",
]


# Configure CORS to allow requests from your Flutter web app's domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Adjust based on the allowed HTTP methods
    allow_headers=["*"],  # You can specify specific headers if needed
)

class ParkingSpace(BaseModel):
    id: int
    name: str
    location: str
    description: str
    latitude: float
    longitude: float
    state: bool  

# Connect to MongoDB
client = AsyncIOMotorClient("mongodb://localhost:27017/")
db = client["parking_db"]
collection = db["parking_spaces"]


# Function to generate the next auto-incremented ID
async def get_next_auto_incremented_id():
    # Find the highest existing ID in the collection
    highest_id_doc = await collection.find_one({}, sort=[("id", pymongo.DESCENDING)])
    if highest_id_doc:
        highest_id = highest_id_doc["id"]
        return highest_id + 1
    else:
        return 1  # If there are no existing documents, start from 1

# Create a new parking space with an auto-incremented ID
@app.post("/parking_spaces/", response_model=ParkingSpace)
async def create_parking_space(space: ParkingSpace):
    # Generate the next auto-incremented ID
    next_id = await get_next_auto_incremented_id()
    
    # Set the ID in the parking space
    space.id = next_id

    # Set the initial state to True (parking space is available)
    space.state = True
    
    # Insert the parking space into the database
    inserted = await collection.insert_one(space.dict())
    
    return {**space.dict(), "_id": inserted.inserted_id}

# Get a list of all parking spaces
@app.get("/parking_spaces/", response_model=list[ParkingSpace])
async def get_parking_spaces():
    spaces = []
    async for doc in collection.find():
        space_dict = doc
        space_dict["id"] = space_dict.pop("_id")  # Rename _id to id
        spaces.append(ParkingSpace(**space_dict))
    return spaces

# Get a specific parking space by ID
@app.get("/parking_spaces/{space_id}", response_model=ParkingSpace)
async def get_parking_space(space_id: str):
    space = await collection.find_one({"_id": space_id})
    if not space:
        raise HTTPException(status_code=404, detail="Parking space not found")
    space["id"] = space.pop("_id")  # Rename _id to id
    return ParkingSpace(**space)

# Update a parking space by ID
@app.put("/parking_spaces/{space_id}", response_model=ParkingSpace)
async def update_parking_space(space_id: str, updated_space: ParkingSpace):
    existing_space = await collection.find_one({"_id": space_id})
    if not existing_space:
        raise HTTPException(status_code=404, detail="Parking space not found")
    
    # Rename id to _id to match the database field
    updated_space_dict = updated_space.dict()
    updated_space_dict["_id"] = updated_space_dict.pop("id")
    
    await collection.update_one({"_id": space_id}, {"$set": updated_space_dict})
    return updated_space

# Delete a parking space by ID
@app.delete("/parking_spaces/{space_id}", response_model=dict)
async def delete_parking_space(space_id: str):
    existing_space = await collection.find_one({"_id": space_id})
    if not existing_space:
        raise HTTPException(status_code=404, detail="Parking space not found")
    await collection.delete_one({"_id": space_id})
    return {"message": "Parking space deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
