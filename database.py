import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from utils import DATA_DIR, ensure_directories, json_deserialize, json_serialize, now_iso

DB_PATH = DATA_DIR / "sbi_talent_intelligence.db"


def get_connection() -> sqlite3.Connection:
    ensure_directories()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY,
                resume_hash TEXT UNIQUE NOT NULL,
                file_name TEXT,
                candidate_name TEXT,
                email TEXT,
                phone TEXT,
                current_role TEXT,
                current_company TEXT,
                experience_years REAL,
                education TEXT,
                skills TEXT,
                certifications TEXT,
                projects TEXT,
                resume_text TEXT,
                parsed_at TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY,
                resume_id INTEGER,
                skill TEXT,
                FOREIGN KEY(resume_id) REFERENCES resumes(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS certifications (
                id INTEGER PRIMARY KEY,
                resume_id INTEGER,
                certification TEXT,
                FOREIGN KEY(resume_id) REFERENCES resumes(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
                resume_id INTEGER,
                project_name TEXT,
                description TEXT,
                FOREIGN KEY(resume_id) REFERENCES resumes(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS candidate_scores (
                id INTEGER PRIMARY KEY,
                resume_id INTEGER,
                job_description TEXT,
                score REAL,
                semantic_similarity REAL,
                skill_match REAL,
                experience_match REAL,
                education_match REAL,
                label TEXT,
                details TEXT,
                generated_at TEXT,
                FOREIGN KEY(resume_id) REFERENCES resumes(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY,
                resume_id INTEGER,
                user_message TEXT,
                assistant_message TEXT,
                session_id TEXT,
                created_at TEXT,
                FOREIGN KEY(resume_id) REFERENCES resumes(id) ON DELETE CASCADE
            )
            """
        )
    conn.close()


@contextmanager
def transaction() -> sqlite3.Cursor:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def insert_resume(record: Dict[str, Any]) -> int:
    conn = get_connection()
    with conn:
        existing = conn.execute(
            "SELECT id FROM resumes WHERE resume_hash = ?", (record["resume_hash"],)
        ).fetchone()
        if existing:
            return existing["id"]
        cursor = conn.execute(
            """
            INSERT INTO resumes (
                resume_hash, file_name, candidate_name, email, phone,
                current_role, current_company, experience_years, education,
                skills, certifications, projects, resume_text,
                parsed_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.get("resume_hash"),
                record.get("file_name"),
                record.get("candidate_name"),
                record.get("email"),
                record.get("phone"),
                record.get("current_role"),
                record.get("current_company"),
                record.get("experience_years"),
                record.get("education"),
                json_serialize(record.get("skills", [])),
                json_serialize(record.get("certifications", [])),
                json_serialize(record.get("projects", [])),
                record.get("resume_text"),
                now_iso(),
                now_iso(),
                now_iso(),
            ),
        )
        resume_id = cursor.lastrowid
        insert_collections(resume_id, record)
    conn.close()
    return resume_id


def insert_collections(resume_id: int, record: Dict[str, Any]) -> None:
    conn = get_connection()
    with conn:
        skills = record.get("skills", [])
        certifications = record.get("certifications", [])
        projects = record.get("projects", [])
        for skill in skills:
            conn.execute(
                "INSERT INTO skills (resume_id, skill) VALUES (?, ?)",
                (resume_id, skill),
            )
        for certification in certifications:
            conn.execute(
                "INSERT INTO certifications (resume_id, certification) VALUES (?, ?)",
                (resume_id, certification),
            )
        for project in projects:
            conn.execute(
                "INSERT INTO projects (resume_id, project_name, description) VALUES (?, ?, ?)",
                (resume_id, project.get("name"), project.get("description")),
            )
    conn.close()


def get_resume_by_id(resume_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,)).fetchone()


def list_resumes(limit: int = 200) -> List[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM resumes ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return list(rows)


def search_resumes(search_text: str, field: str = "candidate_name") -> List[sqlite3.Row]:
    query = f"SELECT * FROM resumes WHERE {field} LIKE ? ORDER BY created_at DESC"
    with get_connection() as conn:
        rows = conn.execute(query, (f"%{search_text}%",)).fetchall()
        return list(rows)


def list_chat_history(limit: int = 100) -> List[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_history ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return list(rows)


def save_chat_message(resume_id: Optional[int], user_message: str, assistant_message: str, session_id: str) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO chat_history (resume_id, user_message, assistant_message, session_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (resume_id, user_message, assistant_message, session_id, assistant_message and now_iso()),
        )
        return cursor.lastrowid


def save_candidate_score(data: Dict[str, Any]) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO candidate_scores (resume_id, job_description, score, semantic_similarity, skill_match, experience_match, education_match, label, details, generated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                data.get("resume_id"),
                data.get("job_description"),
                data.get("score"),
                data.get("semantic_similarity"),
                data.get("skill_match"),
                data.get("experience_match"),
                data.get("education_match"),
                data.get("label"),
                data.get("details"),
                now_iso(),
            ),
        )
        return cursor.lastrowid


def list_candidate_scores(limit: int = 100) -> List[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM candidate_scores ORDER BY generated_at DESC LIMIT ?", (limit,)).fetchall()
        return list(rows)


def resume_exists(resume_hash: str) -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT 1 FROM resumes WHERE resume_hash = ?", (resume_hash,)).fetchone()
        return row is not None
