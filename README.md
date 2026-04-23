# ⚡ Agentic Research Hub

[![Live Demo](https://img.shields.io/badge/Live_Demo-View_Here-success?style=for-the-badge&logo=vercel)](https://ai-researcher-five.vercel.app/)

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![React](https://img.shields.io/badge/React-Vite-cyan)
![Tailwind](https://img.shields.io/badge/Tailwind_CSS-38B2AC?logo=tailwind-css&logoColor=white)
![AI Engine](https://img.shields.io/badge/AI-CrewAI%20%7C%20Groq-orange)

Agentic Research Hub is a full-stack, multi-agent AI application designed to conduct deep internet research and analyze private PDF documents. Built with a decoupled architecture, it leverages CrewAI to orchestrate multiple LLM agents (Researcher, Writer, Editor) powered by Groq's high-speed inference engine (Llama 3.3 70B), all wrapped in a sleek, enterprise-grade dark-mode UI.

---

## ✨ Key Features

- **Premium SaaS UI:** Beautifully designed using **Tailwind CSS** and **Shadcn UI**, featuring a responsive two-column workspace, a slide-out history drawer, and rich typography for Markdown rendering.
- **Multi-Agent Orchestration:** Uses CrewAI to break down complex research tasks into specialized roles (Researcher, Content Strategist, Editor).
- **Real-Time Streaming Terminal:** A custom React UI intercepts Server-Sent Events (SSE) to stream the AI's internal thought process and live status directly to the browser.
- **Dynamic Tool Routing:** Agents can autonomously browse the live internet (DuckDuckGo) or extract text from uploaded PDFs using Python-native context parsing.
- **Persistent History:** Automatically caches user sessions and research results into a local SQLite database for instant retrieval via the UI sidebar.
- **Hardened Architecture:** Engineered with strict JSON fallbacks, process guardrails, and optimized prompts to handle strict tool-calling environments without rate-limiting or hallucinating.

---

## 🏗️ Architecture Stack

- **Frontend:** React, Vite, Tailwind CSS, Shadcn UI, React Markdown, Lucide Icons
- **Backend:** FastAPI, Python, SSE, Uvicorn
- **AI Framework:** CrewAI, LangChain Tools
- **LLM Engine:** Groq (`llama-3.3-70b-versatile`)
- **Database:** SQLite (managed via SQLAlchemy)
- **File Parsing:** PyPDF

---

## 🚀 Local Development Setup

Follow these steps to run the application on your local machine.

### 1. Prerequisites

- Python 3.10+
- Node.js & npm
- A free [Groq API Key](https://console.groq.com/keys)

### 2. Clone the Repository

```bash
git clone [https://github.com/sahej009/Ai-researcher.git](https://github.com/sahej009/Ai-researcher.git)
cd Ai-researcher
3. Backend Setup (FastAPI & AI)
Open a terminal in the project root:

Bash
# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Create a .env file and add your Groq API key
echo "GROQ_API_KEY=gsk_your_api_key_here" > .env

# Run the FastAPI server
uvicorn main:app --reload
The backend will now be running on http://127.0.0.1:8000

4. Frontend Setup (React)
Open a second terminal window. If your React code is inside a frontend folder, navigate there first:

Bash
cd frontend

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev
The frontend will now be running on http://localhost:5173

☁️ Deployment
This project is configured for a split deployment architecture:

Backend: Deploy main.py and requirements.txt to Render as a Python Web Service. Ensure you set the GROQ_API_KEY in Render's environment variables.

Frontend: Update the API_URL variable in src/App.jsx to point to your live Render backend URL, then deploy the frontend repository to Vercel.

Note: Free-tier cloud providers use ephemeral file systems. SQLite history and temporary PDF uploads will reset if the server spins down.

📝 License
This project is open-source and available under the MIT License.
```
