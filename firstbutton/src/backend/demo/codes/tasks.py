import os
import mysql.connector
from celery_app import celery
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from prometheus_client import Histogram, Counter, Gauge, start_http_server

from startButton import integrated_file_reader, parse_response_to_events, google_calendar
from config import load_env

load_env()

# Celery worker 프로세스에서 메트릭 서빙 (uvicorn과 별도 포트)
try:
    start_http_server(9092)
except OSError:
    pass  # 이미 실행 중이면 무시

# Prometheus 메트릭 (schedule.py와 동일한 메트릭 재사용)
STEP_DURATION = Histogram(
    'upload_step_duration_seconds',
    'Duration of each upload pipeline step',
    ['step'],
    buckets=[0.1, 0.5, 1, 2, 3, 4, 5, 7.5, 10, 15, 30, 45, 60, 90, 120]
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

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", 3306))
}


def get_valid_creds(email: str):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()

        if not user_data:
            return None

        creds = Credentials(
            token=user_data['access_token'],
            refresh_token=user_data['refresh_token'],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            scopes=['https://www.googleapis.com/auth/calendar.events']
        )

        if creds.expired:
            print(f"🔄 {email}님의 토큰 만료됨. 갱신 중...")
            creds.refresh(Request())

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


@celery.task(bind=True, max_retries=2)
def process_upload(self, save_path, file_extension, base_name, event_color, user_email):
    CONCURRENT_UPLOADS.inc()
    try:
        # 1. AI 분석
        with STEP_DURATION.labels(step='ai_analysis').time():
            ai_response = integrated_file_reader(
                file_path=save_path,
                file_type=file_extension,
                file_name=base_name,
                color=event_color
            )

        # 2. 이벤트 파싱
        with STEP_DURATION.labels(step='parse_events').time():
            events_list = parse_response_to_events(ai_response)

        if not events_list:
            return {"status": "error", "message": "일정을 찾지 못했습니다."}

        # 3. Google Calendar 등록
        creds = get_valid_creds(user_email)
        if not creds:
            return {"status": "error", "message": "인증 정보를 찾을 수 없습니다. 다시 로그인해 주세요."}

        with STEP_DURATION.labels(step='calendar_register').time():
            google_calendar(events_list, creds)

        return {"status": "success", "count": len(events_list), "user": user_email}

    except Exception as e:
        UPLOAD_ERRORS.labels(error_type=type(e).__name__).inc()
        print(f"❌ Error processing {base_name}: {str(e)}")
        return {"status": "error", "message": str(e)}

    finally:
        CONCURRENT_UPLOADS.dec()
        if os.path.exists(save_path):
            os.remove(save_path)
