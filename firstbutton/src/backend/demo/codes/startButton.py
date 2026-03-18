import hashlib
import json
import os
import re
from datetime import date, timedelta

import google.generativeai as genai
import pymupdf
from PIL import Image
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import load_env


load_env()

SCOPES = ["https://www.googleapis.com/auth/calendar"]
GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite")
GENERATION_CONFIG = {"temperature": 0}

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
17. Preserve the exact calendar day written in the source. Never move an event to the previous or next day.
18. If the source contains both a weekday and a numeric date, trust the numeric date written in the source.
19. If the source says Feb 2, 2/2, or 2026-02-02, start.date must be exactly that day.
20. For a one-day event, only change end.date by adding one day. Do not change start.date when creating an all-day event.
21. In tables, copy the date from the same row or cell as the event. Do not borrow a date from a nearby row.
"""

WEEKDAY_MARKERS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)

DATE_PATTERNS = (
    re.compile(r"\b\d{4}[-/.]\d{1,2}[-/.]\d{1,2}\b"),
    re.compile(r"\b\d{1,2}[-/.]\d{1,2}(?:[-/.]\d{2,4})?\b"),
    re.compile(
        r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
        r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|"
        r"oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}"
        r"(?:,\s*\d{4})?\b",
        re.IGNORECASE,
    ),
)

COMMON_EVENT_MARKERS = (
    ("reading day", "reading day"),
    ("spring break", "break"),
    ("fall break", "break"),
    ("winter break", "break"),
    ("summer break", "break"),
    ("semester break", "break"),
    ("holiday", "holiday"),
    ("no classes", "no class"),
    ("no class", "no class"),
    ("recess", "break"),
    ("break", "break"),
)


def integrated_file_reader(file_path, file_type, file_name, color):
    try:
        if file_type in [".jpg", ".jpeg", ".png"]:
            processed_file = Image.open(file_path)
            prompt = build_direct_file_prompt(file_type, file_name, color)
            response = generate_schedule_content([processed_file, prompt])
            return response.text

        if file_type == ".pdf":
            return read_pdf_with_fallbacks(file_path, file_name, color)

        raise ValueError(f"Unsupported file type: {file_type}")

    except FileNotFoundError:
        return f"Error: file not found at '{file_path}'."


def build_schedule_prompt(intro, file_name, color, source_name, content=None):
    prompt = (
        f"{intro}\n\n"
        + COMMON_PROMPT_RULES.format(file_name=file_name, color_id=color).strip()
        + "\n\n"
    )

    if content is None:
        prompt += (
            "22. Use only the uploaded file content.\n"
            "23. Ignore non-schedule content in the uploaded file.\n"
            "24. Do not infer events that are not supported by the uploaded file."
        )
        return prompt

    prompt += (
        f"22. Use only the provided {source_name}.\n"
        f"23. Ignore {source_name} content that is not related to schedules.\n"
        f"24. Do not infer events that are not supported by the provided {source_name}.\n\n"
        f"Provided {source_name}:\n"
        f"{content}"
    )
    return prompt.strip()


def generate_schedule_content(contents):
    return model.generate_content(contents, generation_config=GENERATION_CONFIG)


def build_direct_file_prompt(file_type, file_name, color):
    return build_schedule_prompt(
        intro=f"Summarize all the academic schedules from this {file_type} file and organize them into a JSON format in English.",
        file_name=file_name,
        color=color,
        source_name="uploaded file content",
    )


def read_pdf_with_fallbacks(file_path, file_name, color):
    table_text = extract_schedule_tables_as_markdown(file_path)
    if table_text:
        print("[PDF] Schedule-like table extraction succeeded. Sending table text to Gemini.")
        prompt = build_schedule_prompt(
            intro="You are given schedule tables extracted from a syllabus PDF.",
            file_name=file_name,
            color=color,
            source_name="table data",
            content=table_text,
        )
        response = generate_schedule_content(prompt)
        return response.text

    print("[PDF] No schedule-like table found. Falling back to OCR.")
    ocr_text = extract_text_with_ocr(file_path)
    if ocr_text:
        prompt = build_schedule_prompt(
            intro="You are given OCR text extracted from a syllabus PDF.",
            file_name=file_name,
            color=color,
            source_name="OCR text",
            content=ocr_text,
        )
        response = generate_schedule_content(prompt)
        return response.text

    print("[PDF] OCR failed. Falling back to direct Gemini PDF upload.")
    uploaded_pdf = genai.upload_file(path=file_path, display_name="syllabus PDF")
    prompt = build_direct_file_prompt(".pdf", file_name, color)
    response = generate_schedule_content([uploaded_pdf, prompt])
    return response.text


def table_looks_like_schedule(markdown):
    if not markdown:
        return False

    lowered = markdown.lower()

    if "week" in lowered or any(day in lowered for day in WEEKDAY_MARKERS):
        return True

    return any(pattern.search(markdown) for pattern in DATE_PATTERNS)


def extract_schedule_tables_as_markdown(file_path):
    markdown_tables = []

    try:
        document = pymupdf.open(file_path)
    except Exception as exc:
        print(f"[PDF] Failed to open document: {exc}")
        return ""

    try:
        for page_index, page in enumerate(document, start=1):
            try:
                found_tables = page.find_tables()
            except Exception as exc:
                print(f"[PDF] Table detection failed on page {page_index}: {exc}")
                continue

            for table_index, table in enumerate(found_tables.tables, start=1):
                try:
                    markdown = (table.to_markdown(fill_empty=True) or "").strip()
                except Exception as exc:
                    print(
                        f"[PDF] Table conversion failed on page {page_index}, table {table_index}: {exc}"
                    )
                    continue

                if not table_looks_like_schedule(markdown):
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
        print(f"[OCR] Failed to open document: {exc}")
        return ""

    try:
        for page_index, page in enumerate(document, start=1):
            try:
                text_page = page.get_textpage_ocr(language="eng", dpi=300, full=True)
                page_text = page.get_text("text", textpage=text_page, sort=True).strip()
            except Exception as exc:
                print(f"[OCR] OCR failed on page {page_index}: {exc}")
                return ""

            if page_text:
                ocr_pages.append(f"[Page {page_index}]\n{page_text}")
    finally:
        document.close()

    return "\n\n".join(ocr_pages)


def parse_iso_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def normalize_event_dates(events):
    normalized_events = []

    for event_data in events:
        start_value = event_data.get("start", {}).get("date")
        end_value = event_data.get("end", {}).get("date")
        start_date = parse_iso_date(start_value)
        end_date = parse_iso_date(end_value)

        if start_date and end_date and end_date <= start_date:
            event_data.setdefault("end", {})["date"] = (
                start_date + timedelta(days=1)
            ).isoformat()

        normalized_events.append(event_data)

    return normalized_events


def parse_response_to_events(response_text):
    if not response_text:
        raise ValueError("AI response was empty.")

    start = response_text.find("[")
    end = response_text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []

    candidate = response_text[start : end + 1]
    data = json.loads(candidate)
    events = data if isinstance(data, list) else [data]
    return normalize_event_dates(events)


def normalize_event_text(value):
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def get_common_event_category(event_data):
    searchable_text = " ".join(
        filter(
            None,
            [event_data.get("summary", ""), event_data.get("description", "")],
        )
    )
    normalized = normalize_event_text(searchable_text)

    for marker, category in COMMON_EVENT_MARKERS:
        if marker in normalized:
            return category

    return ""


def get_event_date_range(event_data):
    start = event_data.get("start", {}).get("date", "")
    end = event_data.get("end", {}).get("date", "")
    return start, end


def find_existing_common_event(service, event_data, dedupe_key):
    start_date, end_date = get_event_date_range(event_data)
    if not start_date or not end_date:
        return False

    time_min = f"{start_date}T00:00:00Z"
    time_max = f"{end_date}T00:00:00Z"

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
        return True

    target_category = get_common_event_category(event_data)
    target_range = get_event_date_range(event_data)

    fallback = (
        service.events()
        .list(
            calendarId="primary",
            showDeleted=False,
            singleEvents=True,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=20,
        )
        .execute()
    )

    for item in fallback.get("items", []):
        if get_common_event_category(item) != target_category:
            continue
        if get_event_date_range(item) != target_range:
            continue
        return True

    return False


def google_calendar(events_list, credentials):
    if not credentials:
        print("Credentials are missing. Skipping calendar registration.")
        return

    try:
        service = build("calendar", "v3", credentials=credentials)
        seen_common_event_keys = set()

        for event_data in events_list:
            try:
                dedupe_key = None

                if is_common_event(event_data):
                    dedupe_key = make_common_event_id(event_data)
                    if dedupe_key in seen_common_event_keys:
                        print(
                            f"Skipping duplicate common event from current batch: {event_data.get('summary')}"
                        )
                        continue

                    event_data.setdefault("extendedProperties", {}).setdefault(
                        "private", {}
                    )["dedupeKey"] = dedupe_key

                    if find_existing_common_event(service, event_data, dedupe_key):
                        print(
                            f"Skipping duplicate common event already in calendar: {event_data.get('summary')}"
                        )
                        seen_common_event_keys.add(dedupe_key)
                        continue

                service.events().insert(calendarId="primary", body=event_data).execute()
                if dedupe_key:
                    seen_common_event_keys.add(dedupe_key)
                print(f"Event created: {event_data.get('summary')}")

            except HttpError as error:
                if error.resp.status == 409:
                    print(f"Skipping duplicate event: {event_data.get('summary')}")
                else:
                    error_body = (
                        error.content.decode("utf-8", errors="replace")
                        if isinstance(error.content, (bytes, bytearray))
                        else str(error.content)
                    )
                    print(f"Calendar insert failed: {event_data.get('summary')} - {error}")
                    print(f"[GCAL][ERROR] status={error.resp.status}")
                    print(
                        f"[GCAL][ERROR] payload={json.dumps(event_data, ensure_ascii=False)}"
                    )
                    print(f"[GCAL][ERROR] response={error_body}")

    except HttpError as error:
        print(f"Google Calendar service error: {error}")


def is_common_event(event_data):
    return bool(get_common_event_category(event_data))


def make_common_event_id(event_data):
    start = event_data["start"]["date"].replace("-", "")
    end = event_data["end"]["date"].replace("-", "")
    category = get_common_event_category(event_data)
    summary_title = normalize_event_text(event_data.get("summary", "")).replace(" ", "")
    raw_id = f"{category or summary_title}{start}{end}"
    return hashlib.md5(raw_id.encode()).hexdigest()
