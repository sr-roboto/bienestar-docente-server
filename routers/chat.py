from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import google.generativeai as genai
from database import get_db
from models.user import UserDB
from schemas.chat import ChatRequest
from services.auth_service import get_current_user
from config import GOOGLE_API_KEY

router = APIRouter(prefix="/api", tags=["chat"])

# Configure Gemini
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)



@router.post("/chat")
async def chat_endpoint(request: ChatRequest, current_user: UserDB = Depends(get_current_user)):
    """Chat with AI assistant."""
    if not GOOGLE_API_KEY:
        return {"response": f"Simulated AI: Hola {current_user.username}."}
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        chat = model.start_chat()
        
        system_instruction = f"Contexto: {request.context}. Usuario: {current_user.username}. Eres un asistente útil. Hoy es {datetime.now().isoformat()}."
        full_prompt = f"{system_instruction}\nUser: {request.message}"
        
        response = chat.send_message(full_prompt)
        
        return {"response": response.text}

    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "quota" in error_str.lower():
            print(f"Gemini Rate Limit Exceeded: {e}")
            return {"response": "⏳ El sistema de IA está saturado momentáneamente (límite de cuota gratuito). Por favor, intenta de nuevo en unos segundos."}
        
        print(f"Error calling Gemini: {e}")
        return {"response": f"Lo siento, hubo un error técnico: {str(e)}"}


