# ⚡ Agentic Research Hub (Enterprise V2)

[![Live Demo](https://img.shields.io/badge/Live_Demo-View_Here-success?style=for-the-badge&logo=vercel)](https://ai-researcher-five.vercel.app/)

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![React](https://img.shields.io/badge/React-Vite-cyan)
![Tailwind](https://img.shields.io/badge/Tailwind_CSS-38B2AC?logo=tailwind-css&logoColor=white)
![AI Engine](https://img.shields.io/badge/AI-CrewAI%20%7C%20Groq-orange)
![Vector DB](https://img.shields.io/badge/Database-Qdrant-red)

Agentic Research Hub V2 is a full-stack, enterprise-grade AI application engineered to solve the biggest challenges in modern AI: document hallucinations and token limits.

Built with a decoupled "Dual-Brain" architecture, it leverages **CrewAI** to orchestrate specialized agents that dynamically route queries between a local **Qdrant Vector Database** (for dense, private document analytics) and the live internet. All of this is wrapped in a sleek, 3-column B2B SaaS React dashboard.

---

## ✨ Key Features

- **Advanced RAG Pipeline:** Utilizes LlamaIndex to chunk, embed, and ingest massive, dense enterprise PDFs into a local Qdrant Vector Database.
- **Precision Reranking (Hallucination Mitigation):** Integrates a Cohere Cross-Encoder reranker to filter semantic noise, ensuring the AI only processes the exact paragraphs needed to answer highly technical queries, effectively bypassing standard token limits.
- **Multi-Agent Orchestration:** Deploys CrewAI to break down complex tasks into specialized autonomous roles (Senior Tech Researcher, Content Strategist, Chief Editor) with strict tool-calling guardrails.
- **Dynamic Tool Routing:** Agents autonomously decide whether to query the live internet (DuckDuckGo) or retrieve structured/unstructured data from local enterprise databases.
- **Enterprise SaaS UI:** A beautiful, responsive frontend built with React and Tailwind CSS, featuring a 3-column layout (Navigation, Data Workspace, and Live AI Copilot).
- **Asynchronous API Bridge:** Engineered with FastAPI and Pydantic to seamlessly orchestrate the python-based Agentic workflows and stream data to the front end.

---

## 🏗️ Architecture Stack

- **Frontend:** React, Vite, Tailwind CSS
- **Backend:** FastAPI, Python, Uvicorn
- **AI Framework:** CrewAI, LlamaIndex
- **RAG Stack:** Qdrant (Vector DB), Cohere (Reranker)
- **LLM Engine:** Groq (`llama-3.3-70b-versatile`)

---

## 🚀 Local Development Setup

Follow these steps to run the V2 application on your local machine.

### 1. Prerequisites

- Python 3.10+
- Node.js & npm
- Free API Keys for: [Groq](https://console.groq.com/keys) and [Cohere](https://dashboard.cohere.com/api-keys)

### 2. Clone the Repository

```bash
git clone [https://github.com/sahej009/Ai-researcher.git](https://github.com/sahej009/Ai-researcher.git)
cd Ai-researcher
3. Backend Setup (FastAPI & AI)
Open a terminal in the project root:

Bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Create a .env file and add your required API keys
echo "GROQ_API_KEY=gsk_your_groq_key_here" > .env
echo "COHERE_API_KEY=your_cohere_key_here" >> .env

# Run the FastAPI server
uvicorn main:app --reload
The backend will now be running on http://127.0.0.1:8000

4. Frontend Setup (React)
Open a second terminal window.

Bash
cd frontend

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev
The frontend will now be running on http://localhost:5173

☁️ Deployment
This project is configured for a split deployment architecture:

Backend: Deploy main.py and requirements.txt to Render as a Python Web Service. Ensure you add GROQ_API_KEY and COHERE_API_KEY to Render's environment variables.

Frontend: Update the fetch/API URLs in your React components to point to your live Render backend URL, then deploy the frontend to Vercel.
```
