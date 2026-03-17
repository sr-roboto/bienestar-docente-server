import os
from fastapi_sso.sso.google import GoogleSSO
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI

google_sso = GoogleSSO(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    redirect_uri=GOOGLE_REDIRECT_URI,
    allow_insecure_http=True,
    scope=["openid", "email", "profile", "https://www.googleapis.com/auth/calendar.events"]
)
