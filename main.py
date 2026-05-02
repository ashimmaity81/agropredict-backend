
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pickle
import numpy as np
import os
from dotenv import load_dotenv

# Routers
from auth import router as auth_router
from chatbot import router as chatbot_router
from translate_route import router as translate_router   # ← NEW

from datetime import datetime
from datetime import timezone
from database import recommendations_collection

# -----------------------------
# Load Environment Variables
# -----------------------------
load_dotenv()

# -----------------------------
# Initialize FastAPI App
# -----------------------------
app = FastAPI()

# -----------------------------
# Enable CORS (for React)
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://agropredict06.netlify.app","https://agropredict06lpu.netlify.app","*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Include Routers
# -----------------------------
app.include_router(chatbot_router)
app.include_router(auth_router, prefix="/api/auth")
app.include_router(translate_router, prefix="/api")     # ← NEW  →  POST /api/translate

# -----------------------------
# Root Route
# -----------------------------
@app.get("/")
def home():
    return {"message": "AgroPredict Backend Running 🚀"}

# -----------------------------
# Load ML Model
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model_path    = os.path.join(BASE_DIR, "models", "crop_model.pkl")
encoder_path  = os.path.join(BASE_DIR, "models", "label_encoder.pkl")

model   = pickle.load(open(model_path,   "rb"))
encoder = pickle.load(open(encoder_path, "rb"))

# -----------------------------
# Input Schema
# -----------------------------
class CropInput(BaseModel):
    N: float
    P: float
    K: float
    temperature: float
    humidity: float
    ph: float
    rainfall: float

# -----------------------------
# Crop Routes
# -----------------------------
@app.get("/crops")
def get_crops():
    crops = sorted(encoder.classes_.tolist())
    return {"crops": crops}


@app.post("/predict")
def predict(data: CropInput):
    try:
        features = [data.N, data.P, data.K,
                    data.temperature, data.humidity,
                    data.ph, data.rainfall]
        input_array = np.array(features).reshape(1, -1)
        prediction  = model.predict(input_array)
        crop_name   = encoder.inverse_transform(prediction)[0]
        return {"recommended_crop": crop_name}
    except Exception as e:
        return {"error": str(e)}


# -----------------------------
# History Routes
# -----------------------------
@app.post("/save-recommendation")
def save_recommendation(data: dict):
    try:
        recommendations_collection.insert_one({
            "email":       data["email"],
            "crop":        data["crop"],
            "N":           data["N"],
            "P":           data["P"],
            "K":           data["K"],
            "temperature": data["temperature"],
            "humidity":    data["humidity"],
            "ph":          data["ph"],
            "rainfall":    data["rainfall"],
            "createdAt": datetime.now(timezone.utc)
        })
        return {"message": "Saved successfully"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/history/{email}")
def get_history(email: str):
    try:
        data = list(
            recommendations_collection
            .find({"email": email})
            .sort("createdAt", -1)
        )
        for record in data:
            if "_id" in record:
                record["_id"] = str(record["_id"])
            if "createdAt" in record and hasattr(record["createdAt"], "isoformat"):
                record["createdAt"] = record["createdAt"].isoformat() + "Z"
        return {"history": data}
    except Exception as e:
        return {"error": str(e)}


@app.delete("/history/{email}/{record_id}")
def delete_history_record(email: str, record_id: str):
    try:
        from bson import ObjectId
        result = recommendations_collection.delete_one({
            "email": email,
            "_id":   ObjectId(record_id)
        })
        if result.deleted_count == 1:
            return {"message": "Deleted successfully"}
    except Exception:
        pass

    from urllib.parse import unquote
    try:
        ts_str = unquote(record_id)
        result = recommendations_collection.delete_one({
            "email":     email,
            "createdAt": {"$lte": datetime.fromisoformat(ts_str.replace("Z", "+00:00"))}
        })
        if result.deleted_count >= 1:
            return {"message": "Deleted successfully"}
    except Exception:
        pass

    return {"error": "Record not found or could not be deleted"}