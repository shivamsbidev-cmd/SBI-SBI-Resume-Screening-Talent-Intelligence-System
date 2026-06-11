import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pdfplumber
from pypdf import PdfReader

from utils import clean_text, format_phone, hash_file_bytes, is_pdf_file, call_openrouter

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


def parse_resume_with_ai(text: str, api_key: str, model_name: str) -> Dict[str, Any]:
    """Extract candidate details using OpenRouter LLM parsing."""
    prompt = (
        "You are an expert recruitment assistant. Analyze the candidate resume text below and extract structured metadata.\n"
        "Format the output STRICTLY as a valid JSON object with the following keys. "
        "Do NOT wrap the output in markdown code blocks or backticks (e.g. no ```json). "
        "Output ONLY the raw JSON string.\n\n"
        "JSON Keys:\n"
        "- \"candidate_name\": string (e.g., \"John Doe\")\n"
        "- \"email\": string (e.g., \"john@example.com\")\n"
        "- \"phone\": string (e.g., \"123-456-7890\")\n"
        "- \"skills\": list of strings\n"
        "- \"experience_years\": float (e.g., 4.5)\n"
        "- \"education\": string (highest degree and institution)\n"
        "- \"certifications\": list of strings\n"
        "- \"projects\": list of objects, each with keys \"name\" (string) and \"description\" (string)\n"
        "- \"current_role\": string\n"
        "- \"current_company\": string\n\n"
        f"Resume Text:\n{text}"
    )
    
    response = call_openrouter(
        api_key=api_key,
        model_name=model_name,
        prompt=prompt,
        max_tokens=1000,
        temperature=0.1
    )
    
    # Clean the response string from code block markdown wrapping if present
    cleaned = response.strip()
    if cleaned.startswith("```"):
        # Split and locate JSON content
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
        
    return json.loads(cleaned)


def parse_resume_file(file_path: str, api_key: Optional[str] = None, model_name: Optional[str] = None) -> Dict[str, Any]:
    text = extract_text_from_pdf(file_path)
    if not text:
        raise ValueError(f"Unable to extract text from {file_path}")
        
    file_hash = compute_file_hash(file_path)
    
    metadata = {
        "resume_hash": file_hash,
        "file_name": Path(file_path).name,
        "resume_text": text,
    }
    
    ai_parsed = False
    if api_key:
        try:
            ai_data = parse_resume_with_ai(text, api_key, model_name or "openai/gpt-3.5-turbo")
            metadata["candidate_name"] = str(ai_data.get("candidate_name") or "Unknown")
            metadata["email"] = str(ai_data.get("email") or "")
            metadata["phone"] = str(ai_data.get("phone") or "")
            metadata["skills"] = list(ai_data.get("skills") or [])
            
            try:
                metadata["experience_years"] = float(ai_data.get("experience_years") or 0.0)
            except (ValueError, TypeError):
                metadata["experience_years"] = 0.0
                
            metadata["education"] = str(ai_data.get("education") or "Not specified")
            metadata["certifications"] = list(ai_data.get("certifications") or [])
            metadata["projects"] = list(ai_data.get("projects") or [])
            metadata["current_role"] = str(ai_data.get("current_role") or "Not specified")
            metadata["current_company"] = str(ai_data.get("current_company") or "Not specified")
            ai_parsed = True
        except Exception as e:
            # Fall back to heuristics if AI parsing fails
            pass
            
    if not ai_parsed:
        candidate_name = extract_name(text)
        email = extract_email(text)
        phone = extract_phone(text)
        skills = extract_skills(text)
        education = extract_education(text)
        certifications = extract_certifications(text)
        projects = extract_projects(text)
        experience_years = extract_experience_years(text)
        current_role, current_company = extract_current_role_and_company(text)
        
        metadata.update({
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
        })
        
    return metadata


def compute_file_hash(file_path: str) -> str:
    with open(file_path, "rb") as stream:
        return hash_file_bytes(stream.read())


def extract_name(text: str) -> str:
    """Extract candidate name from top of resume or from labeled format."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    # Check for labeled format (Name: XXX)
    for line in lines[:5]:
        if line.lower().startswith("name:"):
            return line.split(":", 1)[1].strip()
    
    # Check first non-empty line for name pattern (typically the header)
    if lines:
        first_line = lines[0]
        # Skip common headers like "PROFESSIONAL SUMMARY", "RESUME", etc.
        if not any(skip in first_line.upper() for skip in ["RESUME", "CURRICULUM", "CV", "SUMMARY", "OBJECTIVE"]):
            # Accept 1-5 words that start with capital letters
            if all(word[0].isupper() for word in first_line.split() if word):
                return first_line
    
    return lines[0] if lines else "Unknown"


def extract_email(text: str) -> str:
    """Extract email from labeled format or regex pattern."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    # Check for labeled format (Email: xxx@yyy.zzz)
    for line in lines[:10]:
        if line.lower().startswith("email:"):
            email = line.split(":", 1)[1].strip()
            if EMAIL_PATTERN.match(email):
                return email.lower()
    
    # Fallback to regex search
    match = EMAIL_PATTERN.search(text)
    return match.group(0).strip().lower() if match else ""


