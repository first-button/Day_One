# auth와 다르게 실제 기능 실행 시 사용 (파일 업로드 및 일정 등록)
import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Cookie, Body
from celery.result import AsyncResult
from prometheus_client import Histogram
from pydantic import BaseModel
from config import load_env

from tasks import process_upload, process_scrape
from startButton import scrape_webpage_schedule, parse_response_to_events, google_calendar
from tasks import get_valid_creds
from celery_app import celery


class ScrapeRequest(BaseModel):
    url: str
    color: str = "1"

# --- Prometheus 메트릭 정의 ---
UPLOAD_FILE_SIZE = Histogram(
    'upload_file_size_bytes',
    'Size of uploaded files',
    buckets=[1024, 10240, 102400, 1048576, 10485760]  # 1KB ~ 10MB
)

load_env()

# 이 라우터의 모든 주소 앞에 붙을 공통 주소
router = APIRouter(prefix="/api/schedule", tags=["Schedule"])


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
    unique_id = str(uuid.uuid4())[:8]
    save_path = f"temp_{unique_id}_{original_filename}"

    # 3. 파일 물리적 저장 (빠름, <100ms)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(uploaded_file.file, buffer)
    UPLOAD_FILE_SIZE.observe(os.path.getsize(save_path))

    # 4. Celery 태스크 큐에 넣고 즉시 반환
    task = process_upload.delay(save_path, file_extension, base_name, event_color, user_email)

    return {"status": "processing", "task_id": task.id}


@router.post("/scrape")
async def scrape_schedule(
    body: ScrapeRequest,
    user_email: str = Cookie(None)
):
    if not user_email:
        raise HTTPException(status_code=401, detail="로그인이 필요한 서비스입니다.")

    url = body.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL이 비어있습니다.")

    # URL에서 과목명 추출 (예: ~cse327 → cse327)
    import re
    match = re.search(r'~([a-zA-Z]{3}\d{3})', url)
    file_name = match.group(1).upper() if match else "webpage"

    # --- 로컬 테스트용 동기 처리 (배포 시 Celery 비동기로 전환 필요) ---
    try:
        ai_response = scrape_webpage_schedule(url=url, file_name=file_name, color=body.color)

        if ai_response.startswith("Error:"):
            raise HTTPException(status_code=400, detail=ai_response)

        events_list = parse_response_to_events(ai_response)
        if not events_list:
            raise HTTPException(status_code=400, detail="일정을 찾지 못했습니다.")

        creds = get_valid_creds(user_email)
        if not creds:
            raise HTTPException(status_code=401, detail="인증 정보를 찾을 수 없습니다. 다시 로그인해 주세요.")

        google_calendar(events_list, creds)

        return {"status": "success", "count": len(events_list)}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error scraping {url}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upload/status/{task_id}")
async def get_upload_status(task_id: str):
    result = AsyncResult(task_id, app=celery)

    if result.state == "PENDING":
        return {"status": "processing"}
    elif result.state == "SUCCESS":
        return result.result
    elif result.state == "FAILURE":
        return {"status": "error", "message": str(result.info)}
    else:
        return {"status": "processing"}
