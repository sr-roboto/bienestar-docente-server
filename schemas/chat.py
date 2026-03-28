from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    context: str = "general"
