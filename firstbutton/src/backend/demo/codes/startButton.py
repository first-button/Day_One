import os
import google.generativeai as genai
from PIL import Image
import json
import hashlib

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

# 1. 설정 및 모델 로드
SCOPES = ['https://www.googleapis.com/auth/calendar']
GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# AI 프롬프트 설정
PROMPT_TEMPLATE = "Summarize all the academic schedules from this {file} file and organize them into a JSON format in English. \
                However, make sure to strictly comply with the following requirements: \
                1. Things to be excluded: TA office hour, professor office hour, assignment release date. \
                2. Things to be included: quiz, midterm, final exam, any kind of project deadlines, assignment submission deadlines, no class, holiday, reading day, any kind of breaks.\
                3. Do not contain any other information except the schedule information.\
                4. Finally, the keys of JSON object must be: summary, location, description, colorId, start, end.\
                5. **The start key and end key must be a dictionary object with only the 'date' key (YYYY-MM-DD format). Do NOT include 'timeZone' or 'dateTime'. The 'end' date must be one day after the 'start' date to ensure it is displayed as an all-day event.** \
                    For example: **'start': {{'date': '2025-09-01'}}, 'end': {{'date': '2025-09-02'}}**. \
                6. If same schedule lasts for couple of consecutive days, you must not make those separately, but make them in one object.\
                    For example, if the semester break is from June 1 to June 10, then the start date must be June 1 and the end date must be June 11.\
                7. The colorId field must be set to {colorId}.\
                8. The summary field must have the file name \"{name}\" at the beginning with brackets wrapped. But if the schedule is related to one of these three categories: holiday, semester break, no class, then do not include the file name.\
                9. The description field must have the brief description of the schedule in 3 ~ 4 words. If a particular schedule has a description in the {file}, use that description. But if not, make the description on your own within 3 ~ 4 words. \
                10. If the schedule is related to one of these categories: holiday, semester break, no class, then choose one of them and include it in the description. \
                11. The output must be a valid JSON format only, without any additional words." 

# 2. 핵심 로직 함수들

def integrated_file_reader(file_path, file_type, file_name, color):
    """파일을 읽어 Gemini AI를 통해 일정 JSON 텍스트 생성"""
    try:
        if file_type in [".jpg", ".jpeg", ".png"]:
            processed_file = Image.open(file_path)
        elif file_type == ".pdf":
            processed_file = genai.upload_file(path=file_path, display_name="syllabus PDF")
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {file_type}")
            
    except FileNotFoundError:
        return f"오류: '{file_path}' 경로에서 파일을 찾을 수 없습니다."
        
    file_prompt = PROMPT_TEMPLATE.format(file=file_type, name=file_name, colorId=color)
    response = model.generate_content([processed_file, file_prompt])
    return response.text

def parse_response_to_events(response_text):
    """AI의 텍스트 응답에서 JSON 배열을 추출하여 파싱"""
    if not response_text:
        raise ValueError("AI 응답이 비어있습니다.")
    
    start = response_text.find('[')
    end = response_text.rfind(']')
    if start == -1 or end == -1 or end <= start:
        return []

    candidate = response_text[start:end+1]
    data = json.loads(candidate)
    
    return data if isinstance(data, list) else [data]

def google_calendar(events_list, credentials):
    if not credentials:
        print("❌ 인증 정보가 없습니다. 일정을 등록할 수 없습니다.")
        return
            
    try:
        service = build('calendar', 'v3', credentials=credentials)
        common_events = [e for e in events_list if is_common_event(e)]

        # 2) 공통 이벤트가 있으면, 해당 기간 내 기존 이벤트를 "한 번에" 조회해서 dedupeKey set 만들기
        existing_keys = set()
        if common_events:
            min_start = min(e["start"]["date"] for e in common_events)  # YYYY-MM-DD라 문자열 min/max 가능
            max_end = max(e["end"]["date"] for e in common_events)

            time_min = f"{min_start}T00:00:00Z"
            time_max = f"{max_end}T00:00:00Z"

            page_token = None
            while True:
                resp = service.events().list(
                    calendarId="primary",
                    timeMin=time_min,
                    timeMax=time_max,
                    showDeleted=False,
                    singleEvents=True,
                    maxResults=250,
                    pageToken=page_token
                ).execute()

                for item in resp.get("items", []):
                    key = (
                        item.get("extendedProperties", {})
                            .get("private", {})
                            .get("dedupeKey")
                    )
                    if key:
                        existing_keys.add(key)

                page_token = resp.get("nextPageToken")
                if not page_token:
                    break
                
        for event_data in events_list:
            try:
                if is_common_event(event_data):
                    dedupe_key = make_common_event_id(event_data)  # (이제는 'id'가 아니라 'key'로 사용)
                    event_data.setdefault("extendedProperties", {}) \
                              .setdefault("private", {})["dedupeKey"] = dedupe_key

                    
                    if dedupe_key in existing_keys:
                        print(f"중복 일정(이미 존재) 건너뜀: {event_data.get('summary')}")
                        continue
                    existing_keys.add(dedupe_key)
                
                service.events().insert(calendarId="primary", body=event_data).execute()
                print(f"✅ 일정 등록 완료: {event_data.get('summary')}")
                
            except HttpError as e:
                if e.resp.status == 409:
                    print(f"중복 일정 건너뜀: {event_data.get('summary')}")
                else: 
                    print(f"등록 오류: {event_data.get('summary')} - {e}")
        
    except HttpError as error:
        print(f"구글 서비스 연결 오류: {error}")

def is_common_event(event_data):
    """공통 일정(휴강, 방학 등)인지 확인하여 중복 방지 ID 부여 대상 선별"""
    description = event_data.get("description", "").lower()
    keywords = ["holiday", "break", "no class"] 
    return any(kw in description for kw in keywords)

def make_common_event_id(event_data):
    """공통 일정에 대한 고유 해시 ID 생성 (중복 등록 방지)"""
    start = event_data["start"]["date"].replace("-", "")
    end = event_data["end"]["date"].replace("-", "")
    summary_title = (event_data.get("summary", "").lower()).replace(" ", "")
    raw_id = f"{summary_title}{start}{end}"
    return hashlib.md5(raw_id.encode()).hexdigest()