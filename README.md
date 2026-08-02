# Financial News Researcher Backend 🚀

An asynchronous Python backend built with **FastAPI** designed to power an intelligent AI research agent for financial market analysis. The application automates stock research workflows by ingesting SEC filings (10-K/10-Q), aggregating market data, and leveraging **Agentic Retrieval-Augmented Generation (RAG)** to produce structured, evidence-based trade thesis reports.

---

## 🎯 Architecture & Objective

Transitioning from traditional web development into AI engineering requires moving beyond basic wrapper API calls. This project focuses on production-grade AI backend patterns:

* **Data Grounding:** Hybrid search (Vector + Keyword) over dense SEC filings to eliminate hallucinations.
* **Agentic Orchestration:** Multi-step reasoning loops using tools for web search, financial APIs, and vector database retrieval.
* **Structured Outputs:** Enforcing strict Pydantic schemas to ensure LLM outputs reliably integrate with frontend UIs.
* **Real-time UX:** Server-Sent Events (SSE) streaming agent execution steps to the client in real-time.

---

## 🛠️ Tech Stack & Tooling

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous Python Web Framework)
* **Package & Env Manager:** [`uv`](https://github.com/astral-sh/uv) (Ultra-fast Rust-based Python package manager)
* **Data Validation:** [Pydantic v2](https://docs.pydantic.dev/latest/)
* **Testing:** [pytest](https://docs.pytest.org/) & `httpx` / `TestClient`
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
│   │   └── ticker.py
│   └── routers/            # API routes grouped by feature domain
│       ├── __init__.py
│       └── tickers.py
├── tests/                  # Unit and integration test suite
│   ├── __init__.py
│   └── test_tickers.py
├── pyproject.toml          # Project dependencies and configuration
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
* Python 3.12+ installed
* `uv` package manager installed

### 1. Installation
Clone the repository and install dependencies using `uv`:

```bash
git clone [https://github.com/](https://github.com/)<YOUR_GITHUB_USERNAME>/financial-news-researcher-backend.git
cd financial-news-researcher-backend
uv sync
```

### 2. Running the development server
Start the local FastAPI development server:

```bash
uv run fastapi dev app/main.py
```
The server will spin up at `http://127.0.0.1:8000`


### 3. API Documentation
FastAPI automatically generates interactive OpenAPI documentation. Once the app is running, visit:
* **SwaggerUI**: `http://127.0.0.1:8000/docs`
* **ReDoc**: `http://127.0.0.1:8000/redoc`

## Running tests
Execute the automated pytest test suite:
```bash
uv run pytest
```
