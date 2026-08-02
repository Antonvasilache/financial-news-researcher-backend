# Financial News Researcher Backend 🚀

![Python](https://img.shields.io/badge/Python-3.14%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141%2B-009688?logo=fastapi&logoColor=white)
![uv](https://img.shields.io/badge/package%20manager-uv-DE5FE9?logo=astral&logoColor=white)
![pytest](https://img.shields.io/badge/tested%20with-pytest-0A9EDC?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?logo=open-source-initiative&logoColor=white)

An asynchronous Python backend built with **FastAPI** designed to power an intelligent AI research agent for financial market analysis. The application automates stock research workflows by ingesting SEC filings (10-K/10-Q), aggregating market data, and leveraging **Agentic Retrieval-Augmented Generation (RAG)** to produce structured, evidence-based trade thesis reports.

---

## 🎯 Architecture & Objective

Transitioning from traditional web development into AI engineering requires moving beyond basic wrapper API calls. This project focuses on production-grade AI backend patterns:

* **Data Grounding:** Hybrid search (Vector + Keyword) over dense SEC filings to eliminate hallucinations.
* **Agentic Orchestration:** Multi-step reasoning loops using tools for web search, financial APIs, and vector database retrieval.
* **Structured Outputs:** Enforcing strict Pydantic schemas to ensure LLM outputs reliably integrate with frontend UIs.
* **Real-time UX:** Server-Sent Events (SSE) streaming agent execution steps to the client in real-time.

---

## 🚦 Feature Matrix

| Feature | Status | Description |
| :--- | :---: | :--- |
| **FastAPI Core & Routing** | ✅ Implemented | Asynchronous web framework setup with modular routers |
| **Tickers Management API** | ✅ Implemented | CRUD operations for stock tickers with schema validation & error handling |
| **Automated Test Suite** | ✅ Implemented | Isolated unit testing with `pytest` & `TestClient` |
| **SEC Filings Ingestion** | 🚧 Roadmap | Automated ingestion and parsing of 10-K and 10-Q filings |
| **Vector Store (ChromaDB)** | 🚧 Roadmap | Hybrid search indexing for financial document retrieval |
| **Agentic RAG Engine** | 🚧 Roadmap | Multi-step research workflow utilizing LangGraph / LangChain |
| **SSE Streaming** | 🚧 Roadmap | Real-time agent status and log streaming to frontend clients |

---

## 🛠️ Tech Stack & Tooling

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous Python Web Framework)
* **Package & Env Manager:** [`uv`](https://github.com/astral-sh/uv) (Ultra-fast Rust-based Python package manager)
* **Data Validation:** [Pydantic v2](https://docs.pydantic.dev/latest/)
* **Testing:** [pytest](https://docs.pytest.org/) & [`httpx`](https://www.python-httpx.org/) / `TestClient`
* **Agent & RAG Stack (Upcoming):** LangChain / LangGraph, ChromaDB

---

## 📁 Repository Structure

```text
financial-news-researcher-backend/
├── app/
│   ├── __init__.py
│   ├── main.py             # Application entrypoint & router setup
│   ├── schemas/            # Pydantic data models & request/response validation
│   │   ├── __init__.py
│   │   └── ticker.py       # Ticker schemas (TickerCreate, TickerResponse)
│   └── routers/            # API routes grouped by feature domain
│       ├── __init__.py
│       └── tickers.py      # Tickers CRUD endpoints
├── tests/                  # Unit and integration test suite
│   ├── __init__.py
│   └── test_tickers.py     # Tickers endpoint tests
├── .python-version         # Python version configuration (3.14)
├── pyproject.toml          # Project dependencies and configuration
├── uv.lock                 # Lockfile for reproducible environment builds
├── LICENSE                 # MIT License file
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
* Python 3.14+ installed
* [`uv`](https://github.com/astral-sh/uv) package manager installed

### 1. Installation
Clone the repository and install dependencies using `uv`:

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/financial-news-researcher-backend.git
cd financial-news-researcher-backend
uv sync
```

### 2. Running the Development Server
Start the local FastAPI development server:

```bash
uv run fastapi dev app/main.py
```
The server will spin up at `http://127.0.0.1:8000`.

### 3. API Documentation
FastAPI automatically generates interactive OpenAPI documentation. Once the app is running, visit:
* **SwaggerUI**: `http://127.0.0.1:8000/docs`
* **ReDoc**: `http://127.0.0.1:8000/redoc`

---

## 🧪 Running Tests

Execute the automated pytest test suite:

```bash
uv run pytest
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
