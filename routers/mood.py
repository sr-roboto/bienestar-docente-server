from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.mood import MoodEntryDB
from models.user import UserDB
from schemas.mood import MoodEntryCreate, MoodEntryResponse
from services.auth_service import get_current_user

router = APIRouter(prefix="/api/mood", tags=["mood"])


def format_mood(mood_db):
    """Format mood entry for response."""
    m = MoodEntryResponse.model_validate(mood_db)
    if mood_db.timestamp:
        m.timestamp = mood_db.timestamp.isoformat()
    return m


@router.get("", response_model=List[MoodEntryResponse])
def get_moods(db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    """Get all mood entries for current user."""
    moods = db.query(MoodEntryDB).filter(MoodEntryDB.user_id == current_user.id).all()
    return list(map(format_mood, moods))


@router.post("", response_model=MoodEntryResponse)
def log_mood(entry: MoodEntryCreate, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    """Log a new mood entry."""
    db_entry = MoodEntryDB(
        mood=entry.mood, 
        note=entry.note,
        user_id=current_user.id
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return format_mood(db_entry)
