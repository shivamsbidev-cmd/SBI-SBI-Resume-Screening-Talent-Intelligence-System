import hashlib
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests import Response

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("sbi_talent_intelligence")

DATA_DIR = Path(__file__).resolve().parent / "data"
FAISS_DIR = Path(__file__).resolve().parent / "faiss_index"

SUPPORTED_PDF_EXTENSIONS = {".pdf"}

MODEL_OPTIONS = [
    "openrouter/auto",
    "deepseek/deepseek-chat-v3-0324:free",
    "qwen/qwen3-32b:free",
    "anthropic/claude-sonnet-4",
    "openai/gpt-4.1-mini",
]


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FAISS_DIR.mkdir(parents=True, exist_ok=True)
    logger.debug("Ensured storage directories exist: %s, %s", DATA_DIR, FAISS_DIR)


def hash_file_bytes(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def safe_filename(filename: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)


def format_phone(phone_text: str) -> str:
    digits = re.sub(r"\D", "", phone_text)
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
    return phone_text.strip()


def clean_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned


def call_openrouter(api_key: str, model_name: str, prompt: str, max_tokens: int = 800, temperature: float = 0.2) -> str:
    if not api_key:
        raise ValueError("OpenRouter API key is required.")
    url = "https://openrouter.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "top_p": 0.95,
        "max_tokens": max_tokens,
    }
    try:
        response: Response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"].get("content", "")
        if "output" in result and isinstance(result["output"], list):
            return "\n".join(str(item) for item in result["output"])
        return json.dumps(result)
    except requests.RequestException as exc:
        logger.error("OpenRouter request failed: %s", exc)
        raise RuntimeError(f"OpenRouter API request failed: {exc}") from exc


def is_pdf_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in SUPPORTED_PDF_EXTENSIONS


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def json_serialize(data: Any) -> str:
    return json.dumps(data, default=str, ensure_ascii=False)


def json_deserialize(value: Optional[str]) -> Any:
    if not value:
        return []
    return json.loads(value)
