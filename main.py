from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:45269",
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

# Define a Pydantic model for the parking space data, including position (latitude and longitude)
class ParkingSpace(BaseModel):
    name: str
    location: str
    description: str
    latitude: float
    longitude: float

# Connect to MongoDB
client = AsyncIOMotorClient("mongodb://localhost:27017/")
db = client["parking_db"]
collection = db["parking_spaces"]

# Create a new parking space
@app.post("/parking_spaces/", response_model=ParkingSpace)
async def create_parking_space(space: ParkingSpace):
    inserted = await collection.insert_one(space.dict())
    return {**space.dict(), "_id": inserted.inserted_id}

# Get a list of all parking spaces
@app.get("/parking_spaces/", response_model=list[ParkingSpace])
async def get_parking_spaces():
    spaces = []
    async for doc in collection.find():
        spaces.append(doc)
    return spaces

# Get a specific parking space by ID
@app.get("/parking_spaces/{space_id}", response_model=ParkingSpace)
async def get_parking_space(space_id: str):
    space = await collection.find_one({"_id": space_id})
    if not space:
        raise HTTPException(status_code=404, detail="Parking space not found")
    return space

# Update a parking space by ID
@app.put("/parking_spaces/{space_id}", response_model=ParkingSpace)
async def update_parking_space(space_id: str, updated_space: ParkingSpace):
    existing_space = await collection.find_one({"_id": space_id})
    if not existing_space:
        raise HTTPException(status_code=404, detail="Parking space not found")
    await collection.update_one({"_id": space_id}, {"$set": updated_space.dict()})
    return {**updated_space.dict(), "_id": space_id}

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
