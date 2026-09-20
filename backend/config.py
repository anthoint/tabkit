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

# python run.py          → api
# python run.py local    → local
# python run.py api      → api
MODE = "api"

# Cloud names (what you use now).
API_BASE_URL = None
API_CHAT_MODEL = os.getenv("CHAT_OPENAI_MODEL", "gpt-5.6-terra")
API_SUFFICIENCY_MODEL = os.getenv("SUFFICIENCY_OPENAI_MODEL", "gpt-5-mini")
API_MEMORY_MODEL = os.getenv("MEMORY_OPENAI_MODEL", "gpt-5.6-luna")
API_SUMMARIZE_MODEL = os.getenv("SUMMARIZE_OPENAI_MODEL", "gpt-5-mini")
API_PAGES_MODEL = os.getenv("PAGES_OPENAI_MODEL", "gpt-5.6-luna")

# Local names for ~12 GB VRAM. Ollama's qwen2.5:14b is this same Instruct build.
# Chat is the bigger one; the rest stay small so filing 40 headings does not crawl.
# If chat OOMs on a fat notes dump, set LOCAL_CHAT_MODEL to qwen2.5:7b-instruct too.
LOCAL_BASE_URL = os.getenv("LOCAL_BASE_URL", "http://127.0.0.1:11434/v1")
LOCAL_CHAT_MODEL = os.getenv("LOCAL_CHAT_MODEL", "qwen2.5:14b")
LOCAL_SUFFICIENCY_MODEL = os.getenv("LOCAL_SUFFICIENCY_MODEL", "qwen2.5:7b")
LOCAL_MEMORY_MODEL = os.getenv("LOCAL_MEMORY_MODEL", "qwen2.5:7b")
LOCAL_SUMMARIZE_MODEL = os.getenv("LOCAL_SUMMARIZE_MODEL", "qwen2.5:7b")
LOCAL_PAGES_MODEL = os.getenv("LOCAL_PAGES_MODEL", "qwen2.5:7b")

# Live names. Default api. set_mode() overwrites these if you pass local.
BASE_URL = API_BASE_URL
CHAT_MODEL = API_CHAT_MODEL
SUFFICIENCY_MODEL = API_SUFFICIENCY_MODEL
MEMORY_MODEL = API_MEMORY_MODEL
SUMMARIZE_MODEL = API_SUMMARIZE_MODEL
PAGES_MODEL = API_PAGES_MODEL


def set_mode(name):
    global MODE
    global BASE_URL
    global CHAT_MODEL
    global SUFFICIENCY_MODEL
    global MEMORY_MODEL
    global SUMMARIZE_MODEL
    global PAGES_MODEL

    key = (name or "api").strip().lower()
    if key not in ("api", "local"):
        raise ValueError("Mode must be api or local.")

    MODE = key

    if MODE == "local":
        BASE_URL = LOCAL_BASE_URL
        CHAT_MODEL = LOCAL_CHAT_MODEL
        SUFFICIENCY_MODEL = LOCAL_SUFFICIENCY_MODEL
        MEMORY_MODEL = LOCAL_MEMORY_MODEL
        SUMMARIZE_MODEL = LOCAL_SUMMARIZE_MODEL
        PAGES_MODEL = LOCAL_PAGES_MODEL
        return

    BASE_URL = API_BASE_URL
    CHAT_MODEL = API_CHAT_MODEL
    SUFFICIENCY_MODEL = API_SUFFICIENCY_MODEL
    MEMORY_MODEL = API_MEMORY_MODEL
    SUMMARIZE_MODEL = API_SUMMARIZE_MODEL
    PAGES_MODEL = API_PAGES_MODEL


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
    if MODE == "local":
        return OPENAI_API_KEY or "local"
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is not set. Put it in a .env file in the tabkit folder."
        )
    return OPENAI_API_KEY


def make_client():
    from openai import OpenAI
    if BASE_URL:
        return OpenAI(api_key=require_openai_api_key(), base_url=BASE_URL)
    return OpenAI(api_key=require_openai_api_key())

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
