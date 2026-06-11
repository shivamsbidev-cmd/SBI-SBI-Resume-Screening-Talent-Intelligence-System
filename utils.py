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
    "openai/gpt-3.5-turbo",
    "openai/gpt-4-turbo",
    "anthropic/claude-3-haiku",
    "anthropic/claude-3-sonnet",
    "mistralai/mistral-7b-instruct",
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
    if not api_key or not api_key.strip():
        raise ValueError("OpenRouter API key is required. Please provide a valid API key in the sidebar.")
    
    api_key = api_key.strip()
    model_name = model_name.strip() if model_name else "gpt-3.5-turbo"
    
    url = "https://openrouter.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "SBI-Talent-Intelligence-System/1.0",
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a helpful HR assistant. Provide concise, accurate responses."},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "top_p": 0.95,
        "max_tokens": min(max_tokens, 2000),
    }
    
    logger.info(f"Calling OpenRouter API with model: {model_name}")
    
    try:
        response: Response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if response.status_code == 404:
            logger.error(f"404 Error: Model '{model_name}' not found on OpenRouter. Check if model name is correct and API key is valid.")
            raise ValueError(f"Model '{model_name}' not found on OpenRouter. Possible causes: Invalid API key, incorrect model name, or service unavailable.")
        
        if response.status_code == 401:
            logger.error("401 Error: Unauthorized. API key is invalid or expired.")
            raise ValueError("OpenRouter API authentication failed. Check your API key in the sidebar.")
        
        response.raise_for_status()
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"].get("content", "")
            if content:
                return content
        
        if "output" in result and isinstance(result["output"], list):
            return "\n".join(str(item) for item in result["output"])
        
        logger.warning(f"Unexpected response format: {result}")
        return "Unable to process response from OpenRouter API."
        
    except requests.ConnectionError as exc:
        logger.error(f"Connection error: {exc}")
        raise RuntimeError(f"Failed to connect to OpenRouter API. Check your internet connection and try again.") from exc
    except requests.Timeout as exc:
        logger.error(f"Request timeout: {exc}")
        raise RuntimeError(f"OpenRouter API request timed out. Please try again.") from exc
    except requests.RequestException as exc:
        logger.error(f"OpenRouter request failed: {exc}")
        raise RuntimeError(f"OpenRouter API request failed: {exc}") from exc
    except ValueError as exc:
        raise exc
    except Exception as exc:
        logger.error(f"Unexpected error: {exc}")
        raise RuntimeError(f"Unexpected error calling OpenRouter API: {exc}") from exc


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
