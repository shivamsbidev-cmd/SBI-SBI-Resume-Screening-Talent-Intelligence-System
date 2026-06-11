import io
import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import streamlit as st
from fpdf import FPDF

from analytics import (
    build_candidate_leaderboard,
    build_education_distribution,
    certification_trend_chart,
    education_pie_chart,
    experience_histogram,
    get_top_skills,
    load_resume_dataframe,
    skill_frequency_chart,
)
from candidate_ranker import generate_interview_questions, rank_candidates
from database import (
    get_resume_by_id,
    init_db,
    insert_resume,
    list_candidate_scores,
    list_chat_history,
    list_resumes,
    resume_exists,
    save_candidate_score,
    save_chat_message,
    search_resumes,
)
from rag_engine import RAGEngine
try:
    from resume_parser_2 import parse_resume_file, validate_resume_file
except Exception as exc:
    raise ImportError(
        "Could not import parser functions from resume_parser_2.py. "
        "Ensure resume_parser_2.py defines parse_resume_file and validate_resume_file, "
        f"and that all required dependencies are installed. Original error: {exc}"
    ) from exc
from talent_intelligence import fallback_candidate_summary, generate_candidate_intelligence
from utils import DATA_DIR, FAISS_DIR, MODEL_OPTIONS, ensure_directories, now_iso

UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

rag_engine = RAGEngine()


def parse_json_field(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return []
    return value or []


def collect_resume_dicts(rows: List) -> List[Dict[str, Any]]:
    resumes: List[Dict[str, Any]] = []
    for row in rows:
        resume = dict(row)
        resume["skills"] = parse_json_field(resume.get("skills"))
        resume["certifications"] = parse_json_field(resume.get("certifications"))
        resume["projects"] = parse_json_field(resume.get("projects"))
        resumes.append(resume)
    return resumes


def save_uploaded_file(uploaded_file: Any) -> Path:
    target = UPLOAD_DIR / uploaded_file.name
    with open(target, "wb") as output:
        output.write(uploaded_file.getbuffer())
    return target


def process_uploaded_resumes(uploaded_files: List[Any]) -> List[str]:
    messages: List[str] = []
    for uploaded_file in uploaded_files:
        if not validate_resume_file(uploaded_file.name):
            messages.append(f"Skipped invalid file format: {uploaded_file.name}")
            continue
        saved_path = save_uploaded_file(uploaded_file)
        try:
            metadata = parse_resume_file(str(saved_path))
            if resume_exists(metadata["resume_hash"]):
                messages.append(f"Duplicate resume skipped: {metadata['file_name']}")
                continue
            resume_id = insert_resume(metadata)
            rag_engine.index_resume(resume_id, metadata["resume_text"], metadata["file_name"])
            messages.append(f"Indexed resume: {metadata['candidate_name']} ({metadata['file_name']})")
        except Exception as exc:
            messages.append(f"Failed to process {uploaded_file.name}: {exc}")
    return messages


def export_resume_excel(resumes: List[Dict[str, Any]]) -> bytes:
    df = pd.DataFrame(resumes)
    df = df.drop(columns=["resume_text"], errors="ignore")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Resumes")
    return buffer.getvalue()


def export_resume_pdf(resumes: List[Dict[str, Any]]) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 12, "SBI Talent Intelligence - Resume Report", ln=True)
    pdf.set_font("Arial", size=11)
    for idx, resume in enumerate(resumes[:10], start=1):
        pdf.ln(4)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, f"{idx}. {resume.get('candidate_name', 'Unknown')}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 6, f"Email: {resume.get('email', '')}")
        pdf.multi_cell(0, 6, f"Phone: {resume.get('phone', '')}")
        pdf.multi_cell(0, 6, f"Current Role: {resume.get('current_role', '')}")
        pdf.multi_cell(0, 6, f"Skills: {', '.join(resume.get('skills', []))}")
        pdf.multi_cell(0, 6, f"Education: {resume.get('education', '')}")
        pdf.multi_cell(0, 6, f"Certifications: {', '.join(resume.get('certifications', []))}")
        pdf.multi_cell(0, 6, "-")
    return pdf.output(dest="S").encode("latin-1")


