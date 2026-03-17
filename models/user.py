from sqlalchemy import Column, Integer, String
from database import Base
from sqlalchemy.orm import relationship


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=True)  # Nullable for purely Google auth
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)  # Null for Google auth
    google_id = Column(String, unique=True, index=True, nullable=True)
    google_access_token = Column(String, nullable=True)
    google_refresh_token = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)

    posts = relationship("CommunityPostDB", back_populates="owner")
    moods = relationship("MoodEntryDB", back_populates="owner")
