# ⚡ Agentic Research Hub

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![React](https://img.shields.io/badge/React-Vite-cyan)
![AI Engine](https://img.shields.io/badge/AI-CrewAI%20%7C%20Groq-orange)

Agentic Research Hub is a full-stack, multi-agent AI application designed to conduct deep internet research and analyze private PDF documents. Built with a decoupled architecture, it leverages CrewAI to orchestrate multiple LLM agents (Researcher, Writer, Editor) powered by Groq's high-speed inference engine.

## ✨ Key Features

* **Multi-Agent Orchestration:** Uses CrewAI to break down complex research tasks into specialized roles.
* **Dynamic Tool Routing:** Agents can autonomously browse the live internet (DuckDuckGo) or extract text from uploaded PDFs using Python-native Context Stuffing.
* **Real-Time Streaming Terminal:** A custom React UI intercepts Server-Sent Events (SSE) to stream the AI's internal thought process and logs directly to the browser.
* **Persistent History:** Automatically caches user sessions and research results into a local SQLite database for instant retrieval.
* **Strict JSON Fallbacks:** Engineered to handle LLM parsing errors by utilizing models optimized for structured tool calling.

## 🏗️ Architecture Stack

* **Frontend:** React, Vite, React Markdown, standard CSS
* **Backend:** FastAPI, Python, SSE, Uvicorn
* **AI Framework:** CrewAI, LangChain Tools
* **LLM Engine:** Groq (OpenAI OSS / Llama 3 models)
* **Database:** SQLite (managed via SQLAlchemy)
* **File Parsing:** PyPDF

---

## 🚀 Local Development Setup

Follow these steps to run the application on your local machine.

### 1. Prerequisites
* Python 3.10+
* Node.js & npm
* A free [Groq API Key](https://console.groq.com/keys)

### 2. Clone the Repository
```bash
git clone [https://github.com/sahej009/Ai-researcher.git](https://github.com/sahej009/Ai-researcher.git)
cd Ai-researcher
