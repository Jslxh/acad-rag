# acad_rag.py — SaaS-ready, FAST RAG backend

import os
import re
import pdfplumber
import pickle
import numpy as np
import faiss
import requests
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

# ================= CONFIG =================
BASE_DATA_DIR = "data/users"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:2b-instruct")

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"   # FAST + SMALL
MAX_CHUNK_LEN = 600                    # chunk size
MAX_CONTEXT_CHARS = 400                # HARD LIMIT PER CHUNK
DEFAULT_TOP_K = 3                      # speed
OLLAMA_TIMEOUT = 30                    # FAIL FAST

# ================= GLOBAL CACHES =================
_embedder = SentenceTransformer(EMBED_MODEL_NAME)
_FAISS_CACHE = {}   # user_id -> (faiss_index, chunks)

# ================= PATH HELPERS =================
def _user_paths(user_id):
    base = os.path.join(BASE_DATA_DIR, str(user_id))
    docs = os.path.join(base, "docs")
    faiss_dir = os.path.join(base, "faiss")
    notes = os.path.join(base, "notes.txt")

    os.makedirs(docs, exist_ok=True)
    os.makedirs(faiss_dir, exist_ok=True)

    return docs, faiss_dir, notes


# ================= TEXT UTILS =================
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text


def clean_text(text):
    text = re.sub(r"\n\s*\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_chunks(text, max_len=MAX_CHUNK_LEN):
    sentences = re.split(r"(?<=[.!?]) +", text)
    chunks, buf = [], ""
    for s in sentences:
        if len(buf) + len(s) <= max_len:
            buf += s + " "
        else:
            chunks.append(buf.strip())
            buf = s + " "
    if buf:
        chunks.append(buf.strip())
    return chunks


# ================= INGEST =================
def ingest_pdf(pdf_path, user_id):
    docs_dir, faiss_dir, notes_path = _user_paths(user_id)

    raw = extract_text_from_pdf(pdf_path)
    cleaned = clean_text(raw)

    # append notes
    with open(notes_path, "a", encoding="utf-8") as f:
        f.write("\n" + cleaned)

    chunks = split_chunks(cleaned)
    embeddings = _embedder.encode(chunks, convert_to_numpy=True)

    index_path = os.path.join(faiss_dir, "index.faiss")
    chunks_path = os.path.join(faiss_dir, "chunks.pkl")

    if os.path.exists(index_path):
        index = faiss.read_index(index_path)
        with open(chunks_path, "rb") as f:
            all_chunks = pickle.load(f)
    else:
        index = faiss.IndexFlatL2(embeddings.shape[1])
        all_chunks = []

    index.add(embeddings.astype("float32"))
    all_chunks.extend(chunks)

    faiss.write_index(index, index_path)
    with open(chunks_path, "wb") as f:
        pickle.dump(all_chunks, f)

    _FAISS_CACHE.pop(user_id, None)


# ================= OLLAMA =================
def call_ollama(prompt):
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2
                }
            },
            timeout=60
        )

        if r.status_code == 200:
            data = r.json()
            return data.get("response", "").strip()

        print("Ollama HTTP error:", r.status_code, r.text)
    except Exception as e:
        print("[Ollama exception]", e)

    return ""


# ================= QUERY =================
def query_rag(user_query, user_id, top_k=DEFAULT_TOP_K):
    _, faiss_dir, _ = _user_paths(user_id)

    index_path = os.path.join(faiss_dir, "index.faiss")
    chunks_path = os.path.join(faiss_dir, "chunks.pkl")

    if not os.path.exists(index_path):
        return {"answer": "⚠️ No documents uploaded yet."}

    if user_id in _FAISS_CACHE:
        index, chunks = _FAISS_CACHE[user_id]
    else:
        index = faiss.read_index(index_path)
        with open(chunks_path, "rb") as f:
            chunks = pickle.load(f)
        _FAISS_CACHE[user_id] = (index, chunks)

    q_emb = _embedder.encode([user_query], convert_to_numpy=True)
    _, idx = index.search(q_emb.astype("float32"), top_k)

    retrieved = [chunks[i][:MAX_CONTEXT_CHARS] for i in idx[0]]

    prompt = (
        "Answer concisely for exam preparation.\n"
        "Use bullet points if helpful.\n\n"
        f"NOTES:\n{chr(10).join(retrieved)}\n\n"
        f"QUESTION:\n{user_query}\n\nANSWER:"
    )

    answer = call_ollama(prompt)

    return {
        "answer": answer.strip() if answer else "⚠️ Model did not respond.",
        "retrieved": retrieved
    }
