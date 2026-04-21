import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import './App.css'

function App() {
  const [topic, setTopic] = useState('')
  const [file, setFile] = useState(null)
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState([])
  const [copied, setCopied] = useState(false)
  
  // NEW: State for History
  const [history, setHistory] = useState([])
  const logsEndRef = useRef(null)

  // NEW: Fetch history when the app loads
  const fetchHistory = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/history");
      const data = await res.json();
      setHistory(data);
    } catch (err) {
      console.error("Failed to fetch history");
    }
  }

  useEffect(() => {
    fetchHistory();
  }, [])

  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs])

  // NEW: Load an old search from history
  const loadHistoryItem = (item) => {
    setTopic(item.topic);
    setResult(item.result);
    setLogs([]); // Clear logs since we aren't generating live
  }

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0])
    }
  }

  const handleResearch = async () => {
    if (!topic) return;
    
    setLoading(true)
    setResult('')
    setLogs([])
    setCopied(false)

    let uploadedFilePath = '';

    if (file) {
      setLogs((prev) => [...prev, `Uploading document: ${file.name}...`]);
      const formData = new FormData();
      formData.append("file", file);

      try {
        const uploadRes = await fetch("http://127.0.0.1:8000/api/upload", {
          method: "POST",
          body: formData
        });
        const uploadData = await uploadRes.json();
        if (uploadData.status === "success") {
          uploadedFilePath = uploadData.file_path;
          setLogs((prev) => [...prev, `Upload complete! Initializing AI agents...`]);
        }
      } catch (err) {
        setLogs((prev) => [...prev, `CRITICAL ERROR: Failed to upload file.`]);
        setLoading(false);
        return;
      }
    }

    const streamUrl = `http://127.0.0.1:8000/api/research?topic=${encodeURIComponent(topic)}&file_path=${encodeURIComponent(uploadedFilePath)}`;
    const eventSource = new EventSource(streamUrl);

    eventSource.onmessage = (event) => {
      const parsedData = JSON.parse(event.data);
      
      if (parsedData.type === 'log') {
        setLogs((prev) => [...prev, parsedData.message]);
      } else if (parsedData.type === 'complete') {
        setResult(parsedData.data);
        eventSource.close();
        setLoading(false);
        fetchHistory(); // <-- NEW: Refresh history sidebar after generation!
      } else if (parsedData.type === 'error') {
        setLogs((prev) => [...prev, `CRITICAL ERROR: ${parsedData.message}`]);
        eventSource.close();
        setLoading(false);
      }
    };

    eventSource.onerror = () => {
      setLogs((prev) => [...prev, 'Connection to server closed.']);
      eventSource.close();
      setLoading(false);
    };
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(result);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="dashboard">
      {/* --- NEW: SIDEBAR --- */}
      <div className="sidebar">
        <h3 className="sidebar-title">📚 History</h3>
        <button className="new-chat-btn" onClick={() => { setTopic(''); setResult(''); setLogs([]); }}>
          + New Research
        </button>
        <div className="history-list">
          {history.map((item) => (
            <div key={item.id} className="history-item" onClick={() => loadHistoryItem(item)}>
              <span className="history-topic">{item.topic}</span>
              <span className="history-date">{new Date(item.created_at).toLocaleDateString()}</span>
            </div>
          ))}
          {history.length === 0 && <p className="no-history">No past research.</p>}
        </div>
      </div>

      {/* --- MAIN CONTENT (Your existing UI) --- */}
      <div className="main-content">
        <div className="container">
          <h1>🤖 Agentic Research Hub</h1>
          <p>Powered by CrewAI, Groq, and React</p>
          
          <div className="search-box">
            <input 
              type="text" 
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Ask a question or enter a topic..."
              disabled={loading}
            />
            <input 
              type="file" 
              accept=".pdf"
              onChange={handleFileChange}
              disabled={loading}
              className="file-input"
            />
            <button onClick={handleResearch} disabled={loading || !topic}>
              {loading ? 'Analyzing...' : 'Generate Post'}
            </button>
          </div>

          {(logs.length > 0 || loading) && (
            <div className="terminal">
              <div className="terminal-header">
                <span className="dot red"></span>
                <span className="dot yellow"></span>
                <span className="dot green"></span>
                <span className="title">Agent Status Terminal</span>
              </div>
              <div className="terminal-body">
                {logs.map((log, index) => (
                  <div key={index} className="log-line">
                    <span className="timestamp">[{new Date().toLocaleTimeString()}]</span> {log}
                  </div>
                ))}
                {loading && <div className="log-line animate-pulse">_</div>}
                <div ref={logsEndRef} />
              </div>
            </div>
          )}
          
          {result && (
            <div className="result-box fade-in">
              <div className="result-header">
                <h2>Final Output:</h2>
                <button className="copy-btn" onClick={handleCopy}>
                  {copied ? '✅ Copied!' : '📋 Copy to Clipboard'}
                </button>
              </div>
              <div className="markdown-content">
                <ReactMarkdown>{result}</ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App