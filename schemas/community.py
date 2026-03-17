from pydantic import BaseModel
from typing import Optional


class CommunityPostCreate(BaseModel):
    content: str
    author: Optional[str] = None


class CommunityPostResponse(BaseModel):
    id: int
    author: Optional[str]
    content: str
    likes: int
    user_id: Optional[int]

    class Config:
        from_attributes = True
