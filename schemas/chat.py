from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    context: str = "general"


class CalendarEventResponse(BaseModel):
    id: Optional[str] = None
    summary: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    link: Optional[str] = None
