import hashlib
import json
import os

import google.generativeai as genai
import pymupdf
from PIL import Image
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


load_dotenv()

# 1. 설정 및 모델 로드
SCOPES = ["https://www.googleapis.com/auth/calendar"]
GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

COMMON_PROMPT_RULES = """
1. Exclude TA office hour, professor office hour, and assignment release date.
2. Include quiz, midterm, final exam, project deadline, assignment submission deadline, no class, holiday, reading day, and any kind of break.
3. Do not include any information other than the events listed in item 2.
4. Each JSON object must contain exactly these keys:
   summary, location, description, colorId, start, end
5. The colorId field must be set to {color_id}.
6. The summary field must begin with [{file_name}] for course-specific events.
7. If the event is a holiday, semester break, or no class, do not include [{file_name}] in the summary.
8. The summary must be short and directly related to the event, about 2 to 3 words.
9. The description must be short, about 3 to 4 words.
10. If the source contains a useful event description, use it. Otherwise create a short description yourself.
11. If the description is related to holiday, semester break, or no class, include one of those labels in the description.
12. The start field must be an object with only this format:
    {{"date": "YYYY-MM-DD"}}
13. The end field must be an object with only this format:
    {{"date": "YYYY-MM-DD"}}
14. For a one-day event, end.date must be one day after start.date so it is saved as an all-day Google Calendar event.
15. If one event lasts for consecutive days, combine it into one JSON object and set end.date to the day after the final day.
16. The output must be a valid JSON array only, with no extra text.
"""


def integrated_file_reader(file_path, file_type, file_name, color):
    """파일을 읽어 Gemini AI를 통해 일정 JSON 텍스트 생성"""
    try:
        if file_type in [".jpg", ".jpeg", ".png"]:
            processed_file = Image.open(file_path)
            prompt = build_direct_file_prompt(file_type, file_name, color)
            response = model.generate_content([processed_file, prompt])
            return response.text

        if file_type == ".pdf":
            return read_pdf_with_fallbacks(file_path, file_name, color)

        raise ValueError(f"지원하지 않는 파일 형식입니다: {file_type}")

    except FileNotFoundError:
        return f"오류: '{file_path}' 경로에서 파일을 찾을 수 없습니다."


def build_schedule_prompt(intro, file_name, color, source_name, content=None):
    prompt = (
        f"{intro}\n\n"
        + COMMON_PROMPT_RULES.format(file_name=file_name, color_id=color).strip()
        + "\n\n"
    )

    if content is None:
        prompt += (
            "17. Use only the uploaded file content.\n"
            "18. Ignore non-schedule content in the uploaded file.\n"
            "19. Do not infer events that are not supported by the uploaded file."
        )
        return prompt

    prompt += (
        f"17. Use only the provided {source_name}.\n"
        f"18. Ignore {source_name} content that is not related to schedules.\n"
        f"19. Do not infer events that are not supported by the provided {source_name}.\n\n"
        f"Provided {source_name}:\n"
        f"{content}"
    )
    return prompt.strip()


def build_direct_file_prompt(file_type, file_name, color):
    return build_schedule_prompt(
        intro=f"Summarize all the academic schedules from this {file_type} file and organize them into a JSON format in English.",
        file_name=file_name,
        color=color,
        source_name="uploaded file content",
    )


def read_pdf_with_fallbacks(file_path, file_name, color):
    table_text = extract_week_tables_as_markdown(file_path)
    if table_text:
        print("[PDF] 'week' 테이블 추출 성공. Gemini에 표 텍스트를 전달합니다.")
        prompt = build_schedule_prompt(
            intro="You are given schedule tables extracted from a syllabus PDF.",
            file_name=file_name,
            color=color,
            source_name="table data",
            content=table_text,
        )
        response = model.generate_content(prompt)
        return response.text

    print("[PDF] 'week' 테이블을 찾지 못했습니다. OCR을 시도합니다.")
    ocr_text = extract_text_with_ocr(file_path)
    if ocr_text:
        prompt = build_schedule_prompt(
            intro="You are given OCR text extracted from a syllabus PDF.",
            file_name=file_name,
            color=color,
            source_name="OCR text",
            content=ocr_text,
        )
        response = model.generate_content(prompt)
        return response.text

    print("[PDF] OCR도 실패했습니다. Gemini PDF 업로드 방식으로 되돌아갑니다.")
    uploaded_pdf = genai.upload_file(path=file_path, display_name="syllabus PDF")
    prompt = build_direct_file_prompt(".pdf", file_name, color)
    response = model.generate_content([uploaded_pdf, prompt])
    return response.text


