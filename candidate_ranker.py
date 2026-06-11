from typing import Dict, List, Tuple


def compute_similarity(text_a: str, text_b: str) -> float:
    """Compute text similarity using word overlap."""
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = len(words_a & words_b)
    union = len(words_a | words_b)
    return intersection / union if union > 0 else 0.0


def score_skill_match(candidate_skills: List[str], job_description: str) -> float:
    description = job_description.lower()
    if not candidate_skills or not description:
        return 0.0
    matches = sum(1 for skill in candidate_skills if skill.lower() in description)
    return matches / len(candidate_skills)


def score_experience_match(experience_years: float, job_description: str) -> float:
    if experience_years <= 0:
        return 0.0
    years_required = 0.0
    found = [int(token) for token in job_description.split() if token.isdigit() and 1 <= int(token) <= 30]
    if found:
        years_required = max(found)
    if years_required == 0:
        return min(1.0, experience_years / 5.0)
    return min(1.0, experience_years / years_required)


def score_education_match(education_text: str, job_description: str) -> float:
    if not education_text:
        return 0.0
    jd_lower = job_description.lower()
    education_text_lower = education_text.lower()
    for token in ["phd", "master", "mba", "bachelor", "degree", "diploma"]:
        if token in jd_lower and token in education_text_lower:
            return 1.0
    if any(token in education_text_lower for token in ["bachelor", "master", "mba"]):
        return 0.7
    return 0.3


def compute_final_score(
    resume_text: str,
    candidate_skills: List[str],
    education_text: str,
    experience_years: float,
    job_description: str,
) -> Dict[str, float]:
    semantic_similarity = compute_similarity(resume_text, job_description)
    skill_match = score_skill_match(candidate_skills, job_description)
    experience_match = score_experience_match(experience_years, job_description)
    education_match = score_education_match(education_text, job_description)
    score = (
        0.45 * semantic_similarity
        + 0.3 * skill_match
        + 0.15 * experience_match
        + 0.1 * education_match
    )
    return {
        "semantic_similarity": semantic_similarity,
        "skill_match": skill_match,
        "experience_match": experience_match,
        "education_match": education_match,
        "score": score,
    }


def label_candidate(score: float) -> str:
    if score >= 0.80:
        return "Strong Hire"
    if score >= 0.65:
        return "Hire"
    if score >= 0.45:
        return "Consider"
    return "Reject"


def generate_interview_questions(candidate_name: str, candidate_skills: List[str], job_description: str) -> List[str]:
    questions = [
        f"Tell me about an impactful project where you used {skill} in a production environment." for skill in candidate_skills[:3]
    ]
    questions.append(
        "Describe how your background aligns with the key business priorities in this job description."
    )
    questions.append(
        "What is the most challenging data problem you solved and what was the business outcome?"
    )
    return questions


def rank_candidates(resumes: List[Dict], job_description: str) -> List[Dict]:
    ranked: List[Dict] = []
    for resume in resumes:
        score_data = compute_final_score(
            resume_text=resume.get("resume_text", ""),
            candidate_skills=resume.get("skills", []),
            education_text=resume.get("education", ""),
            experience_years=resume.get("experience_years", 0.0),
            job_description=job_description,
        )
        label = label_candidate(score_data["score"])
        ranked.append(
            {
                **resume,
                **score_data,
                "label": label,
            }
        )
    return sorted(ranked, key=lambda item: item["score"], reverse=True)