def show_dashboard(resumes: List[Dict[str, Any]], rankings: Optional[List[Dict[str, Any]]] = None) -> None:
    total = len(resumes)
    avg_experience = sum([r.get("experience_years", 0.0) for r in resumes]) / total if total else 0.0
    top_skill_counts = get_top_skills(resumes)
    education_dist = build_education_distribution(resumes)
    from analytics import get_top_certifications

    cert_counts = get_top_certifications(resumes)

    st.metric("Total Resumes", total)
    st.metric("Average Experience (years)", f"{avg_experience:.1f}")
    with st.expander("Top Skills"):
        st.write(top_skill_counts)
    col1, col2 = st.columns(2)
    with col1:
        chart = skill_frequency_chart(top_skill_counts)
        if chart is not None:
            st.plotly_chart(chart, use_container_width=True)
    with col2:
        chart = experience_histogram(resumes)
        if chart is not None:
            st.plotly_chart(chart, use_container_width=True)
    col3, col4 = st.columns(2)
    with col3:
        chart = education_pie_chart(education_dist)
        if chart is not None:
            st.plotly_chart(chart, use_container_width=True)
    with col4:
        chart = certification_trend_chart(cert_counts)
        if chart is not None:
            st.plotly_chart(chart, use_container_width=True)
    if rankings:
        leaderboard = build_candidate_leaderboard(rankings)
        if leaderboard is not None:
            st.plotly_chart(leaderboard, use_container_width=True)


def show_candidate_explorer(resumes: List[Dict[str, Any]]) -> None:
    df = pd.DataFrame(resumes)
    skill_options = sorted({skill for resume in resumes for skill in resume.get("skills", [])})
    selected_skill = st.multiselect("Filter by Skill", options=skill_options)
    selected_name = st.text_input("Search by Candidate Name")
    selected_education = st.text_input("Education Keyword")
    selected_certification = st.text_input("Certification Keyword")
    filtered = resumes
    if selected_skill:
        filtered = [r for r in filtered if all(skill in r.get("skills", []) for skill in selected_skill)]
    if selected_name:
        filtered = [r for r in filtered if selected_name.lower() in (r.get("candidate_name") or "").lower()]
    if selected_education:
        filtered = [r for r in filtered if selected_education.lower() in (r.get("education") or "").lower()]
    if selected_certification:
        filtered = [r for r in filtered if any(selected_certification.lower() in cert.lower() for cert in r.get("certifications", []))]
    st.write(f"Showing {len(filtered)} candidates")
    for resume in filtered:
        with st.expander(f"{resume.get('candidate_name')} - {resume.get('current_role')}"):
            st.markdown(f"**Company:** {resume.get('current_company')}  ")
            st.markdown(f"**Experience:** {resume.get('experience_years')} years  ")
            st.markdown(f"**Education:** {resume.get('education')}  ")
            st.markdown(f"**Skills:** {', '.join(resume.get('skills', []))}")
            st.markdown(f"**Certifications:** {', '.join(resume.get('certifications', []))}")
            st.markdown(f"**Projects:**")
            for project in resume.get("projects", []) or []:
                st.markdown(f"- {project.get('name')}: {project.get('description')}")


def show_talent_intelligence(resumes: List[Dict[str, Any]], api_key: str, model_name: str) -> None:
    candidate_options = [r.get("candidate_name") for r in resumes]
    selected_candidate = st.selectbox("Select Candidate", options=candidate_options)
    job_description = st.text_area("Job Description", height=220)
    if st.button("Generate Talent Intelligence Report"):
        chosen = next((r for r in resumes if r.get("candidate_name") == selected_candidate), None)
        if not chosen:
            st.warning("Select a candidate to analyze.")
            return
        
        try:
            if api_key and job_description:
                with st.spinner("Generating insights from OpenRouter..."):
                    summary = generate_candidate_intelligence(
                        chosen.get("resume_text", ""), job_description, api_key, model_name
                    )
            else:
                st.info("No API key provided. Using template-based analysis.")
                summary = fallback_candidate_summary(chosen.get("resume_text", ""), job_description)
            st.markdown(summary)
        except ValueError as ve:
            st.error(f"Configuration Error: {str(ve)}")
        except RuntimeError as re:
            st.error(f"API Error: {str(re)}")
            st.info("Using template-based analysis instead...")
            summary = fallback_candidate_summary(chosen.get("resume_text", ""), job_description)
            st.markdown(summary)
        except Exception as e:
            st.error(f"Unexpected Error: {str(e)}")


