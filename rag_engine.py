import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from resume_parser import chunk_text
from utils import FAISS_DIR, call_openrouter, ensure_directories, now_iso

METADATA_FILE = FAISS_DIR / "metadata.pkl"
DOCS_FILE = FAISS_DIR / "documents.pkl"


@dataclass
class DocumentChunk:
    resume_id: int
    text: str
    metadata: Dict[str, str]


class SimpleVectorStore:
    """Pure-Python vector store without ML dependencies."""

    def __init__(self) -> None:
        ensure_directories()
        self.documents: List[DocumentChunk] = self._load_documents()
        self.metadata: List[Dict[str, any]] = self._load_metadata()

    def _load_documents(self) -> List[DocumentChunk]:
        if DOCS_FILE.exists():
            try:
                with open(DOCS_FILE, "rb") as stream:
                    return pickle.load(stream)
            except Exception:
                return []
        return []

    def _load_metadata(self) -> List[Dict[str, any]]:
        if METADATA_FILE.exists():
            try:
                with open(METADATA_FILE, "rb") as stream:
                    return pickle.load(stream)
            except Exception:
                return []
        return []

    def save_store(self) -> None:
        with open(METADATA_FILE, "wb") as stream:
            pickle.dump(self.metadata, stream)
        with open(DOCS_FILE, "wb") as stream:
            pickle.dump(self.documents, stream)

    def _text_similarity(self, text_a: str, text_b: str) -> float:
        """Compute Jaccard similarity between two texts."""
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())
        if not words_a or not words_b:
            return 0.0
        intersection = len(words_a & words_b)
        union = len(words_a | words_b)
        return intersection / union if union > 0 else 0.0

    def add_resume(self, resume_id: int, resume_text: str, file_name: str) -> int:
        chunks = chunk_text(resume_text, chunk_size=800, overlap=100)
        for chunk in chunks:
            self.metadata.append({
                "resume_id": resume_id,
                "file_name": file_name,
                "content": chunk,
                "created_at": now_iso(),
            })
            self.documents.append(DocumentChunk(resume_id=resume_id, text=chunk, metadata={"file_name": file_name}))
        self.save_store()
        return len(chunks)

    def remove_resume(self, resume_id: int) -> bool:
        """Remove all documents for a specific resume from the vector store."""
        original_count = len(self.documents)
        self.documents = [doc for doc in self.documents if doc.resume_id != resume_id]
        self.metadata = [meta for meta in self.metadata if meta.get("resume_id") != resume_id]
        removed_count = original_count - len(self.documents)
        if removed_count > 0:
            self.save_store()
            return True
        return removed_count > 0

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, any]]:
        if not self.metadata:
            return []
        scored_docs = []
        for idx, metadata in enumerate(self.metadata):
            content = metadata.get("content", "")
            score = self._text_similarity(query, content)
            scored_docs.append((score, idx, metadata))
        scored_docs.sort(key=lambda item: item[0], reverse=True)
        results = []
        for score, idx, metadata in scored_docs[:top_k]:
            results.append({
                "score": float(score),
                "resume_id": int(metadata["resume_id"]),
                "file_name": metadata.get("file_name", "Unknown"),
                "content": metadata.get("content", ""),
            })
        return results


class RAGEngine:
    def __init__(self) -> None:
        self.store = SimpleVectorStore()

    def index_resume(self, resume_id: int, resume_text: str, file_name: str) -> int:
        return self.store.add_resume(resume_id, resume_text, file_name)

    def retrieve_documents(self, query: str, top_k: int = 5) -> List[Dict[str, any]]:
        return self.store.search(query, top_k=top_k)

    def answer_query(self, api_key: str, model_name: str, query: str, top_k: int = 5) -> str:
        context_chunks = self.retrieve_documents(query, top_k=top_k)
        context = "\n\n".join([f"Candidate resume segment: {item['content']}" for item in context_chunks])
        prompt = (
            "You are a talent intelligence assistant for SBI recruiters. Use the following resume context snippets "
            "to answer the user query precisely and professionally.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            "Provide a concise answer and cite the strongest candidate evidence."
        )
        return call_openrouter(api_key=api_key, model_name=model_name, prompt=prompt)

    def build_prompt_for_candidate(self, resume_text: str, job_description: str) -> str:
        return (
            "You are an expert HR intelligence engine. Analyze this candidate resume text and the provided job description. "
            "Create a professional recruiting intelligence summary with strengths, weaknesses, skill assessment, leadership indicators, communication indicators, risk factors, "
            "suitable roles, and hiring recommendation.\n\n"
            f"Job Description:\n{job_description}\n\n"
            f"Resume Text:\n{resume_text}\n\n"
            "Answer in structured bullet points and assign one recommendation category: Strong Hire, Hire, Consider, Reject."
        )

    def remove_from_index(self, resume_id: int) -> bool:
        """Remove all documents for a specific resume from the vector store."""
        return self.store.remove_resume(resume_id)
