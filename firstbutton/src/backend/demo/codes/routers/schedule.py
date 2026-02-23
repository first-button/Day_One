# auth와 다르게 실제 기능 실행 시 사용 (파일 업로드 및 일정 등록)
import os
import shutil
import uuid
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Cookie
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from prometheus_client import Histogram, Counter, Gauge

# 상위 폴더에 있는 startButton을 가져옵니다.
from startButton import integrated_file_reader, parse_response_to_events, google_calendar

# --- Prometheus 메트릭 정의 ---
STEP_DURATION = Histogram(
    'upload_step_duration_seconds',
    'Duration of each upload pipeline step',
    ['step'],
    buckets=[0.1, 0.5, 1, 2.5, 5, 10, 15, 30, 45, 60, 90, 120]
)
UPLOAD_FILE_SIZE = Histogram(
    'upload_file_size_bytes',
    'Size of uploaded files',
    buckets=[1024, 10240, 102400, 1048576, 10485760]  # 1KB ~ 10MB
)
UPLOAD_ERRORS = Counter(
    'upload_errors_total',
    'Total upload errors',
    ['error_type']
)
CONCURRENT_UPLOADS = Gauge(
    'concurrent_uploads',
    'Number of uploads currently being processed'
)

load_dotenv()

# 이 라우터의 모든 주소 앞에 붙을 공통 주소
router = APIRouter(prefix="/api/schedule", tags=["Schedule"])

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", 3306))
}

# --- [추가] DB에서 유효한 토큰을 가져오는 함수 ---
def get_valid_creds(email: str):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 1. DB에서 해당 이메일의 토큰 정보 조회
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()

        if not user_data:
            return None

        # 2. 구글 Credentials 객체 생성
        creds = Credentials(
            token=user_data['access_token'],
            refresh_token=user_data['refresh_token'],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            scopes=['https://www.googleapis.com/auth/calendar.events']
        )

        # 3. 토큰이 만료되었는지 확인 후 필요 시 자동 갱신
        # credentials 객체 자체의 만료 확인 로직 사용
        if creds.expired:
            print(f"🔄 {email}님의 토큰 만료됨. 갱신 중...")
            creds.refresh(Request())
            
            # 4. 갱신된 새 토큰을 DB에 업데이트
            update_sql = "UPDATE users SET access_token = %s, expires_at = %s WHERE email = %s"
            cursor.execute(update_sql, (creds.token, creds.expiry, email))
            conn.commit()
            print(f"✅ {email}님의 새 토큰 DB 저장 완료")

        return creds

    except Exception as e:
        print(f"❌ DB 토큰 로드 중 오류: {e}")
        return None
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


@router.post("/upload")
async def upload_schedule(
    uploaded_file: UploadFile = File(...), 
    event_color: str = Form(...),
    user_email: str = Cookie(None)
):
    
    if not user_email:
        raise HTTPException(status_code=401, detail="로그인이 필요한 서비스입니다.")
    
    # 1. 파일 이름 관련 정보 추출
    original_filename = uploaded_file.filename
    base_name, file_extension = os.path.splitext(original_filename)
    file_extension = file_extension.lower()

    # 2. 서버 내 임시 저장 경로 설정 (중복 방지를 위해 UUID 사용)
    # 단순히 'temp_'를 붙이는 것보다 UUID를 써야 여러 명이 동시에 올릴 때 안 꼬입니다.
    # 클라우스 서버 구축 후 거기에 저장 할 예정임.
    unique_id = str(uuid.uuid4())[:8]
    save_path = f"temp_{unique_id}_{original_filename}"

    CONCURRENT_UPLOADS.inc()
    try:
        # 3. 파일 물리적 저장
        with STEP_DURATION.labels(step='file_save').time():
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(uploaded_file.file, buffer)
            UPLOAD_FILE_SIZE.observe(os.path.getsize(save_path))

        # 4. AI 분석 (가독성 있게 변수 전달)
        # 여기서 base_name은 AI가 일정 요약본 앞에 [파일명]을 붙일 때 사용됩니다.
        with STEP_DURATION.labels(step='ai_analysis').time():
            ai_response = integrated_file_reader(
                file_path=save_path,
                file_type=file_extension,
                file_name=base_name,
                color=event_color
            )

        # 5. 데이터 파싱 및 캘린더 등록
        with STEP_DURATION.labels(step='parse_events').time():
            events_list = parse_response_to_events(ai_response)

        if events_list:
            creds = get_valid_creds(user_email)
            if not creds:
                raise HTTPException(status_code=403, detail="인증 정보를 찾을 수 없습니다. 다시 로그인해 주세요.")

            with STEP_DURATION.labels(step='calendar_register').time():
                google_calendar(events_list, creds)
            return {"status": "success", "count": len(events_list), "user": user_email}

        return {"status": "error", "message": "일정을 찾지 못했습니다."}

    except Exception as e:
        UPLOAD_ERRORS.labels(error_type=type(e).__name__).inc()
        # 에러 발생 시 상세 로그 출력
        print(f"❌ Error processing {original_filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 내부 처리 오류: {str(e)}")

    finally:
        CONCURRENT_UPLOADS.dec()
        # 6. 작업 완료 후 임시 파일 삭제
        # 클라우드 서버에 저장 할 예정.
        if os.path.exists(save_path):
            os.remove(save_path)