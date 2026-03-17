from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from models.user import UserDB
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
import datetime

def get_calendar_service(user: UserDB):
    if not user.google_access_token:
        return None
    
    creds = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET
    )
    
    return build('calendar', 'v3', credentials=creds)

def get_upcoming_events(user: UserDB, max_results=5):
    service = get_calendar_service(user)
    if not service:
        return []

    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          maxResults=max_results, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    return events

def create_event(user: UserDB, summary: str, start_time: str, end_time: str, description: str = None):
    service = get_calendar_service(user)
    if not service:
        return None

    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time, # ISO format
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'UTC',
        },
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    return event.get('htmlLink')