def extract_week_tables_as_markdown(file_path):
    markdown_tables = []

    try:
        document = pymupdf.open(file_path)
    except Exception as exc:
        print(f"[PDF] 문서를 여는 중 오류가 발생했습니다: {exc}")
        return ""

    try:
        for page_index, page in enumerate(document, start=1):
            try:
                found_tables = page.find_tables()
            except Exception as exc:
                print(f"[PDF] 페이지 {page_index} 테이블 탐지 실패: {exc}")
                continue

            for table_index, table in enumerate(found_tables.tables, start=1):
                try:
                    markdown = (table.to_markdown(fill_empty=True) or "").strip()
                except Exception as exc:
                    print(f"[PDF] 페이지 {page_index} 테이블 {table_index} 변환 실패: {exc}")
                    continue

                if not markdown or "week" not in markdown.lower():
                    continue

                markdown_tables.append(
                    f"[Page {page_index}][Table {table_index}]\n{markdown}"
                )
    finally:
        document.close()

    return "\n\n".join(markdown_tables)


def extract_text_with_ocr(file_path):
    ocr_pages = []

    try:
        document = pymupdf.open(file_path)
    except Exception as exc:
        print(f"[OCR] 문서를 여는 중 오류가 발생했습니다: {exc}")
        return ""

    try:
        for page_index, page in enumerate(document, start=1):
            try:
                text_page = page.get_textpage_ocr(language="eng", dpi=300, full=True)
                page_text = page.get_text("text", textpage=text_page, sort=True).strip()
            except Exception as exc:
                print(f"[OCR] 페이지 {page_index} OCR 실패: {exc}")
                return ""

            if page_text:
                ocr_pages.append(f"[Page {page_index}]\n{page_text}")
    finally:
        document.close()

    return "\n\n".join(ocr_pages)


def parse_response_to_events(response_text):
    """AI의 텍스트 응답에서 JSON 배열을 추출하여 파싱"""
    if not response_text:
        raise ValueError("AI 응답이 비어있습니다.")

    start = response_text.find("[")
    end = response_text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []

    candidate = response_text[start : end + 1]
    data = json.loads(candidate)

    return data if isinstance(data, list) else [data]


def google_calendar(events_list, credentials):
    if not credentials:
        print("❌ 인증 정보가 없습니다. 일정을 등록할 수 없습니다.")
        return

    try:
        service = build("calendar", "v3", credentials=credentials)

        for event_data in events_list:
            try:
                if is_common_event(event_data):
                    dedupe_key = make_common_event_id(event_data)
                    event_data.setdefault("extendedProperties", {}).setdefault(
                        "private", {}
                    )["dedupeKey"] = dedupe_key

                    time_min = f"{event_data['start']['date']}T00:00:00Z"
                    time_max = f"{event_data['end']['date']}T00:00:00Z"

                    found = (
                        service.events()
                        .list(
                            calendarId="primary",
                            privateExtendedProperty=f"dedupeKey={dedupe_key}",
                            showDeleted=False,
                            singleEvents=True,
                            timeMin=time_min,
                            timeMax=time_max,
                            maxResults=1,
                        )
                        .execute()
                    )

                    if found.get("items"):
                        print(f"중복 일정(이미 존재) 건너뜀: {event_data.get('summary')}")
                        continue

                service.events().insert(calendarId="primary", body=event_data).execute()
                print(f"✅ 일정 등록 완료: {event_data.get('summary')}")

            except HttpError as e:
                if e.resp.status == 409:
                    print(f"중복 일정 건너뜀: {event_data.get('summary')}")
                else:
                    error_body = (
                        e.content.decode("utf-8", errors="replace")
                        if isinstance(e.content, (bytes, bytearray))
                        else str(e.content)
                    )
                    print(f"등록 오류: {event_data.get('summary')} - {e}")
                    print(f"[GCAL][ERROR] status={e.resp.status}")
                    print(
                        f"[GCAL][ERROR] payload={json.dumps(event_data, ensure_ascii=False)}"
                    )
                    print(f"[GCAL][ERROR] response={error_body}")

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
