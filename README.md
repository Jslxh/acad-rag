# AcadRAG – Academic Retrieval-Augmented Generation Assistant

AcadRAG is a full-stack, AI-powered academic assistant that converts study PDFs into a persistent, interactive knowledge base.
It allows users to upload, manage, and query academic documents using natural language, delivering accurate, context-aware answers through a Retrieval-Augmented Generation (RAG) pipeline — all running locally and privacy-first.

## Features

* **User Authentication**: Secure login and registration system with user-isolated data.
* **Document Management (CRUD)**: Upload, view, and delete academic PDFs per user.
* **Multi-PDF Support**: Processes multiple academic documents together for richer context.
* **Text Extraction & Cleaning**: Uses 'pdfplumber' to extract clean, structured text from PDFs.
* **Chunk-Based Indexing**: Splits large documents into smaller chunks for efficient retrieval.
* **FAISS Vector Search**: Enables fast semantic search over indexed document embeddings.
* **Local AI Model Integration**: Works with Ollama models (e.g., gemma:2b-instruct) for question answering.
* **Context-Aware Q&A**: Combines retrieved document chunks with LLMs to generate detailed academic answers.
* **Offline & Privacy-Friendly**: Runs fully offline using Ollama; no data leaves the system.
* **SaaS-Ready Architecture**: Modular Flask-based design suitable for future cloud deployment.

## Project Structure

```text
ACADRAG
│
├── app.py                  # Flask application entry point
├── acad_rag.py              # Core RAG pipeline (ingest + query)
│
├── routes/
│   └── documents.py         # Document routes (upload, list, delete)
│
├── services/
│   └── document_service.py  # Document storage & indexing logic
│
├── templates/
│   ├── dashboard.html       # Main Q&A interface
│   ├── documents.html       # Document management UI
│   ├── login.html
│   └── register.html
│
├── static/                  # Static assets (CSS/JS if extended)
├── data/                    # User PDFs & FAISS indexes
│
├── users.db                 # SQLite user database
├── requirements.txt
├── README.md
├── .env.example
└── .gitignore
```

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Install Ollama (https://ollama.ai) and pull a model
ollama pull gemma:2b-instruct
ollama serve

# Run the AcadRAG web application
python app.py

# Open in browser
# http://127.0.0.1:8501

```

## Usage Flow

```text
1. Register / Login via the web interface
2. Upload academic PDFs from the Documents page
3. Ask questions from the Dashboard
4. Receive context-aware answers generated using RAG
```
## Privacy & Offline Support

* All documents remain on the local system
* No cloud dependency required
* Ideal for academic, institutional, and exam-prep use cases
* Production-ready & SaaS-extensible