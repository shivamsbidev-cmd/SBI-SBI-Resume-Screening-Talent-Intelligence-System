import os
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from resume_parser import chunk_text
from utils import FAISS_DIR, call_openrouter, ensure_directories, json_serialize, now_iso

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
INDEX_FILE = FAISS_DIR / "faiss.index"
METADATA_FILE = FAISS_DIR / "metadata.pkl"
DOCS_FILE = FAISS_DIR / "documents.pkl"


@dataclass
class DocumentChunk:
    resume_id: int
    text: str
    metadata: Dict[str, str]


class FaissManager:
    def __init__(self) -> None:
        ensure_directories()
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = self._load_or_init_index()
        self.metadata: List[Dict[str, any]] = self._load_metadata()
        self.documents: List[DocumentChunk] = self._load_documents()

    def _load_or_init_index(self) -> faiss.Index:
        if INDEX_FILE.exists():
            try:
                index = faiss.read_index(str(INDEX_FILE))
                return index
            except Exception:
                pass
        return faiss.IndexFlatIP(self.dimension)

    def _load_metadata(self) -> List[Dict[str, any]]:
        if METADATA_FILE.exists():
            try:
                with open(METADATA_FILE, "rb") as stream:
                    return pickle.load(stream)
            except Exception:
                return []
        return []

    def _load_documents(self) -> List[DocumentChunk]:
        if DOCS_FILE.exists():
            try:
                with open(DOCS_FILE, "rb") as stream:
                    return pickle.load(stream)
            except Exception:
                return []
        return []

    def save_index(self) -> None:
        faiss.write_index(self.index, str(INDEX_FILE))
        with open(METADATA_FILE, "wb") as stream:
            pickle.dump(self.metadata, stream)
        with open(DOCS_FILE, "wb") as stream:
            pickle.dump(self.documents, stream)

    def embed_text(self, text: str) -> np.ndarray:
        embeddings = self.model.encode([text], normalize_embeddings=True)
        return embeddings.astype("float32")[0]

    def add_resume(self, resume_id: int, resume_text: str, file_name: str) -> int:
        chunks = chunk_text(resume_text, chunk_size=800, overlap=100)
        embeddings = self.model.encode(chunks, normalize_embeddings=True).astype("float32")
        self.index.add(embeddings)
        for chunk, embedding in zip(chunks, embeddings):
            self.metadata.append({
                "resume_id": resume_id,
                "file_name": file_name,
                "content": chunk,
                "created_at": now_iso(),
            })
            self.documents.append(DocumentChunk(resume_id=resume_id, text=chunk, metadata={"file_name": file_name}))
        self.save_index()
        return len(chunks)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, any]]:
        if self.index.ntotal == 0:
            return []
        query_embedding = self.embed_text(query)[None, :]
        scores, indexes = self.index.search(query_embedding, top_k)
        results: List[Dict[str, any]] = []
        for score, idx in zip(scores[0], indexes[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            metadata = self.metadata[idx]
            results.append({
                "score": float(score),
                "resume_id": int(metadata["resume_id"]),
                "file_name": metadata.get("file_name", "Unknown"),
                "content": metadata.get("content", ""),
            })
        return results


class RAGEngine:
    def __init__(self) -> None:
        self.faiss_manager = FaissManager()

    def index_resume(self, resume_id: int, resume_text: str, file_name: str) -> int:
        return self.faiss_manager.add_resume(resume_id, resume_text, file_name)

    def retrieve_documents(self, query: str, top_k: int = 5) -> List[Dict[str, any]]:
        return self.faiss_manager.search(query, top_k=top_k)

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
