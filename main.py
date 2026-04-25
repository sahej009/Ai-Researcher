import os
import json
import shutil
import time
import re
from queue import Queue
from langchain_groq import ChatGroq
from crewai import LLM
from threading import Thread
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from pypdf import PdfReader

# --- NEW IMPORTS FOR DATABASE ---
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# --- DATABASE SETUP ---
DATABASE_URL = "sqlite:///./research_history.db" # Creates a local file database
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the SQL Table schema
class ResearchHistory(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    result = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create the table in the database file
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_key = os.environ.get("GROQ_API_KEY")
os.makedirs("temp_uploads", exist_ok=True)

# The stable 70B model with strict tool adherence
groq_llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    temperature=0,
    max_tokens=4096
)

# GUARDRAIL 1: Explicit instructions on HOW to use the tool
@tool("search_internet")
def search_internet(query: str) -> str:
    """
    Search the internet for the latest information on a given topic.
    The input MUST be a single string representing the search query.
    Do not use any special characters or XML tags.
    """
    try:
        # We import it inside the function to avoid startup crashes
        from langchain_community.tools import DuckDuckGoSearchRun
        search = DuckDuckGoSearchRun()
        return search.run(query)
    except Exception as e:
        return f"Search failed. Please rely on your internal knowledge or document context. Error: {str(e)}"

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    file_path = f"temp_uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"status": "success", "file_path": file_path}

@app.get("/api/history")
def get_history():
    db = SessionLocal()
    history_records = db.query(ResearchHistory).order_by(ResearchHistory.created_at.desc()).all()
    db.close()
    return [{"id": r.id, "topic": r.topic, "result": r.result, "created_at": r.created_at} for r in history_records]

@app.get("/api/research")
def conduct_research(topic: str, file_path: str = None):
    queue = Queue()

    def agent_step_callback(step_action):
        queue.put(json.dumps({"type": "log", "message": "Agent is processing data..."}))

    def run_crew():
        try:
            queue.put(json.dumps({"type": "log", "message": f"Initializing workflow for: {topic}"}))
            
            extracted_text = ""
            if file_path and os.path.exists(file_path):
                queue.put(json.dumps({"type": "log", "message": f"Extracting text from PDF via Python..."}))
                reader = PdfReader(file_path)
                for page in reader.pages:
                    if page.extract_text():
                        extracted_text += page.extract_text() + "\n"
                queue.put(json.dumps({"type": "log", "message": f"Successfully extracted {len(extracted_text)} characters."}))

            researcher = Agent(
                role='Senior Tech Researcher',
                goal=f'Analyze data and uncover insights about: {topic}',
                backstory='You read provided documents and search the web to extract verified facts.',
                allow_delegation=False,
                verbose=False,  
                memory=False,   
                tools=[search_internet], 
                llm=groq_llm,
                step_callback=agent_step_callback
            )

            writer = Agent(
                role='Tech Content Strategist',
                goal='Craft compelling summaries based on raw research',
                backstory='You are a renowned tech writer.',
                allow_delegation=False,
                verbose=False,  
                memory=False,   
                llm=groq_llm,
                step_callback=agent_step_callback
            )

            editor = Agent(
                role='Chief Content Editor',
                goal='Ensure the final post is highly engaging and professional.',
                backstory='You are a meticulous tech editor who polishes content.',
                allow_delegation=False,
                verbose=False,  
                memory=False,   
                llm=groq_llm,
                step_callback=agent_step_callback
            )

            # GUARDRAIL 2: Strict tool rules injected into the prompt
            if extracted_text:
                task_desc = f"Analyze the following document text and search the web to research: {topic}. ONLY use the 'search_internet' tool if needed. Do NOT use tags like <function>.\n\n--- DOC START ---\n{extracted_text}\n--- DOC END ---"
            else:
                task_desc = f"Search the web to research: {topic}. Extract key facts. ONLY use the 'search_internet' tool. Do NOT use tags like <function>."

            # GUARDRAIL 3: max_inter limits the agent from looping into errors
            research_task = Task(
                description=task_desc, 
                expected_output='A list of findings.', 
                agent=researcher,
                max_inter=3 
            )
            
            write_task = Task(description='Write a comprehensive research report based on the findings. Use Markdown formatting including a main title (H1), section headers (H2), and bullet points for key data.', expected_output='A highly structured Markdown report.', agent=writer)
            edit_task = Task(description='Review and polish the drafted report. Ensure the Markdown formatting is perfect, professional, and highly readable.', expected_output='The final formatted Markdown report..', agent=editor)

            ai_crew = Crew(
                agents=[researcher, writer, editor],
                tasks=[research_task, write_task, edit_task],
                process=Process.sequential
            )

            # --- NEW AUTO-RETRY CODE WITH DYNAMIC WAIT TIME ---
            max_retries = 2
            delay_seconds = 20
            final_text = None

            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        queue.put(json.dumps({"type": "log", "message": f"Retrying task... (Attempt {attempt}/{max_retries})"}))
                    
                    result = ai_crew.kickoff()
                    final_text = str(result)
                    break  # If successful, break out of the retry loop

                except Exception as e:
                    error_str = str(e).lower()
                    if attempt < max_retries and ("rate limit" in error_str or "tokens" in error_str or "429" in error_str):
                        match = re.search(r"try again in (\d+\.?\d*)s", error_str)
                        if match:
                            exact_wait = float(match.group(1)) + 1.0
                        else:
                            exact_wait = 20.0 
                        delay_seconds = round(exact_wait, 2)
                        
                        queue.put(json.dumps({"type": "log", "message": f"API cooldown hit. Dynamically pausing for {delay_seconds} seconds..."}))
                        time.sleep(delay_seconds)
                    else:
                        raise e 
            
            db = SessionLocal()
            new_entry = ResearchHistory(topic=topic, result=final_text)
            db.add(new_entry)
            db.commit()
            db.close()
            
            queue.put(json.dumps({"type": "complete", "data": final_text}))
            
        except Exception as e:
            queue.put(json.dumps({"type": "error", "message": str(e)}))
        finally:
            queue.put("DONE")

    Thread(target=run_crew).start()

    def event_stream():
        while True:
            msg = queue.get()
            if msg == "DONE":
                break
            yield f"data: {msg}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")