import os
import google.generativeai as genai
from config import GOOGLE_API_KEY

# Configure Gemini
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


SYSTEM_INSTRUCTION = """
Eres una IA de Bienestar Docente, conocida como el "Asistente Pedagógico Emocional". 
Tu objetivo es apoyar a los docentes en su bienestar emocional, gestión del estrés y planificación eficiente.

Tus funciones principales y guía de estilo son:

1. **Soporte en Crisis**: Si un docente menciona estar estresado, abrumado o haber tenido un mal día, ofrece INMEDIATAMENTE un ejercicio de respiración o mindfulness corto (máximo 2 minutos) o una técnica de "grounding". Sé muy empático.

2. **Asistente de Planificación con Bienestar**: Cuando te pidan ayuda para planificar, prioriza siempre el equilibrio vida-trabajo. Sugiere descansos, técnicas Pomodoro y estructuras que eviten el agotamiento (burnout).

3. **Monitor de Clima Emocional**: Pregunta sutilmente cómo se sienten si el contexto lo permite. Valida sus emociones ("Es normal sentirse así...").

4. **Tono**: Empático, cálido, profesional, motivador y no-juzgador. Eres un colega sabio y comprensivo.

NO actúes como un chatbot genérico. Mantente en personaje.
"""

def get_gemini_model():
    """Get the configured Gemini model."""
    # Use the system instruction to define the persona
    model = genai.GenerativeModel(
        "gemini-2.5-flash",
        system_instruction=SYSTEM_INSTRUCTION
    )
    return model

async def generate_ai_response(message: str, context: str = "general", tools: list = None) -> str:
    """Generate an AI response using Gemini."""
    model = get_gemini_model()
    
    if tools:
        # Enable function calling - note: system_instruction stays from get_gemini_model if supported, 
        # but re-instantiating might lose it depending on library version. 
        # Safest to pass it again if we re-instantiate.
        model = genai.GenerativeModel(
            "gemini-2.5-flash", 
            tools=tools,
            system_instruction=SYSTEM_INSTRUCTION
        )
    
    # Create chat session
    chat = model.start_chat(history=[])
    
    # Send message
    response = await chat.send_message_async(message)
    
    return response
