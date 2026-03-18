"use client";

import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { Send, User, Bot, AlertCircle, FileText, CheckCircle2, XCircle, Info, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";

type SourceDocument = {
  filename: string;
  department: string;
  page: number | null;
  relevance_score: number;
};

type VerificationResult = {
  status: "Verified" | "Unverified" | "Partial" | "Blocked";
  reason: string;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceDocument[];
  confidence?: "High" | "Medium" | "Low";
  verification?: VerificationResult;
  latency_ms?: Record<string, number>;
  isError?: boolean;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Welcome to the **Government Scheme Assistant**. Ask me about Indian education policies, scholarships, or schemes.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await axios.post("http://localhost:8000/query", {
        query: userMessage.content,
        top_k: 5,
      });

      const { answer, sources, confidence, verification, latency_ms } = response.data;

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content: answer,
          sources,
          confidence,
          verification,
          latency_ms,
        },
      ]);
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.message || "Failed to connect to the server.";
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content: `**Error:** ${errorMsg}`,
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex flex-col h-screen bg-surface-100 font-sans">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-surface-50 border-b border-surface-300 shadow-sm sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-brand-500 rounded-lg flex items-center justify-center shadow-inner">
            <Bot className="text-white w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-surface-900 tracking-tight">Smart Retrieval RAG</h1>
            <p className="text-xs text-brand-600 font-medium">Government Scheme Assistant</p>
          </div>
        </div>
      </header>

      {/* Main Chat Area */}
      <div className="flex-1 overflow-y-auto px-4 py-8" ref={scrollRef}>
        <div className="max-w-4xl mx-auto space-y-8 pb-4">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {isLoading && (
            <div className="flex gap-4">
              <div className="w-8 h-8 rounded-full bg-brand-100 flex-shrink-0 flex items-center justify-center">
                <Bot className="w-5 h-5 text-brand-600" />
              </div>
              <div className="bg-surface-50 p-6 rounded-2xl rounded-tl-sm border border-brand-100 shadow-sm flex items-center justify-center">
                <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
                <span className="ml-3 text-surface-900 font-medium animate-pulse">Analyzing documents...</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Input Form */}
      <div className="bg-surface-50 border-t border-surface-300 p-4">
        <div className="max-w-4xl mx-auto relative">
          <form
            onSubmit={handleSubmit}
            className="flex items-end gap-3 bg-white p-2 rounded-2xl border border-surface-300 shadow-sm focus-within:ring-2 focus-within:ring-brand-500 focus-within:border-brand-500 transition-shadow"
          >
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              placeholder="Ask about AICTE scholarships, PM POSHAN eligibility..."
              className="flex-1 max-h-48 min-h-[52px] resize-none bg-transparent px-4 py-3 outline-none text-surface-900 placeholder:text-gray-400"
              rows={1}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="mb-1 mr-1 p-3 rounded-xl bg-brand-500 text-white hover:bg-brand-600 disabled:opacity-50 disabled:hover:bg-brand-500 transition-colors flex flex-shrink-0 items-center justify-center"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
          <p className="text-center text-xs text-gray-500 mt-3 font-medium">
            AI can make mistakes. Verify critical facts with official sources.
          </p>
        </div>
      </div>
    </main>
  );
}

// --- Components ---

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-4 ${isUser ? "flex-row-reverse" : ""}`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center
        ${isUser ? "bg-surface-900" : "bg-brand-100"}`}
      >
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : (
          <Bot className="w-5 h-5 text-brand-600" />
        )}
      </div>

      {/* Bubble Container */}
      <div
        className={`max-w-[85%] flex flex-col gap-3
        ${isUser ? "items-end" : "items-start"}`}
      >
        <div
          className={`px-6 py-4 rounded-2xl ${isUser
              ? "bg-surface-900 text-white rounded-tr-sm"
              : message.isError
                ? "bg-red-50 text-red-900 border border-red-200 rounded-tl-sm"
                : "bg-surface-50 border border-brand-100 shadow-sm rounded-tl-sm"
            }`}
        >
          <div className={`prose prose-sm max-w-none ${isUser ? "text-white prose-invert" : ""}`}>
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        </div>

        {/* Metadata section (sources, verification, latencies) */}
        {!isUser && !message.isError && message.sources && (
          <MessageMetadata message={message} />
        )}
      </div>
    </div>
  );
}

