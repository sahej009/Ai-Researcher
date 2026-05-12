import os
import json
import shutil
import time
import re
from queue import Queue
from threading import Thread

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# --- DATABASE SETUP ---
DATABASE_URL = "sqlite:///./research_history.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ResearchHistory(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    result = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)
os.makedirs("temp_uploads", exist_ok=True)

# --- INSTANT FASTAPI BOOT ---
# Because there are no heavy AI imports at the top level, 
# Uvicorn will reach this line in milliseconds and open the port for Render.
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to cache models across requests
models_loaded = False
groq_llm_instance = None

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

    def run_crew():
        global models_loaded, groq_llm_instance
        try:
            queue.put(json.dumps({"type": "log", "message": "Loading AI Dependencies (This takes ~30 seconds on the first run)..."}))
            
            # --- DEEP LAZY IMPORTS ---
            # These massive libraries are only loaded into memory in the background thread!
            from crewai import LLM, Agent, Task, Crew, Process
            from crewai.tools import tool
            from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Settings
            from llama_index.vector_stores.qdrant import QdrantVectorStore
            from llama_index.embeddings.cohere import CohereEmbedding
            from llama_index.readers.file import PyMuPDFReader
            from llama_index.postprocessor.cohere_rerank import CohereRerank
            from llama_index.llms.groq import Groq as LlamaIndexGroq
            import qdrant_client

            # We define tools dynamically so they can access the imported @tool decorator
            @tool("search_internet")
            def search_internet(query: str) -> str:
                """Search the internet for the latest information on a given topic."""
                try:
                    from langchain_community.tools import DuckDuckGoSearchRun
                    search = DuckDuckGoSearchRun()
                    # UPDATED: Truncate tool output to prevent token bloat
                    return search.run(query)[:2000]
                except Exception as e:
                    return f"Search failed. Error: {str(e)}"

            @tool("search_pdf_database")
            def search_pdf_database(query: str) -> str:
                """Search the uploaded private PDF document for highly specific information."""
                try:
                    client = qdrant_client.QdrantClient(path="./qdrant_db")
                    vector_store = QdrantVectorStore(client=client, collection_name="current_research")
                    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
                    
                    cohere_rerank = CohereRerank(api_key=os.environ.get("COHERE_API_KEY"), top_n=3)
                    query_engine = index.as_query_engine(similarity_top_k=10, node_postprocessors=[cohere_rerank])
                    
                    response = query_engine.query(query)
                    # UPDATED: Truncate tool output to prevent token bloat
                    return str(response)[:2000]
                except Exception as e:
                    return f"Database search failed. Error: {str(e)}"

            # Load heavy models only once
            if not models_loaded:
                queue.put(json.dumps({"type": "log", "message": "Caching HuggingFace Embeddings..."}))
                Settings.embed_model = CohereEmbedding(
                    api_key=os.environ.get("COHERE_API_KEY"),
                    model_name="embed-english-v3.0",
                    input_type="search_document"
                )
                Settings.llm = LlamaIndexGroq(model="llama-3.3-70b-versatile", api_key=os.environ.get("GROQ_API_KEY"))
                
                groq_llm_instance = LLM(
                    model="groq/llama-3.3-70b-versatile",
                    temperature=0,
                    max_tokens=4096
                )
                models_loaded = True

            def agent_step_callback(step_action):
                queue.put(json.dumps({"type": "log", "message": "Agent is processing data..."}))

            queue.put(json.dumps({"type": "log", "message": f"Initializing workflow for: {topic}"}))
            agent_tools = [search_internet] 

            if file_path and os.path.exists(file_path):
                queue.put(json.dumps({"type": "log", "message": "High-Fidelity PDF detected. Building Vector Database..."}))
                if os.path.exists("./qdrant_db"):
                    shutil.rmtree("./qdrant_db")
                
                pdf_extractor = {".pdf": PyMuPDFReader()}
                documents = SimpleDirectoryReader(input_files=[file_path], file_extractor=pdf_extractor).load_data()
                
                queue.put(json.dumps({"type": "log", "message": "Chunking math & text into Qdrant..."}))
                client = qdrant_client.QdrantClient(path="./qdrant_db")
                vector_store = QdrantVectorStore(client=client, collection_name="current_research")
                storage_context = StorageContext.from_defaults(vector_store=vector_store)
                VectorStoreIndex.from_documents(documents, storage_context=storage_context)
                
                queue.put(json.dumps({"type": "log", "message": "Database ready! Equipping Agent with RAG Tool."}))
                agent_tools.append(search_pdf_database)
                task_desc = f"Research this topic: {topic}. You have access to a local PDF database. Use BOTH tools to cross-reference private facts with public news."
            else:
                task_desc = f"Search the web to research: {topic}. Extract key facts. ONLY use the 'search_internet' tool."

            researcher = Agent(
                role='Senior Tech Researcher',
                goal=f'Analyze data and uncover insights about: {topic}',
                backstory='You seamlessly navigate private databases and public web pages.',
                allow_delegation=False,
                verbose=False,  
                memory=False,   
                tools=agent_tools,
                llm=groq_llm_instance,
                max_iter=3, # UPDATED: Added iteration cap here to prevent infinite loops
                step_callback=agent_step_callback
            )

            writer = Agent(
                role='Tech Content Strategist',
                goal='Craft compelling summaries based on raw research',
                backstory='You are a renowned tech writer.',
                allow_delegation=False,
                verbose=False,  
                memory=False,   
                llm=groq_llm_instance,
                step_callback=agent_step_callback
            )

            editor = Agent(
                role='Chief Content Editor',
                goal='Ensure the final post is highly engaging and professional.',
                backstory='You are a meticulous tech editor.',
                allow_delegation=False,
                verbose=False,  
                memory=False,   
                llm=groq_llm_instance,
                step_callback=agent_step_callback
            )

            # UPDATED: Removed the typo 'max_inter=3' from this task
            research_task = Task(description=task_desc, expected_output='A list of findings.', agent=researcher)
            write_task = Task(description='Write a comprehensive report. Use Markdown.', expected_output='A structured report.', agent=writer)
            edit_task = Task(description='Review and polish the report.', expected_output='Final report.', agent=editor)
            
            ai_crew = Crew(
                agents=[researcher, writer, editor],
                tasks=[research_task, write_task, edit_task],
                process=Process.sequential
            )

            max_retries = 2
            delay_seconds = 20
            final_text = None

            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        queue.put(json.dumps({"type": "log", "message": f"Retrying task... (Attempt {attempt}/{max_retries})"}))
                    
                    result = ai_crew.kickoff()
                    final_text = str(result)
                    break 

                except Exception as e:
                    error_str = str(e).lower()
                    if attempt < max_retries and ("rate limit" in error_str or "tokens" in error_str or "429" in error_str):
                        match = re.search(r"try again in (\d+\.?\d*)s", error_str)
                        exact_wait = float(match.group(1)) + 1.0 if match else 20.0
                        delay_seconds = round(exact_wait, 2)
                        
                        queue.put(json.dumps({"type": "log", "message": f"API cooldown hit. Pausing for {delay_seconds} seconds..."}))
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