#최초 로그인 및 사용자 등록 시 사용 (로그인 버튼)
import os
from datetime import datetime, timedelta
import mysql.connector
from dotenv import load_dotenv
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

import os

# .env 파일에서 환경변수 로드
load_dotenv()

router = APIRouter(prefix="/api/auth", tags=["Auth"])

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", 3306))
}

# 구글 콘솔에서 받은 설정값
CLIENT_CONFIG = {
    "web": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

SCOPES = ['https://www.googleapis.com/auth/calendar.events', 'https://www.googleapis.com/auth/userinfo.email', 'openid'] 

#login 엔드포인트: 구글 로그인 페이지로 리다이렉트  
@router.get("/login")
def login():
    #사용자의 인증 과정을 관리하는 가이드
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES)
    flow.redirect_uri = f"{BASE_URL}/api/auth/callback" #로그인 완료 후 돌아올 주소 설정
    
    # access_type='offline'을 설정해야 refresh_token을 받을 수 있습니다.
    #구글의 진짜 로그인 페이지 URL
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline') 
    return {"url": auth_url}


#callback 엔드포인트: 구글이 로그인 후 리다이렉트하는 곳
# 1. 구글이 보내준 'code'를 쿼리 파라미터에서 추출.
# 2. Flow 객체를 다시 생성 (login 함수와 설정이 똑같아야 함)
# 3. 임시 코드를 '진짜 토큰'으로 교환
# 4. 토큰 정보를 추출.
@router.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES)
    flow.redirect_uri = f"{BASE_URL}/api/auth/callback"
    
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    # 2. 구글에서 사용자 이메일 정보 가져오기
    user_info_service = build('oauth2', 'v2', credentials=credentials)
    user_info = user_info_service.userinfo().get().execute()
    user_email = user_info.get("email")

    if not user_email:
        raise HTTPException(status_code=400, detail="사용자 정보를 가져올 수 없습니다.")

    # 3. 만료 시간 계산 (현재 시간 + 만료 초)
    # credentials.expiry는 보통 datetime 객체로 제공되지만, 수동 계산 시 아래와 같이 합니다.
    expires_at = datetime.now() + timedelta(seconds=credentials.expiry.timestamp() - datetime.now().timestamp())

    # 4. MySQL에 저장 (Upsert: 있으면 업데이트, 없으면 삽입)
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
        
        # refresh_token은 최초 1회만 제공되는 경우가 많으므로 IFNULL 처리를 해줍니다.
        val = (user_email, credentials.token, credentials.refresh_token, expires_at)
        
        cursor.execute(sql, val)
        conn.commit()
        
        print(f"✅ DB 저장 완료: {user_email}")

    except mysql.connector.Error as err:
        print(f"❌ DB 오류: {err}")
        raise HTTPException(status_code=500, detail="데이터베이스 저장 실패")
    
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

    # 5. 응답 처리 (쿠키에 이메일 저장하여 누구인지 식별)
    response = RedirectResponse(url=f"{BASE_URL}/")
    response.set_cookie(key="user_email", value=user_email, httponly=False)
    
    return response