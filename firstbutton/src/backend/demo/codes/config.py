from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
DEMO_DIR = BASE_DIR.parent
SECRET_DIR = DEMO_DIR / "secret"
ENV_CANDIDATES = [
    SECRET_DIR / ".env",
    DEMO_DIR / ".env",
    BASE_DIR / ".env",
]
ENV_FILE_PATH = next(
    (candidate for candidate in ENV_CANDIDATES if candidate.exists()),
    ENV_CANDIDATES[0],
)

_ENV_LOADED = False


def load_env():
    global _ENV_LOADED

    if not _ENV_LOADED:
        load_dotenv(ENV_FILE_PATH, override=False)
        _ENV_LOADED = True

    return ENV_FILE_PATH


load_env()
