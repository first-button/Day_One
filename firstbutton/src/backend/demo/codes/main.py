import config  # Secrets Manager 로드 (다른 모듈보다 먼저 import)
import os
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from routers import schedule, auth

app = FastAPI(title="첫단추 API")

async def read_index():
    """메인 인덱스 페이지 반환"""
    return FileResponse(os.path.join(DIST_PATH, "index.html"))

async def serve_spa(catchall: str):
    """SPA 라우팅 대응 (404 방지)"""
    if catchall.startswith("api"):
        return Response(status_code=404)
    return FileResponse(os.path.join(DIST_PATH, "index.html"))

# 0. CORS 설정 (프론트엔드와 백엔드가 포트가 다를 경우 필수)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 실제 배포 시에는 특정 도메인만 허용하는 게 좋아요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. 라우터 연결 (API 정의가 먼저!)
app.include_router(auth.router)     # [추가] 로그인/콜백 담당
app.include_router(schedule.router) # 일정 추출/업로드 담당

# 2. 경로 설정 (dist 폴더 위치)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../../../dist"))


# 3. 정적 파일 마운트 (가장 아래에!)
if os.path.exists(DIST_PATH):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_PATH, "assets")), name="assets")

    # 경로 등록 (데코레이터 대신 직접 등록)
    app.get("/")(read_index)
    app.get("/{catchall:path}")(serve_spa)
else:
    print(f"⚠️ 경고: DIST_PATH를 찾을 수 없습니다.")
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)