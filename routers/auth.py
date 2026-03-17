from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from models.user import UserDB
from schemas.user import UserCreate, UserResponse, Token
from services.auth_service import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)
from google_auth import google_sso
from config import ACCESS_TOKEN_EXPIRE_MINUTES, FRONTEND_URL

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    db_user = db.query(UserDB).filter((UserDB.username == user.username) | (UserDB.email == user.email)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = UserDB(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with username/email and password."""
    user = db.query(UserDB).filter(UserDB.username == form_data.username).first()
    if not user:
         # Try email login
         user = db.query(UserDB).filter(UserDB.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username if user.username else user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: UserDB = Depends(get_current_user)):
    """Get current user information."""
    return current_user


# Google Auth Router (separate to keep at root path)
google_router = APIRouter(prefix="/auth/google", tags=["google-auth"])


@google_router.get("")
async def google_login():
    """Redirects user to Google Login."""
    return await google_sso.get_login_redirect()


@google_router.get("/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle callback from Google."""
    try:
        # We need the raw access_token but verify_and_process only returns user info.
        # We'll temporarily monkeypatch openid_from_response to capture the raw token data.
        raw_auth_data = {}
        original_openid_from_response = google_sso.openid_from_response

        async def intercepted_openid_from_response(response, session=None):
            raw_auth_data.update(response)
            return await original_openid_from_response(response, session)

        # Apply the interceptor
        google_sso.openid_from_response = intercepted_openid_from_response
        
        try:
            user_google = await google_sso.verify_and_process(request)
            access_token = raw_auth_data.get("access_token")
            refresh_token = raw_auth_data.get("refresh_token")
        finally:
            # Restore the original method
            google_sso.openid_from_response = original_openid_from_response
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google Auth Error: {e}")

    # Check if user exists
    user = db.query(UserDB).filter(UserDB.email == user_google.email).first()
    
    if not user:
        user = UserDB(
            email=user_google.email,
            username=user_google.email.split("@")[0],
            google_id=user_google.id,
            avatar_url=user_google.picture,
            google_access_token=access_token,
            google_refresh_token=refresh_token
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.google_id = user_google.id
        user.avatar_url = user_google.picture
        user.google_access_token = access_token
        if refresh_token:
            user.google_refresh_token = refresh_token
        db.commit()

    access_token = create_access_token(data={"sub": user.username if user.username else user.email})
    
    return RedirectResponse(url=f"{FRONTEND_URL}/login/callback?token={access_token}")
