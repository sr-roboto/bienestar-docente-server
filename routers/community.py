from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.community import CommunityPostDB
from models.user import UserDB
from schemas.community import CommunityPostCreate, CommunityPostResponse
from services.auth_service import get_current_user

router = APIRouter(prefix="/api/community", tags=["community"])


@router.get("", response_model=List[CommunityPostResponse])
def get_community_posts(db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    """Get all community posts."""
    posts = db.query(CommunityPostDB).all()
    return posts


@router.post("", response_model=CommunityPostResponse)
def create_post(post: CommunityPostCreate, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    """Create a new community post."""
    db_post = CommunityPostDB(
        content=post.content,
        author=post.author if post.author else current_user.username,
        user_id=current_user.id
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post
