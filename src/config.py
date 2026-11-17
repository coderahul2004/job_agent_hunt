"""Central configuration for the JobHunt Agent Squad."""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
MODEL = os.getenv("MODEL", "groq/openai/gpt-oss-120b").strip()
TOP_N = int(os.getenv("TOP_N", "3"))
JOB_SEARCH_LIMIT = int(os.getenv("JOB_SEARCH_LIMIT", "4"))
MAX_RESUME_CHARS = int(os.getenv("MAX_RESUME_CHARS", "4500"))
MAX_DESCRIPTION_CHARS = int(os.getenv("MAX_DESCRIPTION_CHARS", "350"))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "1800"))

if not MODEL.startswith("groq/"):
    MODEL = f"groq/{MODEL}"

OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TAILORED_APPLICATIONS_PATH = OUTPUT_DIR / "tailored_applications.md"
APPLICATIONS_LOG_PATH = OUTPUT_DIR / "applications_log.csv"


def validate_config() -> None:
    """Fail early with a useful message if the Groq key is missing."""
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        raise ValueError(
            "GROQ_API_KEY is missing. Add it to the .env file (local) "
            "or to the app Secrets (Streamlit Cloud)."
        )
    if TOP_N < 1:
        raise ValueError("TOP_N must be at least 1.")
    if JOB_SEARCH_LIMIT < TOP_N:
        raise ValueError("JOB_SEARCH_LIMIT should be greater than or equal to TOP_N.")