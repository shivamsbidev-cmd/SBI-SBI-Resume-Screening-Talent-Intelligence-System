# parser.py (improved starter version)
# Replace your existing parser with this baseline and extend skill lists as needed.

import re
from pathlib import Path
from typing import Dict, List
from datetime import datetime

import pdfplumber
from pypdf import PdfReader

from utils import clean_text, format_phone, hash_file_bytes, is_pdf_file

EMAIL_PATTERN = re.compile(r'[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}')
PHONE_PATTERN = re.compile(r'(\+?\d[\d\s().-]{7,}\d)')

SKILLS = {
    'python','sql','java','javascript','aws','azure','gcp',
    'pandas','numpy','pytorch','tensorflow','tableau','power bi',
    'machine learning','deep learning','nlp','langchain','genai',
    'docker','kubernetes','git','linux','spark','hadoop',
    'databricks','snowflake','fastapi'
}

SECTION_HEADERS = {
    'experience':['experience','professional experience','employment'],
    'education':['education','academics','qualification'],
    'skills':['skills','technical skills','core competencies'],
    'projects':['projects','project experience'],
    'certifications':['certifications','certificates']
}

def extract_text_from_pdf(file_path: str) -> str:
    text = []
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            text.append(page.extract_text() or '')
    except Exception:
        pass

    if ''.join(text).strip():
        return clean_text('\n'.join(text))

    try:
        with pdfplumber.open(file_path) as pdf:
            return clean_text('\n'.join(
                page.extract_text() or '' for page in pdf.pages
            ))
    except Exception:
        return ''

def extract_name(text: str) -> str:
    lines = [x.strip() for x in text.splitlines() if x.strip()]

    for line in lines[:15]:
        if '@' in line:
            continue
        if re.search(r'\d{5,}', line):
            continue

        words = line.split()
        if 2 <= len(words) <= 5:
            if sum(w[:1].isupper() for w in words) >= max(2, len(words) - 1):
                return line

    return 'Unknown'

def extract_email(text: str) -> str:
    m = EMAIL_PATTERN.search(text)
    return m.group(0).lower() if m else ''

def extract_phone(text: str) -> str:
    m = PHONE_PATTERN.findall(text)
    return format_phone(m[0]) if m else ''

def extract_sections(text: str) -> dict:
    sections = {'header': []}
    current = 'header'

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        lower = line.lower()

        matched = False
        for sec, headers in SECTION_HEADERS.items():
            if lower in headers:
                current = sec
                sections.setdefault(sec, [])
                matched = True
                break

        if not matched:
            sections.setdefault(current, []).append(line)

    return {k: '\n'.join(v) for k, v in sections.items()}

def extract_skills(text: str) -> List[str]:
    lower = text.lower()
    return sorted(
        skill.title()
        for skill in SKILLS
        if re.search(rf'\b{re.escape(skill)}\b', lower)
    )

def extract_experience_years(text: str) -> float:
    current_year = datetime.now().year

    ranges = []
    pattern = re.compile(
        r'(\d{4})\s*(?:-|–|to)\s*(\d{4}|present|current)',
        re.I
    )

    for start, end in pattern.findall(text):
        start = int(start)
        end = current_year if end.lower() in ('present', 'current') else int(end)
        ranges.append((start, end))

    if not ranges:
        return 0.0

    ranges.sort()
    merged = []

    for s, e in ranges:
        if not merged or s > merged[-1][1]:
            merged.append([s, e])
        else:
            merged[-1][1] = max(merged[-1][1], e)

    return float(sum(e - s for s, e in merged))

def compute_file_hash(file_path: str) -> str:
    with open(file_path, 'rb') as f:
        return hash_file_bytes(f.read())

def parse_resume_file(file_path: str) -> Dict:
    text = extract_text_from_pdf(file_path)

    return {
        'resume_hash': compute_file_hash(file_path),
        'file_name': Path(file_path).name,
        'candidate_name': extract_name(text),
        'email': extract_email(text),
        'phone': extract_phone(text),
        'skills': extract_skills(text),
        'experience_years': extract_experience_years(text),
        'resume_text': text,
    }

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(len(words), start + chunk_size)
        chunks.append(' '.join(words[start:end]))
        start += chunk_size - overlap
    return chunks

def validate_resume_file(file_path: str) -> bool:
    return is_pdf_file(file_path)