function MessageMetadata({ message }: { message: Message }) {
  const [showSources, setShowSources] = useState(false);

  const getConfidenceColor = (conf?: string) => {
    switch (conf) {
      case "High": return "bg-green-100 text-green-800 border-green-200";
      case "Medium": return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "Low": return "bg-red-100 text-red-800 border-red-200";
      default: return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const status = message.verification?.status;
  const isVerified = status === "Verified";
  const isUnverified = status === "Unverified" || status === "Blocked";

  return (
    <div className="w-full flex justify-between items-start gap-4">
      {/* Sources Toggle */}
      <div className="bg-surface-50 border border-surface-300 rounded-xl overflow-hidden w-full max-w-lg shadow-sm">
        <button
          onClick={() => setShowSources(!showSources)}
          className="w-full px-4 py-2.5 flex items-center justify-between hover:bg-surface-100 transition-colors"
        >
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-brand-500" />
            <span className="text-sm font-semibold text-surface-900">
              {message.sources?.length || 0} Sources
            </span>
          </div>
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            {showSources ? "Hide" : "Expand"}
          </span>
        </button>

        {showSources && (
          <div className="px-4 pb-3 pt-1 border-t border-surface-200 space-y-2 bg-white">
            {message.sources?.length === 0 ? (
              <p className="text-xs text-gray-500 italic py-2">No sources matched the query.</p>
            ) : (
              message.sources?.map((src, i) => (
                <div key={i} className="flex justify-between items-start text-xs p-2 rounded-md bg-surface-100 border border-surface-200">
                  <div className="flex gap-2">
                    <span className="font-mono bg-brand-50 text-brand-700 px-1.5 py-0.5 rounded border border-brand-200">{src.department}</span>
                    <span className="font-medium truncate max-w-[200px]" title={src.filename}>{src.filename}</span>
                  </div>
                  {src.page && <span className="text-gray-500 whitespace-nowrap">p. {src.page}</span>}
                </div>
              ))
            )}

            {/* Timing Data inside sources drawer */}
            {message.latency_ms && (
              <div className="flex gap-4 mt-3 pt-2 border-t border-dashed border-surface-300 text-[10px] text-gray-500 font-mono">
                <span>Ret: {message.latency_ms.retrieval}ms</span>
                <span>Gen: {message.latency_ms.generation}ms</span>
                <span>Chk: {message.latency_ms.verification}ms</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Badges Container */}
      <div className="flex flex-col gap-2 shrink-0 items-end">
        {/* Confidence Badge */}
        {message.confidence && (
          <div className={`px-2.5 py-1 rounded-full text-xs font-bold border ${getConfidenceColor(message.confidence)} flex items-center gap-1.5 shadow-sm`}>
            <span className="relative flex h-2 w-2">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${message.confidence === 'High' ? 'bg-green-400' : 'bg-yellow-400'}`}></span>
              <span className={`relative inline-flex rounded-full h-2 w-2 ${message.confidence === 'High' ? 'bg-green-500' : 'bg-yellow-500'}`}></span>
            </span>
            {message.confidence} Confidence
          </div>
        )}

        {/* Verification Badge */}
        {message.verification && (
          <div
            className={`group relative px-2.5 py-1 rounded-md text-xs font-semibold border flex items-center gap-1.5 cursor-help shadow-sm
                  ${isVerified ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                isUnverified ? 'bg-rose-50 text-rose-700 border-rose-200' :
                  'bg-slate-50 text-slate-700 border-slate-200'}`}
          >
            {isVerified ? <CheckCircle2 className="w-3.5 h-3.5" /> :
              isUnverified ? <XCircle className="w-3.5 h-3.5" /> :
                <Info className="w-3.5 h-3.5" />}
            {status} Fact-Check

            {/* Tooltip for reason */}
            <div className="absolute opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity bg-black text-white text-[11px] rounded py-1 px-2 right-0 bottom-full mb-1 w-48 text-right z-20 shadow-xl font-normal leading-tight">
              {message.verification.reason}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