def extract_phone(text: str) -> str:
    """Extract phone number from labeled format or regex pattern."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    # Check for labeled format (Phone: xxx-xxx-xxxx)
    for line in lines[:10]:
        if line.lower().startswith("phone:"):
            phone = line.split(":", 1)[1].strip()
            if phone and any(c.isdigit() for c in phone):
                return format_phone(phone)
    
    # Fallback to regex pattern
    matches = PHONE_PATTERN.findall(text)
    if matches:
        return format_phone(matches[0])
    return ""


def extract_skills(text: str) -> List[str]:
    """Extract skills from SKILLS section or by scanning for skill tokens."""
    normalized = text.lower()
    skills = set()
    
    # Look for SKILLS section first
    sections = re.split(r"\n+(?=SKILLS|Technical|TECHNICAL|COMPETENCIES|CORE COMPETENCIES)", text, flags=re.IGNORECASE)
    skills_section = ""
    if len(sections) > 1:
        skills_section = sections[1].split("\n")[0:10]  # Take first 10 lines of skills section
        skills_section = " ".join(skills_section).lower()
    
    # Check for skill tokens
    for token in SKILL_CANDIDATES:
        if token in normalized or (skills_section and token in skills_section):
            skills.add(token.title())
    
    # Extract words after common skill indicators
    skill_indicators = ["skills:", "technical skills:", "core competencies:", "expertise:", "technical expertise:"]
    for indicator in skill_indicators:
        if indicator in normalized:
            idx = normalized.find(indicator)
            following_text = text[idx:idx+500].lower()
            # Extract comma/space-separated technical terms
            terms = re.findall(r'(?:, |;|^)([\w#\+\. ]+?)(?:,|;|\n|$)', following_text)
            for term in terms:
                term = term.strip()
                if term and 2 < len(term) < 30:
                    skills.add(term.title())
    
    return sorted(skills) if skills else []


def extract_education(text: str) -> str:
    """Extract education details from EDUCATION section."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    # Find EDUCATION section
    education_start = None
    for i, line in enumerate(lines):
        if line.upper() in ["EDUCATION", "EDUCATIONAL BACKGROUND", "ACADEMICS"]:
            education_start = i + 1
            break
    
    if education_start:
        # Collect education lines until next major section
        education_lines = []
        for line in lines[education_start:education_start+10]:
            if any(section in line.upper() for section in ["EXPERIENCE", "SKILLS", "PROJECT", "CERTIF"]):
                break
            if line and not line.startswith("|"):
                education_lines.append(line)
        
        if education_lines:
            # Look for degree patterns
            degree_text = " ".join(education_lines[:3])
            degrees = []
            for token in EDUCATION_SECTION_TOKENS:
                if token.lower() in degree_text.lower():
                    degrees.append(degree_text)
                    break
            if degrees:
                return degrees[0][:100]
    
    # Fallback: Find education tokens
    normalized = text.lower()
    values = []
    for token in EDUCATION_SECTION_TOKENS:
        if token in normalized:
            values.append(token.title())
    
    if values:
        return ", ".join(sorted(set(values)))
    return "Not specified"