def show_resume_search(resumes: List[Dict[str, Any]]) -> None:
    query = st.text_input("Search Query for Semantic Candidate Search")
    if st.button("Run Semantic Search") and query:
        results = rag_engine.retrieve_documents(query, top_k=5)
        st.write(f"Found {len(results)} contextual resume segments")
        for item in results:
            st.markdown(f"**Resume ID:** {item['resume_id']}  ")
            st.markdown(f"**Score:** {item['score']:.3f}  ")
            st.markdown(f"{item['content']}")


def show_rag_chat(api_key: str, model_name: str) -> None:
    session_id = st.session_state.get("session_id") or str(uuid.uuid4())
    st.session_state["session_id"] = session_id
    prompt = st.text_area("Ask the talent intelligence assistant a question")
    if st.button("Submit Chat Query") and prompt:
        if not api_key:
            st.warning("OpenRouter API key is required for RAG chat. Enter your API key in the sidebar.")
            return
        try:
            response = rag_engine.answer_query(api_key, model_name, prompt, top_k=5)
            save_chat_message(None, prompt, response, session_id)
            st.markdown("**Assistant response:**")
            st.write(response)
        except ValueError as ve:
            st.error(f"Configuration Error: {str(ve)}")
        except RuntimeError as re:
            st.error(f"API Error: {str(re)}")
        except Exception as e:
            st.error(f"Unexpected Error: {str(e)}")
    history = list_chat_history(limit=20)
    if history:
        st.subheader("Recent Chat History")
        for row in history:
            st.markdown(f"**Q:** {row['user_message']}  \n**A:** {row['assistant_message']}")


def show_candidate_ranking(resumes: List[Dict[str, Any]], api_key: str, model_name: str) -> None:
    job_description = st.text_area("Paste the Job Description to score candidates", height=240)
    if st.button("Rank Candidates") and job_description:
        if not resumes:
            st.warning("No candidates available for ranking.")
            return
        with st.spinner("Scoring candidates..."):
            ranking_results = rank_candidates(resumes, job_description)
            for item in ranking_results[:10]:
                save_candidate_score({
                    "resume_id": item.get("id"),
                    "job_description": job_description,
                    "score": item.get("score"),
                    "semantic_similarity": item.get("semantic_similarity"),
                    "skill_match": item.get("skill_match"),
                    "experience_match": item.get("experience_match"),
                    "education_match": item.get("education_match"),
                    "label": item.get("label"),
                    "details": json.dumps({
                        "skills": item.get("skills"),
                        "education": item.get("education"),
                    }),
                })
            st.success("Ranking completed.")
            st.dataframe(pd.DataFrame(ranking_results).head(20))
            leaderboard = build_candidate_leaderboard(ranking_results)
            if leaderboard is not None:
                st.plotly_chart(leaderboard, use_container_width=True)
    else:
        st.info("Enter a job description and click Rank Candidates.")


def show_database_explorer() -> None:
    tab1, tab2 = st.tabs(["Browse Tables", "Delete Resume"])
    
    with tab1:
        table = st.selectbox("Select a table to explore", ["resumes", "candidate_scores", "chat_history"])
        if table == "resumes":
            rows = collect_resume_dicts(list_resumes(limit=200))
            st.dataframe(pd.DataFrame(rows))
        elif table == "candidate_scores":
            rows = list_candidate_scores(limit=200)
            st.dataframe(pd.DataFrame([dict(row) for row in rows]))
        elif table == "chat_history":
            rows = list_chat_history(limit=200)
            st.dataframe(pd.DataFrame([dict(row) for row in rows]))
    
    with tab2:
        st.header("🗑️ Delete Resume")
        st.warning("⚠️ This action is permanent and will delete the resume from the database and vector store.")
        
        # Get list of resumes
        resume_rows = list_resumes(limit=500)
        resume_dicts = collect_resume_dicts(resume_rows)
        
        if not resume_dicts:
            st.info("No resumes in database.")
            return
        
        # Create options for selection
        options = {
            f"{r.get('candidate_name')} ({r.get('file_name')}) - ID: {r.get('id')}": r.get('id')
            for r in resume_dicts
        }
        
        selected_resume = st.selectbox("Select Resume to Delete", list(options.keys()))
        
        if selected_resume:
            resume_id = options[selected_resume]
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ Delete Resume from Database", key="delete_db"):
                    from database import delete_resume
                    success, message = delete_resume(resume_id)
                    if success:
                        st.success(message)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(message)
            
            with col2:
                if st.button("🗑️ Remove from Vector Store", key="delete_vector"):
                    from database import delete_resume_from_vector_store
                    success, message = delete_resume_from_vector_store(resume_id)
                    if success:
                        st.success(message)
                    else:
                        st.warning(message)
            
            st.info("**Pro Tip:** Delete from database first, then remove from vector store.")
            st.divider()
            st.subheader("Delete All Data for a Candidate")
            if st.button("🗑️ Complete Deletion (DB + Vector Store)", key="delete_all"):
                from database import delete_resume, delete_resume_from_vector_store
                
                # Delete from DB
                db_success, db_msg = delete_resume(resume_id)
                st.info(f"Database: {db_msg}")
                
                # Delete from vector store
                vec_success, vec_msg = delete_resume_from_vector_store(resume_id)
                st.info(f"Vector Store: {vec_msg}")
                
                if db_success or vec_success:
                    st.success("✅ Candidate completely removed from the system!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Failed to delete candidate.")


