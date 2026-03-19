import os
from datetime import datetime, timedelta

import mysql.connector
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from config import load_env

load_env()

router = APIRouter(prefix="/api/auth", tags=["Auth"])

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
DEFAULT_BACKEND_BASE_URL = "http://localhost:8000"
DEFAULT_FRONTEND_BASE_URL = "http://localhost:5173"
BACKEND_BASE_URL = (
    os.getenv("BACKEND_BASE_URL")
    or os.getenv("BASE_URL")
    or DEFAULT_BACKEND_BASE_URL
)
FRONTEND_BASE_URL = (
    os.getenv("FRONTEND_BASE_URL")
    or (
        DEFAULT_FRONTEND_BASE_URL
        if BACKEND_BASE_URL == DEFAULT_BACKEND_BASE_URL
        else BACKEND_BASE_URL
    )
)

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", 3306)),
}

CLIENT_CONFIG = {
    "web": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

# PKCE code_verifier 임시 저장 (state → code_verifier)
_code_verifiers = {}


def build_google_flow():
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES)
    flow.redirect_uri = f"{BACKEND_BASE_URL}/api/auth/callback"
    return flow


@router.get("/login")
def login():
    flow = build_google_flow()
    auth_url, state = flow.authorization_url(prompt="consent", access_type="offline")
    _code_verifiers[state] = flow.code_verifier
    return {"url": auth_url}


@router.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    if not code:
        raise HTTPException(status_code=400, detail="Google OAuth code가 없습니다.")

    flow = build_google_flow()
    flow.fetch_token(code=code, code_verifier=_code_verifiers.pop(state, None))
    credentials = flow.credentials

    user_info_service = build("oauth2", "v2", credentials=credentials)
    user_info = user_info_service.userinfo().get().execute()
    user_email = user_info.get("email")

    if not user_email:
        raise HTTPException(status_code=400, detail="사용자 이메일 정보를 가져오지 못했습니다.")

    expires_at = datetime.now() + timedelta(
        seconds=credentials.expiry.timestamp() - datetime.now().timestamp()
    )

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        sql = """
        INSERT INTO users (email, access_token, refresh_token, expires_at)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            access_token = VALUES(access_token),
            refresh_token = IFNULL(VALUES(refresh_token), refresh_token),
            expires_at = VALUES(expires_at)
        """
        val = (user_email, credentials.token, credentials.refresh_token, expires_at)

        cursor.execute(sql, val)
        conn.commit()
        print(f"DB 저장 완료: {user_email}")

    except mysql.connector.Error as err:
        print(f"DB 오류: {err}")
        raise HTTPException(status_code=500, detail="데이터베이스 저장 실패")

    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()

    response = RedirectResponse(url=f"{FRONTEND_BASE_URL}/")
    response.set_cookie(key="user_email", value=user_email, httponly=False)
    return response
