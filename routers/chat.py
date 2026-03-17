from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import google.generativeai as genai
from database import get_db
from models.user import UserDB
from schemas.chat import ChatRequest, CalendarEventResponse
from services.auth_service import get_current_user
from calendar_service import create_event, get_upcoming_events
from config import GOOGLE_API_KEY

router = APIRouter(prefix="/api", tags=["chat"])

# Configure Gemini
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


def create_calendar_event_tool(summary: str, start_time: str, end_time: str):
    """Schedules an event in the user's Google Calendar.
    
    Args:
        summary: The title of the event.
        start_time: ISO format start time (e.g. 2023-10-27T10:00:00).
        end_time: ISO format end time.
    """
    pass  # This is just for Gemini's tool definition


@router.post("/chat")
async def chat_endpoint(request: ChatRequest, current_user: UserDB = Depends(get_current_user)):
    """Chat with AI assistant."""
    if not GOOGLE_API_KEY:
        return {"response": f"Simulated AI: Hola {current_user.username}."}
    
    try:
        model = genai.GenerativeModel("gemini-2.5-flash", tools=[create_calendar_event_tool])
        chat = model.start_chat()
        
        system_instruction = f"Contexto: {request.context}. Usuario: {current_user.username}. Eres un asistente útil. Tienes herramientas para agendar en Google Calendar. Si el usuario pide agendar, usa la herramienta. Hoy es {datetime.now().isoformat()}."
        full_prompt = f"{system_instruction}\nUser: {request.message}"
        
        response = chat.send_message(full_prompt)
        
        # Check for function call
        if response.candidates[0].content.parts[0].function_call:
            fc = response.candidates[0].content.parts[0].function_call
            if fc.name == "create_calendar_event_tool":
                args = fc.args
                result = create_event(current_user, args['summary'], args['start_time'], args['end_time'])
                
                if result:
                    tool_response = {"result": f"Event created: {result}"}
                else:
                    tool_response = {"result": "Error: Could not create event. User is not logged in with Google or has not granted calendar permissions."}

                # Send result back
                response = chat.send_message(
                    genai.protos.Content(
                        parts=[genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name="create_calendar_event_tool",
                                response=tool_response
                            )
                        )]
                    )
                )
                return {"response": response.text}

        return {"response": response.text}

    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "quota" in error_str.lower():
            print(f"Gemini Rate Limit Exceeded: {e}")
            return {"response": "⏳ El sistema de IA está saturado momentáneamente (límite de cuota gratuito). Por favor, intenta de nuevo en unos segundos."}
        
        print(f"Error calling Gemini: {e}")
        return {"response": f"Lo siento, hubo un error técnico: {str(e)}"}


@router.get("/calendar", response_model=List[CalendarEventResponse])
def get_calendar(db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    """Get upcoming calendar events."""
    events = get_upcoming_events(current_user)
    # Transform to response model
    res = []
    for e in events:
        start = e['start'].get('dateTime', e['start'].get('date'))
        end = e['end'].get('dateTime', e['end'].get('date'))
        res.append(CalendarEventResponse(
            id=e['id'],
            summary=e.get('summary', 'No Title'),
            start=start,
            end=end,
            link=e.get('htmlLink')
        ))
    return res
