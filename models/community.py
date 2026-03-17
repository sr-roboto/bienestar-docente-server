from sqlalchemy import Column, Integer, String, Text, ForeignKey
from database import Base
from sqlalchemy.orm import relationship


class CommunityPostDB(Base):
    __tablename__ = "community_posts"

    id = Column(Integer, primary_key=True, index=True)
    author = Column(String, index=True)  # Keeping for backwards compatibility or display name
    content = Column(Text)
    likes = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    owner = relationship("UserDB", back_populates="posts")
