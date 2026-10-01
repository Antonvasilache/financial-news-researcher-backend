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
| **Revenue Streams Research**| ✅ Implemented | LLM-powered company revenue streams & business model breakdown |
| **SEC Filings Ingestion** | ✅ Implemented | Automated ingestion and parsing of 10-K and 10-Q filings (Business, MD&A, Risk Factors) |
| **Automated Test Suite** | ✅ Implemented | Isolated unit testing with `pytest` & `TestClient` |
| **Financial Data Analysis & ML** | 📅 Planned | Quantitative financial ratio analysis & trend/anomaly detection |
| **Deep Learning & NLP Embeddings** | 📅 Planned | Domain embeddings (FinBERT) & sentiment neural nets |
| **LLM Fine-Tuning (PEFT/LoRA)** | 📅 Planned | Domain adaptation of open-source LLMs on financial filings |
| **Vector Store & Hybrid RAG** | 📅 Planned | ChromaDB dense + keyword retrieval over SEC filings |
| **Multi-Agent Orchestration & SSE** | 📅 Planned | LangChain/LangGraph research agents with real-time SSE streaming |

---

## 🗺️ Development Roadmap

### ✅ Phase 1: LLM-Powered Revenue Streams Analysis
- [x] **FastAPI Core Architecture:** Asynchronous API setup with Pydantic v2 validation models and modular routing.
- [x] **Tickers Management:** In-memory CRUD endpoints with validation and error handling for tracked company tickers.
- [x] **Prompt Engineering & Baseline Generation:** Hugging Face Inference integration to generate structured company revenue breakdowns and business models.
- [x] **Automated Test Suite:** Isolated unit tests with `pytest` and `TestClient` covering routing and mock LLM calls.

### ✅ Phase 2: SEC Filings Ingestion & 10-K/10-Q Parsing
- [x] **SEC EDGAR Ingestion Pipeline:** Automated search and retrieval of recent 10-K (annual) and 10-Q (quarterly) filings via SEC Submissions API.
- [x] **HTML Section Parsing:** Accurate extraction and cleaning of core filing sections:
  - *Item 1: Business*
  - *Item 1A: Risk Factors*
  - *Item 7: Management's Discussion and Analysis (MD&A)*
- [x] **Comprehensive Parser Test Coverage:** Pytest integration verifying filing retrieval, section boundaries, and fallback parsing logic.

### 📅 Phase 3: Financial Data Analysis & Machine Learning
- [ ] **Financial Metrics Extraction:** Quantitative analysis on financial statements (revenue growth, margins, balance sheet ratios).
- [ ] **Machine Learning Classifiers:** Financial trend classification and anomaly detection using scikit-learn.
- [ ] **Deep Learning Models (Keras):** Neural network baselines for price volatility prediction and document section classification.

### 📅 Phase 4: NLP Foundation Models & Transformer Architecture
- [ ] **Semantic Chunking & Data Prep:** Document chunking strategies tailored to tabular and narrative financial disclosures.
- [ ] **Domain-Specific Embeddings:** Integration with financial foundational models (e.g., FinBERT) for semantic representations.
- [ ] **Transformer-based Summarization:** Abstractive summarization for dense 10-K "Item 1A: Risk Factors" sections.

### 📅 Phase 5: Generative AI Engineering & Fine-Tuning
- [ ] **Domain Adaptation with PEFT / LoRA:** Parameter-efficient fine-tuning of open-weights LLMs (Llama/Mistral/Gemma) on financial disclosure Q&A datasets.
- [ ] **Model Evaluation & Benchmarks:** Systematic evaluation using ROUGE, BLEU, and financial domain factual accuracy metrics.

### 📅 Phase 6: Agentic RAG Systems & Real-Time Orchestration
- [ ] **Vector Store Indexing:** High-performance ChromaDB vector storage with hybrid search (dense semantic + keyword BM25).
- [ ] **LangChain & LangGraph Multi-Agent Workflows:** Autonomous agents collaborating across tasks (SEC Analyst, News Sentiment Researcher, Valuation Synthesizer).
- [ ] **Real-Time SSE Streaming:** Server-Sent Events delivering live agent thought processes and tool calls to frontend interfaces.
- [ ] **Full Financial Research Synthesis:** End-to-end automated generation of comprehensive, evidence-grounded trade thesis reports.

---

## 🛠️ Tech Stack & Tooling

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous Python Web Framework)
* **Package & Env Manager:** [`uv`](https://github.com/astral-sh/uv) (Ultra-fast Rust-based Python package manager)
* **Data Validation:** [Pydantic v2](https://docs.pydantic.dev/latest/)
* **HTML Parsing:** [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
* **Data Science & ML:** Pandas, NumPy, Scikit-learn, Keras
* **Transformers & Fine-Tuning:** Hugging Face Transformers, Datasets, PEFT, TRL, LoRA / QLoRA
* **Agent & RAG Stack:** LangChain, LangGraph, ChromaDB
* **Testing:** [pytest](https://docs.pytest.org/) & [`httpx`](https://www.python-httpx.org/) / `TestClient`

---

## 📁 Repository Structure

```text
financial-news-researcher-backend/
├── app/
│   ├── __init__.py
│   ├── main.py             # Application entrypoint & router setup
│   ├── core/               # Configuration & environment settings
│   │   ├── __init__.py
│   │   └── config.py
│   ├── schemas/            # Pydantic data models & request/response validation
│   │   ├── __init__.py
│   │   ├── research.py     # LLM Revenue analysis schemas
│   │   ├── sec.py          # SEC EDGAR metadata & filing section schemas
│   │   └── ticker.py       # Ticker schemas (TickerCreate, TickerResponse)
│   ├── services/           # Business logic & external API clients
│   │   ├── __init__.py
│   │   ├── revenue_researcher.py # Hugging Face LLM analysis service
│   │   └── sec_edgar.py    # SEC EDGAR fetcher & HTML section parser
│   └── routers/            # API routes grouped by feature domain
│       ├── __init__.py
│       ├── research.py     # Revenue research endpoints
│       ├── sec.py          # SEC filings listing & parsing endpoints
│       └── tickers.py      # Tickers CRUD endpoints
├── tests/                  # Unit and integration test suite
│   ├── __init__.py
│   ├── test_research.py    # Revenue research endpoint tests
│   ├── test_sec.py         # SEC filings ingestion & parser tests
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
