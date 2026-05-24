import glob
import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class Document:
    page_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class SimpleVectorStore:
    def __init__(self, documents: List[Document], embedder: Optional[SentenceTransformer]):
        self.documents = documents
        self.embedder = embedder
        self.index: Optional[faiss.IndexFlatL2] = None
        self._build_index()

    def _build_index(self) -> None:
        if self.embedder is None or not self.documents:
            return

        texts = [doc.page_content for doc in self.documents]
        embeddings = self.embedder.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        embeddings = np.asarray(embeddings, dtype="float32")
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)

    def similarity_search(self, query: str, k: int = 2) -> List[Document]:
        if not query:
            return []

        if self.index is None or self.embedder is None:
            return self._keyword_search(query, k)

        query_embedding = self.embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        query_embedding = np.asarray(query_embedding, dtype="float32")
        limit = min(k, len(self.documents))
        _, indices = self.index.search(query_embedding, limit)
        return [self.documents[idx] for idx in indices[0] if 0 <= idx < len(self.documents)]

    def _keyword_search(self, query: str, k: int) -> List[Document]:
        query_terms = set(re.findall(r"\w+", query.lower()))
        if not query_terms:
            return []

        scored_documents = []
        for document in self.documents:
            doc_terms = set(re.findall(r"\w+", document.page_content.lower()))
            score = len(query_terms & doc_terms)
            if score > 0:
                scored_documents.append((score, document))

        scored_documents.sort(key=lambda item: item[0], reverse=True)
        return [document for _, document in scored_documents[:k]]


class RAGPipeline:
    def __init__(self, docs_folder: str = "docs", incident_file: str = "historical_incidents/sample_incidents.json"):
        self.docs_folder = docs_folder
        self.incident_file = incident_file
        self.sop_store: Optional[SimpleVectorStore] = None
        self.incident_store: Optional[SimpleVectorStore] = None
        self.incidents = []
        self.embedder = self._load_embedder()
        self._build_stores()

    def _load_embedder(self) -> Optional[SentenceTransformer]:
        try:
            return SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
        except Exception:
            return None

    def _build_stores(self) -> None:
        self._load_sop_documents()
        self._load_historical_incidents()

    def _create_store(self, documents: List[Document]) -> Optional[SimpleVectorStore]:
        if not documents:
            return None

        try:
            return SimpleVectorStore(documents, self.embedder)
        except Exception:
            return None

    def _load_sop_documents(self) -> None:
        documents: List[Document] = []
        for path in glob.glob(os.path.join(self.docs_folder, "*.txt")):
            try:
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read().strip()
                documents.append(Document(page_content=content, metadata={"source": os.path.basename(path)}))
            except Exception:
                continue

        self.sop_store = self._create_store(documents)

    def _load_historical_incidents(self) -> None:
        documents: List[Document] = []
        try:
            with open(self.incident_file, "r", encoding="utf-8") as file:
                self.incidents = json.load(file)
        except FileNotFoundError:
            self.incidents = []
            self.incident_store = None
            return
        except Exception:
            self.incidents = []
            self.incident_store = None
            return

        for incident in self.incidents:
            content = (
                f"Title: {incident.get('title', '')}\n"
                f"Description: {incident.get('description', '')}\n"
                f"Actions Taken: {incident.get('actions_taken', '')}\n"
                f"Status: {incident.get('status', '')}\n"
                f"Root Cause: {incident.get('root_cause', '')}\n"
            )
            documents.append(Document(page_content=content, metadata=incident))

        self.incident_store = self._create_store(documents)

    def retrieve_relevant_sop(self, alert_description: str, k: int = 2) -> List[Document]:
        if not self.sop_store or not alert_description:
            return []
        return self.sop_store.similarity_search(alert_description, k=k)

    def retrieve_similar_incidents(self, alert_description: str, k: int = 3) -> List[Document]:
        if not self.incident_store or not alert_description:
            return []
        return self.incident_store.similarity_search(alert_description, k=k)
