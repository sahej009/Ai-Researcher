import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Terminal,
  FileText,
  Search,
  Upload,
  History,
  Clock,
  Copy,
  Check,
} from "lucide-react";

// Pointing directly to your live Render backend!
const API_URL = "https://ai-researcher-whvn.onrender.com";

export default function App() {
  const [topic, setTopic] = useState("");
  const [file, setFile] = useState(null);
  const [isResearching, setIsResearching] = useState(false);
  const [logs, setLogs] = useState([]);
  const [result, setResult] = useState("");
  const [history, setHistory] = useState([]);
  const [copied, setCopied] = useState(false); // Brought back your copy state!

  const scrollRef = useRef(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_URL}/api/history`);
      const data = await res.json();
      setHistory(data);
    } catch (error) {
      console.error("Failed to fetch history", error);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  // Brought back your copy function!
  const handleCopy = () => {
    navigator.clipboard.writeText(result);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const startResearch = async () => {
    if (!topic) return;
    setIsResearching(true);
    setLogs(["[SYSTEM] Initializing Agentic Research Hub..."]);
    setResult("");
    setCopied(false);

    let uploadedFilePath = "";

    if (file) {
      setLogs((prev) => [
        ...prev,
        `[SYSTEM] Uploading document: ${file.name}...`,
      ]);
      const formData = new FormData();
      formData.append("file", file);
      try {
        const uploadRes = await fetch(`${API_URL}/api/upload`, {
          method: "POST",
          body: formData,
        });
        const uploadData = await uploadRes.json();
        if (uploadData.status === "success") {
          uploadedFilePath = uploadData.file_path;
          setLogs((prev) => [
            ...prev,
            "[SYSTEM] Document uploaded successfully. Initializing agents...",
          ]);
        }
      } catch (error) {
        setLogs((prev) => [...prev, "[ERROR] Failed to upload document."]);
        return;
      }
    }

    const encodedTopic = encodeURIComponent(topic);
    const encodedPath = encodeURIComponent(uploadedFilePath);
    const eventSource = new EventSource(
      `${API_URL}/api/research?topic=${encodedTopic}&file_path=${encodedPath}`,
    );

    eventSource.onmessage = (event) => {
      const parsedData = JSON.parse(event.data);

      if (parsedData.type === "log") {
        setLogs((prev) => [...prev, `[AGENT] ${parsedData.message}`]);
      } else if (parsedData.type === "complete") {
        setResult(parsedData.data);
        eventSource.close();
        fetchHistory();
      } else if (parsedData.type === "error") {
        setLogs((prev) => [...prev, `[ERROR] ${parsedData.message}`]);
        eventSource.close();
      }
    };

    eventSource.onerror = () => {
      setLogs((prev) => [...prev, "[SYSTEM] Connection to server closed."]);
      eventSource.close();
    };
  };

  const loadHistoryItem = (item) => {
    setTopic(item.topic);
    setResult(item.result);
    setLogs([
      `[SYSTEM] Loaded past research session from ${new Date(item.created_at).toLocaleDateString()}`,
    ]);
    setIsResearching(true);
  };

  if (!isResearching) {
    return (
      <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center p-4 relative">
        <div className="absolute top-6 right-6">
          <Sheet>
            <SheetTrigger asChild>
              <Button
                variant="outline"
                className="border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800"
              >
                <History className="w-4 h-4 mr-2" />
                History
              </Button>
            </SheetTrigger>
            <SheetContent className="bg-zinc-950 border-zinc-800 text-zinc-100 w-[400px]">
              <SheetHeader>
                <SheetTitle className="text-zinc-100 flex items-center gap-2">
                  <History className="w-5 h-5" /> Past Research
                </SheetTitle>
              </SheetHeader>
              <div className="mt-6 flex flex-col gap-3">
                {history.length === 0 ? (
                  <p className="text-zinc-500 text-sm">
                    No past sessions found.
                  </p>
                ) : (
                  history.map((item) => (
                    <Card
                      key={item.id}
                      className="bg-zinc-900 border-zinc-800 cursor-pointer hover:border-zinc-600 transition-colors"
                      onClick={() => loadHistoryItem(item)}
                    >
                      <CardHeader className="p-4">
                        <CardTitle className="text-sm font-medium text-zinc-200">
                          {item.topic}
                        </CardTitle>
                        <p className="text-xs text-zinc-500 flex items-center gap-1 mt-1">
                          <Clock className="w-3 h-3" />{" "}
                          {new Date(item.created_at).toLocaleDateString()}
                        </p>
                      </CardHeader>
                    </Card>
                  ))
                )}
              </div>
            </SheetContent>
          </Sheet>
        </div>

        <Card className="w-full max-w-2xl bg-zinc-900/50 border-zinc-800 text-zinc-100 backdrop-blur-xl">
          <CardHeader className="text-center pb-2">
            <CardTitle className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-zinc-100 to-zinc-500 bg-clip-text text-transparent">
              Agentic Research Hub
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6 pt-4">
            <div className="flex gap-2">
              <Input
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && startResearch()}
                placeholder="What are we researching today?"
                className="bg-zinc-950/50 border-zinc-700 text-zinc-100 h-12 text-lg"
              />
              <Button
                onClick={startResearch}
                className="bg-white text-black hover:bg-zinc-200 h-12 px-8 font-semibold"
              >
                <Search className="w-4 h-4 mr-2" />
                Start
              </Button>
            </div>

            <label className="flex items-center justify-center border-2 border-dashed border-zinc-800 rounded-lg p-6 hover:bg-zinc-800/50 transition-colors cursor-pointer text-zinc-400">
              <input
                type="file"
                className="hidden"
                accept=".pdf"
                onChange={handleFileChange}
              />
              <div className="flex flex-col items-center gap-2">
                <Upload className="w-6 h-6" />
                <span className="text-sm font-medium">
                  {file ? (
                    <span className="text-emerald-400">{file.name}</span>
                  ) : (
                    "Click to attach a PDF for context (Optional)"
                  )}
                </span>
              </div>
            </label>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-4 md:p-8 flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold tracking-tight">
          Agentic Research Hub
        </h1>
        <div className="flex gap-3">
          <Button
            variant="outline"
            className="border-zinc-700 bg-zinc-900 hover:bg-zinc-800 text-zinc-300"
            onClick={() => {
              setIsResearching(false);
              setFile(null);
              setTopic("");
            }}
          >
            New Search
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1 h-[calc(100vh-100px)]">
        <Card className="bg-black border-zinc-800 flex flex-col overflow-hidden">
          <CardHeader className="py-3 px-4 border-b border-zinc-800 bg-zinc-900/50 flex flex-row items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-mono text-zinc-400">
              <Terminal className="w-4 h-4" />
              agent-logs.sh
            </div>
            {!result && (
              <Badge
                variant="outline"
                className="border-emerald-500/30 text-emerald-400 bg-emerald-500/10 animate-pulse"
              >
                Agents Running
              </Badge>
            )}
          </CardHeader>
          <CardContent className="p-0 flex-1 relative">
            <div
              ref={scrollRef}
              className="absolute inset-0 overflow-y-auto p-4 font-mono text-sm text-zinc-300"
            >
              {logs.map((log, i) => (
                <div
                  key={i}
                  className="mb-2 opacity-80 hover:opacity-100 transition-opacity"
                >
                  <span
                    className={
                      log.includes("[ERROR]")
                        ? "text-red-400"
                        : log.includes("[SYSTEM]")
                          ? "text-zinc-500"
                          : "text-emerald-400"
                    }
                  >
                    <span className="text-zinc-600 mr-2">
                      [{new Date().toLocaleTimeString()}]
                    </span>
                    {log}
                  </span>
                </div>
              ))}
              {!result && (
                <div className="animate-pulse text-zinc-500 mt-4">_</div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800 flex flex-col overflow-hidden">
          <CardHeader className="py-3 px-4 border-b border-zinc-800 bg-zinc-950/50 flex flex-row items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-zinc-400" />
              <span className="text-sm font-medium text-zinc-300">
                Research Synthesis
              </span>
            </div>
            {/* The beautiful new copy button! */}
            {result && (
              <Button
                variant="ghost"
                size="sm"
                className="h-8 text-zinc-400 hover:text-white hover:bg-zinc-800"
                onClick={handleCopy}
              >
                {copied ? (
                  <Check className="w-4 h-4 text-emerald-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </Button>
            )}
          </CardHeader>
          <CardContent className="p-0 flex-1">
            <ScrollArea className="h-full p-6">
              {!result ? (
                <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-4 pt-20">
                  <div className="w-8 h-8 border-4 border-zinc-700 border-t-emerald-500 rounded-full animate-spin"></div>
                  <p>Awaiting analysis completion...</p>
                </div>
              ) : (
                <div className="prose prose-invert max-w-none text-zinc-300">
                  <ReactMarkdown>{result}</ReactMarkdown>
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
