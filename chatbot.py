
from fastapi import APIRouter
from pydantic import BaseModel
from openrouter_service import generate_response, agri_expert_response

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

# 🔹 General Chat
@router.post("/chat")
def chat(req: ChatRequest):
    return {"reply": generate_response(req.message)}

# 🌾 Agriculture Chat
@router.post("/agri-chat")
def agri_chat(req: ChatRequest):
    return {"reply": agri_expert_response(req.message)}