def extract_certifications(text: str) -> List[str]:
    """Extract certifications from CERTIFICATIONS section or by scanning."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    certifications = set()
    
    # Look for CERTIFICATIONS section
    cert_start = None
    for i, line in enumerate(lines):
        if "CERTIF" in line.upper():
            cert_start = i + 1
            break
    
    if cert_start:
        for line in lines[cert_start:cert_start+15]:
            if any(section in line.upper() for section in ["EXPERIENCE", "EDUCATION", "SKILLS", "PROJECT"]):
                break
            lower = line.lower()
            # Check for certification tokens
            for token in CERTIFICATION_TOKENS:
                if token in lower:
                    certifications.add(line)  # Add the full line as certification
                    break
    
    # Fallback: scan entire text for tokens
    if not certifications:
        normalized = text.lower()
        for token in CERTIFICATION_TOKENS:
            if token in normalized:
                certifications.add(token.title())
    
    return sorted(certifications)


def extract_projects(text: str) -> List[Dict[str, str]]:
    """Extract projects from PROJECTS section."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    projects: List[Dict[str, str]] = []
    
    # Look for PROJECTS section
    project_start = None
    for i, line in enumerate(lines):
        if "PROJECT" in line.upper():
            project_start = i + 1
            break
    
    if project_start:
        current_project = None
        for line in lines[project_start:]:
            # Stop if we hit another major section
            if any(section in line.upper() for section in ["EXPERIENCE", "EDUCATION", "SKILLS", "CERTIF"]):
                break
            
            # Lines starting with "- " or containing keywords are project entries
            if line.startswith("- ") or any(keyword in line.lower() for keyword in PROJECT_SECTION_TOKENS):
                if current_project:
                    projects.append(current_project)
                current_project = {
                    "name": line.replace("- ", "").strip()[:80],
                    "description": ""
                }
            elif current_project and line and not line.startswith("•"):
                current_project["description"] += " " + line
        
        if current_project:
            projects.append(current_project)
    
    return projects[:5]


def extract_current_role_and_company(text: str) -> Tuple[str, str]:
    """Extract current role and company from CURRENT ROLE section or EXPERIENCE section."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    # Look for "CURRENT ROLE" section
    for i, line in enumerate(lines):
        if "CURRENT ROLE" in line.upper():
            if i + 1 < len(lines):
                role_line = lines[i + 1]
                # Check if it's formatted as "Role at Company"
                if " at " in role_line:
                    parts = role_line.split(" at ")
                    return parts[0].strip(), parts[1].strip()
                # Otherwise take the whole line as role
                return role_line, ""
    
    # Look for most recent position in EXPERIENCE section
    for i, line in enumerate(lines):
        if "EXPERIENCE" in line.upper() or "PROFESSIONAL EXPERIENCE" in line.upper():
            # Look at next few lines for a position
            for j in range(i + 1, min(i + 5, len(lines))):
                exp_line = lines[j]
                if " | " in exp_line:
                    parts = exp_line.split(" | ")
                    if len(parts) >= 2:
                        return parts[0].strip(), parts[1].strip()
                elif " at " in exp_line:
                    parts = exp_line.split(" at ")
                    return parts[0].strip(), parts[1].strip()
    
    # Fallback: search for role keywords in first 30 lines
    for line in lines[:30]:
        lower = line.lower()
        if any(keyword in lower for keyword in ["manager", "engineer", "analyst", "consultant", "lead", "director", "officer", "developer"]):
            if " at " in line:
                parts = line.split(" at ")
                return parts[0].strip(), parts[1].strip()
            return line.strip(), ""
    
    return "Not specified", "Not specified"


def extract_experience_years(text: str) -> float:
    """Extract total years of experience from dates in resume."""
    # Normalize unicode/replacement dashes to standard hyphens
    normalized_text = re.sub(r"[\u2010-\u2015\u2013\u2014\uff0d\uff0e\ufffd]+", "-", text)
    lines = [line.strip() for line in normalized_text.splitlines() if line.strip()]
    
    # Look for year ranges in EXPERIENCE section
    all_years = []
    in_experience = False
    
    for line in lines:
        if "EXPERIENCE" in line.upper():
            in_experience = True
        elif in_experience and any(sec in line.upper() for sec in ["EDUCATION", "SKILLS", "PROJECT", "CERTIF"]):
            in_experience = False
        
        if in_experience:
            # Find year patterns like "2020 - 2024" or "2020-Present"
            year_ranges = re.findall(r"(\d{4})\s*(?:-|to)\s*(?:(\d{4})|present|current)", line, re.IGNORECASE)
            for match in year_ranges:
                start_year = int(match[0])
                end_year = int(match[1]) if match[1] else 2026  # Current year
                all_years.append((start_year, end_year))
    
    # If we found year ranges, sort and merge overlapping intervals
    if all_years:
        all_years.sort()
        merged = []
        for start, end in all_years:
            if not merged or start > merged[-1][1]:
                merged.append([start, end])
            else:
                merged[-1][1] = max(merged[-1][1], end)
        total_years = sum(end - start for start, end in merged)
        return float(total_years) if total_years > 0 else 1.0
    
    # Fallback: look for any 4-digit years in text (restrict to reasonable ranges)
    years = [int(y) for y in re.findall(r"\b(\d{4})\b", normalized_text) if 1970 <= int(y) <= 2035]
    if not years:
        return 0.0
    
    unique_years = sorted(set(years))
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
    return is_pdf_file(file_path)
