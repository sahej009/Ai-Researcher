# ⚡ Agentic Research Hub (Enterprise V2)

[![Live Demo](https://img.shields.io/badge/Live_Demo-View_Here-success?style=for-the-badge&logo=vercel)](https://ai-researcher-five.vercel.app/)
![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![React](https://img.shields.io/badge/React-Vite-cyan)
![Tailwind](https://img.shields.io/badge/Tailwind_CSS-38B2AC?logo=tailwind-css&logoColor=white)
![AI Engine](https://img.shields.io/badge/AI-CrewAI%20%7C%20Groq-orange)
![Vector DB](https://img.shields.io/badge/Database-Qdrant-red)

Agentic Research Hub V2 is a full-stack, enterprise-grade AI application engineered to solve document hallucinations and token limits in dense enterprise retrieval.

Built with a decoupled "Dual-Brain" architecture, it leverages **CrewAI** to orchestrate specialized agents that dynamically route queries between a local **Qdrant Vector Database** (for dense, private document analytics) and the live internet via DuckDuckGo. The system is wrapped in a responsive, 3-column B2B SaaS React dashboard.

---

## 📈 Two-Stage RAG Retrieval Benchmarks

Evaluated using `benchmark_rag.py` over an enterprise semantic distractor corpus, comparing Stage-1 dense vector search (**Qdrant** + `sentence-transformers/all-MiniLM-L6-v2`) against Stage-2 cross-encoder reranking (**Cohere** `rerank-english-v3.0`):

| Pipeline Stage / Metric            | Stage 1: Qdrant Vector Search | Stage 2: + Cohere Reranker      | Engineering Takeaway                                                |
| :--------------------------------- | :---------------------------- | :------------------------------ | :------------------------------------------------------------------ |
| **Top-1 Retrieval Accuracy**       | 88.9%                         | **100.0%**                      | **+11.1% precision lift** on subtle semantic distractors            |
| **Top-3 Hit Rate**                 | 100.0%                        | **100.0%**                      | Ground-truth context consistently preserved in top candidates       |
| **Mean Reciprocal Rank (MRR@3)**   | 0.944                         | **1.000**                       | Ground-truth context promoted to the #1 rank prior to LLM synthesis |
| **Median Search / Rerank Latency** | **12.43 ms** (`18.94 ms` p95) | **371.66 ms** (`~384 ms` total) | Sub-400ms end-to-end two-stage retrieval pipeline                   |
| **Chunk Indexing Throughput**      | **225.4 ms** (16 chunks)      | —                               | **~71 chunks/sec** embedding and vector upsert rate                 |

---

## ✨ Key Features

- **Advanced RAG Pipeline:** Utilizes LlamaIndex to chunk, embed, and ingest dense enterprise PDFs into an on-disk Qdrant Vector Database.
- **Two-Stage Precision Reranking:** Integrates a Cohere Cross-Encoder (`rerank-english-v3.0`) to filter semantic noise, lifting Top-1 accuracy from 88.9% to 100% (1.000 MRR@3) while minimizing LLM prompt token costs.
- **Multi-Agent Orchestration:** Deploys CrewAI to break down complex research tasks into specialized autonomous roles (Senior Tech Researcher, Content Strategist, Chief Editor) with strict tool-calling guardrails.
- **Dynamic Tool Routing:** Agents autonomously decide whether to query live web search (DuckDuckGo) or retrieve private knowledge from local Qdrant collections.
- **Enterprise SaaS UI:** Built with React, Vite, and Tailwind CSS, featuring a 3-column layout (Navigation, Data Workspace, and Live AI Copilot).
- **Asynchronous API Bridge:** Engineered with FastAPI and Pydantic to orchestrate multi-agent workflows and stream responses to the client.

---

## 🏗️ Architecture Stack

- **Frontend:** React, Vite, Tailwind CSS
- **Backend:** FastAPI, Python 3.11, Uvicorn, Pydantic
- **Multi-Agent Framework:** CrewAI, asyncio
- **RAG & Retrieval:** LlamaIndex, Qdrant (Vector DB), Cohere Reranker, Hugging Face Embeddings
- **LLM Engine:** Groq (`llama-3.3-70b-versatile`)
- **Persistence:** SQLite (`research_history.db`)

---

## 🚀 Local Development Setup

Follow these steps to run the application on your local machine.

### 1. Prerequisites

- Python 3.10+
- Node.js & npm
- API Keys: [Groq Console](https://console.groq.com/keys) and [Cohere Dashboard](https://dashboard.cohere.com/api-keys)

### 2. Clone the Repository

```bash
git clone https://github.com/sahej009/Ai-researcher.git
cd Ai-researcher
```

### 3. Backend Setup (FastAPI & AI)

Open a terminal in the project root:

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -r requirements.txt

# Create a .env file and configure your API keys
echo "GROQ_API_KEY=your_groq_key_here" > .env
echo "COHERE_API_KEY=your_cohere_key_here" >> .env

# Run the FastAPI server
uvicorn main:app --reload
```

The backend will be running at `http://127.0.0.1:8000`.

### 4. Frontend Setup (React)

Open a second terminal window:

```bash
cd frontend

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev
```

The frontend will be running at `http://localhost:5173`.

### 5. Run the Retrieval Benchmark Suite

```bash
python benchmark_rag.py
```

---

## ☁️ Deployment

This project uses a split deployment architecture:

- **Backend:** Deploy `main.py` and `requirements.txt` to Render as a Python Web Service. Set `GROQ_API_KEY` and `COHERE_API_KEY` in Render environment variables.
- **Frontend:** Configure API endpoint environment variables in `frontend/src/` to point to the live Render backend URL, then deploy to Vercel.

---

## 🛡️ License

This project is for educational and portfolio demonstration purposes.
