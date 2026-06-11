import json
from typing import Dict, List, Optional

import pandas as pd
import plotly.express as px


def load_resume_dataframe(resumes: List[Dict]) -> pd.DataFrame:
    rows = []
    for resume in resumes:
        skills = resume.get("skills")
        if isinstance(skills, str):
            skills = json.loads(skills) if skills else []
        certifications = resume.get("certifications")
        if isinstance(certifications, str):
            certifications = json.loads(certifications) if certifications else []
        rows.append(
            {
                "id": resume.get("id"),
                "name": resume.get("candidate_name"),
                "email": resume.get("email"),
                "phone": resume.get("phone"),
                "current_role": resume.get("current_role"),
                "current_company": resume.get("current_company"),
                "experience_years": resume.get("experience_years") or 0.0,
                "education": resume.get("education"),
                "skills": skills,
                "certifications": certifications,
                "projects": resume.get("projects"),
            }
        )
    return pd.DataFrame(rows)


def total_resumes(resumes: List[Dict]) -> int:
    return len(resumes)


def average_experience(resumes: List[Dict]) -> float:
    if not resumes:
        return 0.0
    return sum([resume.get("experience_years", 0.0) for resume in resumes]) / len(resumes)


def get_top_skills(resumes: List[Dict], top_n: int = 10) -> Dict[str, int]:
    counts = {}
    for resume in resumes:
        skills = resume.get("skills") or []
        if isinstance(skills, str):
            skills = json.loads(skills) if skills else []
        for skill in skills:
            counts[skill] = counts.get(skill, 0) + 1
    sorted_counts = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:top_n])
    return sorted_counts


def get_top_certifications(resumes: List[Dict], top_n: int = 10) -> Dict[str, int]:
    counts = {}
    for resume in resumes:
        certifications = resume.get("certifications") or []
        if isinstance(certifications, str):
            certifications = json.loads(certifications) if certifications else []
        for cert in certifications:
            counts[cert] = counts.get(cert, 0) + 1
    sorted_counts = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:top_n])
    return sorted_counts


top_skills = get_top_skills


def build_education_distribution(resumes: List[Dict]) -> Dict[str, int]:
    counts = {}
    for resume in resumes:
        education = resume.get("education") or "Unknown"
        counts[education] = counts.get(education, 0) + 1
    return counts


def skill_frequency_chart(skill_counts: Dict[str, int]):
    if not skill_counts:
        return None
    df = pd.DataFrame(list(skill_counts.items()), columns=["Skill", "Count"])
    return px.bar(df, x="Skill", y="Count", title="Top Skills Frequency", color="Count", template="plotly_white")


def experience_histogram(resumes: List[Dict]):
    df = pd.DataFrame([resume.get("experience_years", 0.0) for resume in resumes], columns=["ExperienceYears"])
    return px.histogram(df, x="ExperienceYears", nbins=8, title="Experience Distribution", template="plotly_white")


def education_pie_chart(distribution: Dict[str, int]):
    if not distribution:
        return None
    df = pd.DataFrame(list(distribution.items()), columns=["Education", "Count"])
    return px.pie(df, names="Education", values="Count", title="Education Distribution", template="plotly_white")


def certification_trend_chart(cert_counts: Dict[str, int]):
    if not cert_counts:
        return None
    df = pd.DataFrame(list(cert_counts.items()), columns=["Certification", "Count"])
    return px.bar(df, x="Certification", y="Count", title="Certification Trends", template="plotly_white")


def build_candidate_leaderboard(rankings: List[Dict]):
    if not rankings:
        return None
    df = pd.DataFrame(rankings)
    if "score" not in df.columns:
        return None
    df = df.head(10).copy()
    return px.bar(df, x="candidate_name", y="score", color="label", title="Candidate Ranking Leaderboard", template="plotly_white")