def show_reports(resumes: List[Dict[str, Any]]) -> None:
    st.header("Export Talent Intelligence Reports")
    if resumes:
        excel_data = export_resume_excel(resumes)
        st.download_button("Download Excel Report", data=excel_data, file_name="sbi_candidate_report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        pdf_data = export_resume_pdf(resumes)
        st.download_button("Download PDF Report", data=pdf_data, file_name="sbi_candidate_report.pdf", mime="application/pdf")
        st.write("Export the top candidate resume summaries and talent intelligence tables.")
    else:
        st.warning("Add resumes before exporting reports.")


def main() -> None:
    st.set_page_config(page_title="SBI Resume Screening & Talent Intelligence System", layout="wide")
    init_db()
    ensure_directories()

    st.sidebar.title("SBI Talent Intelligence")
    
    # API Key input with instructions
    st.sidebar.markdown("### 🔐 OpenRouter Configuration")
    with st.sidebar.expander("How to get API Key?", expanded=False):
        st.markdown("""
        1. Go to [openrouter.ai](https://openrouter.ai)
        2. Sign up or log in
        3. Navigate to API keys
        4. Create a new API key
        5. Copy and paste it below
        """)
    
    api_key = st.sidebar.text_input("API Key", type="password", help="Your OpenRouter API key (keep it secret!)")
    
    st.sidebar.markdown("### 🤖 Model Selection")
    model_name = st.sidebar.selectbox(
        "Language Model", 
        MODEL_OPTIONS,
        index=0,
        help="Select the LLM for talent intelligence and RAG chat"
    )
    
    st.sidebar.markdown("### 📄 Resume Upload")
    uploaded_files = st.sidebar.file_uploader(
        "Upload candidate resumes (PDF)", type=["pdf"], accept_multiple_files=True
    )
    if st.sidebar.button("Process Resumes"):
        if uploaded_files:
            messages = process_uploaded_resumes(uploaded_files)
            for message in messages:
                st.sidebar.info(message)
        else:
            st.sidebar.warning("Select one or more PDF resumes to upload.")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Helpful examples")
    st.sidebar.markdown("- Find Python developers with 3+ years experience")
    st.sidebar.markdown("- Which candidates have AWS certifications")
    st.sidebar.markdown("- Who has Banking and AI experience")
    st.sidebar.markdown("---")
    page = st.sidebar.radio(
        "Main Navigation",
        [
            "Dashboard",
            "Candidate Explorer",
            "Talent Intelligence",
            "Resume Search",
            "RAG Chat Assistant",
            "Candidate Ranking",
            "Database Explorer",
            "Reports",
        ],
    )

    rows = list_resumes(limit=500)
    resumes = collect_resume_dicts(rows)

    st.title("SBI Resume Screening & Talent Intelligence System")
    st.markdown("A unified platform for resume ingestion, semantic search, ranking, and reporting.")

    if page == "Dashboard":
        show_dashboard(resumes)
    elif page == "Candidate Explorer":
        show_candidate_explorer(resumes)
    elif page == "Talent Intelligence":
        show_talent_intelligence(resumes, api_key, model_name)
    elif page == "Resume Search":
        show_resume_search(resumes)
    elif page == "RAG Chat Assistant":
        show_rag_chat(api_key, model_name)
    elif page == "Candidate Ranking":
        show_candidate_ranking(resumes, api_key, model_name)
    elif page == "Database Explorer":
        show_database_explorer()
    elif page == "Reports":
        show_reports(resumes)


if __name__ == "__main__":
    main()
