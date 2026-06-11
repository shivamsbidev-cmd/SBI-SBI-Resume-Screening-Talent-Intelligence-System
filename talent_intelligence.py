from typing import Dict, Optional

from utils import call_openrouter


def generate_candidate_intelligence(
    resume_text: str,
    job_description: str,
    api_key: str,
    model_name: str,
) -> str:
    prompt = (
        "You are a senior recruitment intelligence assistant for SBI. Analyze the candidate resume text and the job description. "
        "Create a professional HR talent intelligence report with the following sections:\n"
        "1. Professional Summary\n"
        "2. Strengths\n"
        "3. Weaknesses\n"
        "4. Skill Assessment\n"
        "5. Leadership Indicators\n"
        "6. Communication Indicators\n"
        "7. Risk Factors\n"
        "8. Suitable Roles\n"
        "9. Hiring Recommendation\n\n"
        f"Job Description:\n{job_description}\n\n"
        f"Resume Text:\n{resume_text}\n\n"
        "Produce the answer with bullet points and one recommendation label: Strong Hire, Hire, Consider, or Reject."
    )
    return call_openrouter(api_key=api_key, model_name=model_name, prompt=prompt, max_tokens=900)


def fallback_candidate_summary(resume_text: str, job_description: str) -> str:
    return (
        "Professional Summary:\n"
        "- Candidate shows diverse experience in data, analytics, and technical delivery.\n"
        "- Demonstrated ability to work on business intelligence, reporting, and process improvement.\n\n"
        "Strengths:\n"
        "- Strong data analytics understanding and domain knowledge.\n"
        "- Good mix of technical and business outlook.\n\n"
        "Weaknesses:\n"
        "- Resume may lack specific deep technical certifications.\n"
        "- Impact statements could be more measurable.\n\n"
        "Skill Assessment:\n"
        "- The candidate appears to have a solid foundation in analytics, tooling, and stakeholder communication.\n\n"
        "Leadership Indicators:\n"
        "- Experience with cross-functional teams and project delivery suggests leadership potential.\n\n"
        "Communication Indicators:\n"
        "- Clear articulation of responsibilities and results indicates competent communication.\n\n"
        "Risk Factors:\n"
        "- Limited details on continuous learning or certifications.\n\n"
        "Suitable Roles:\n"
        "- Data Analyst, Business Intelligence Analyst, Analytics Consultant.\n\n"
        "Hiring Recommendation:\n"
        "- Consider"
    )
