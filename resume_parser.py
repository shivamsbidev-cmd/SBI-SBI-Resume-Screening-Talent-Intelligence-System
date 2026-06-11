import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pdfplumber
from pypdf import PdfReader

from utils import clean_text, format_phone, hash_file_bytes, is_pdf_file

SKILL_CANDIDATES = [
    "python", "r", "sql", "excel", "power bi", "tableau", "aws", "azure", "gcp",
    "machine learning", "data analysis", "data visualization", "nlp", "deep learning",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "hadoop", "spark",
    "java", "c#", "excel vba", "selenium", "jira", "devops", "kubernetes",
    "git", "linux", "business analysis", "project management", "risk management",
]

EDUCATION_SECTION_TOKENS = [
    "bachelor", "master", "phd", "mba", "degree", "diploma", "high school", "engineering",
]

CERTIFICATION_TOKENS = [
    "certified", "certificate", "aws", "azure", "gcp", "cfa", "pmp", "scrum", "ibm",
    "cloudera", "google cloud", "data science", "business analyst",
]

PROJECT_SECTION_TOKENS = ["project", "initiative", "engaged", "delivered", "designed", "built"]

PHONE_PATTERN = re.compile(
    r"(\+?\d[\d\s().-]{7,}\d)"
)
EMAIL_PATTERN = re.compile(r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,6}")
NAME_PATTERN = re.compile(r"^([A-Z][a-z]+(?: [A-Z][a-z]+){0,3})$")
DATE_RANGE_PATTERN = re.compile(r"(\b\d{4}\b)")


def extract_text_from_pdf(file_path: str) -> str:
    text_parts: List[str] = []
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            try:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
            except Exception:
                continue
    except Exception:
        pass
    if not any(text_parts):
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    text_parts.append(page_text)
        except Exception:
            pass
    return clean_text("\n".join(text_parts))


def parse_resume_file(file_path: str) -> Dict[str, any]:
    text = extract_text_from_pdf(file_path)
    if not text:
        raise ValueError(f"Unable to extract text from {file_path}")
    candidate_name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    skills = extract_skills(text)
    education = extract_education(text)
    certifications = extract_certifications(text)
    projects = extract_projects(text)
    experience_years = extract_experience_years(text)
    current_role, current_company = extract_current_role_and_company(text)
    file_hash = compute_file_hash(file_path)
    return {
        "resume_hash": file_hash,
        "file_name": Path(file_path).name,
        "candidate_name": candidate_name,
        "email": email,
        "phone": phone,
        "skills": skills,
        "education": education,
        "certifications": certifications,
        "projects": projects,
        "experience_years": experience_years,
        "current_role": current_role,
        "current_company": current_company,
        "resume_text": text,
    }


def compute_file_hash(file_path: str) -> str:
    with open(file_path, "rb") as stream:
        return hash_file_bytes(stream.read())


def extract_name(text: str) -> str:
    first_lines = [line.strip() for line in text.splitlines() if line.strip()][:8]
    for line in first_lines:
        if NAME_PATTERN.match(line) and len(line.split()) <= 4:
            return line
    return first_lines[0] if first_lines else "Unknown"


def extract_email(text: str) -> str:
    match = EMAIL_PATTERN.search(text)
    return match.group(0).strip() if match else ""


def extract_phone(text: str) -> str:
    matches = PHONE_PATTERN.findall(text)
    if matches:
        return format_phone(matches[0])
    return ""


def extract_skills(text: str) -> List[str]:
    normalized = text.lower()
    skills = set()
    for token in SKILL_CANDIDATES:
        if token in normalized:
            skills.add(token.title())
    if not skills:
        skill_matches = re.findall(r"\b([A-Za-z#+\. ]{2,20})\b", normalized)
        for candidate in skill_matches:
            if candidate.strip() and len(candidate.strip()) <= 20:
                if any(token in candidate for token in ["sql", "data", "python", "excel"]):
                    skills.add(candidate.strip().title())
    return sorted(skills)


def extract_education(text: str) -> str:
    normalized = text.lower()
    values = []
    for token in EDUCATION_SECTION_TOKENS:
        if token in normalized:
            values.append(token.title())
    if values:
        return ", ".join(sorted(set(values)))
    return "Not specified"


def extract_certifications(text: str) -> List[str]:
    normalized = text.lower()
    certifications = set()
    for token in CERTIFICATION_TOKENS:
        if token in normalized:
            certifications.add(token.title())
    return sorted(certifications)


def extract_projects(text: str) -> List[Dict[str, str]]:
    sections = re.split(r"\n{2,}", text)
    projects: List[Dict[str, str]] = []
    for section in sections:
        lower_section = section.lower()
        if any(token in lower_section for token in PROJECT_SECTION_TOKENS) and len(section) < 500:
            title = section.split("\n")[0][:80]
            description = " ".join(line.strip() for line in section.splitlines()[1:])
            projects.append({"name": title, "description": description})
    return projects[:5]


def extract_current_role_and_company(text: str) -> Tuple[str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:15]:
        lower = line.lower()
        if any(keyword in lower for keyword in ["manager", "engineer", "analyst", "consultant", "lead", "director", "officer"]):
            pieces = line.split(" at ")
            if len(pieces) == 2:
                return pieces[0].strip(), pieces[1].strip()
            return line.strip(), ""
    return "Not specified", "Not specified"


def extract_experience_years(text: str) -> float:
    years = re.findall(r"(\d{4})", text)
    if not years:
        return 0.0
    unique_years = sorted({int(year) for year in years})
    if len(unique_years) >= 2:
        return float(unique_years[-1] - unique_years[0])
    return 1.0


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(len(words), start + chunk_size)
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def validate_resume_file(file_path: str) -> bool:
    return os.path.exists(file_path) and is_pdf_file(file_path)
