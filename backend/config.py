import os
from pathlib import Path

from dotenv import load_dotenv

# This folder (tabkit/).
REPO_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(REPO_ROOT / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# True = on, False = off.
DEBUG = True
# True = on, False = off. No SerpAPI key → set False.
WEB_SEARCH = True

CHAT_OPENAI_MODEL = os.getenv("CHAT_OPENAI_MODEL", "gpt-5.6-terra")
SUFFICIENCY_OPENAI_MODEL = os.getenv("SUFFICIENCY_OPENAI_MODEL", "gpt-5-mini")
MEMORY_OPENAI_MODEL = os.getenv("MEMORY_OPENAI_MODEL", "gpt-5.6-luna")
SUMMARIZE_OPENAI_MODEL = os.getenv("SUMMARIZE_OPENAI_MODEL", "gpt-5-mini")
PAGES_OPENAI_MODEL = os.getenv("PAGES_OPENAI_MODEL", "gpt-5.6-luna")

# Search only when sufficiency score is below this (1–10)
SUFFICIENCY_THRESHOLD = int(os.getenv("SUFFICIENCY_THRESHOLD", "7"))

# Runtime data lives under backend/data/ (gitignored)
BACKEND_DIR = Path(__file__).resolve().parent
DATA_DIR = BACKEND_DIR / "data"
PAGES_DIR = DATA_DIR / "pages"
MEMORY_DIR = DATA_DIR / "memory"
MEMORY_PATH = MEMORY_DIR / "memory.json"
DEBUG_DIR = DATA_DIR / "debug"
DEBUG_PATH = DEBUG_DIR / "debug.json"
LAST_URL_PATH = DATA_DIR / "last_url.txt"

def require_openai_api_key() -> str:
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is not set. Put it in a .env file in the tabkit folder."
        )
    return OPENAI_API_KEY

# variables for web search
MAX_SEARCH_SNIPPETS = 350
MAX_SEARCH_RESULTS = 10

# x amount of context the main llm can take from web search
MAX_ASSISTANT_SNIPPETS = 800

# variables for summarize llm
MAX_MEMORY_TURNS = 50
MAX_CHAT_MEMORY_TURNS = 8

# x amount of context the main chat llm can produce
CHAT_MAX_TOKENS = 4096

# x amount of pages and context the page llm can produce
MAX_PAGE_SECTIONS = 80
PAGE_CHUNKS_CHARS = 15000
PAGES_MAX_TOKENS = 2048


def use_debug():
    return bool(globals().get("DEBUG", False))


def use_web_search():
    return bool(globals().get("WEB_SEARCH", False))
