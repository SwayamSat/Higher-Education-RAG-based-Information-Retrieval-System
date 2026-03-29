"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, Loader2, Menu, Settings, BarChart } from "lucide-react";
import Link from "next/link";
import { MessageBubble, Message } from "../components/MessageBubble";
import { Sidebar, ChatSession } from "../components/Sidebar";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    const saved = localStorage.getItem("rag_sessions");
    if (saved) {
      const parsed = JSON.parse(saved);
      setSessions(parsed);
      if (parsed.length > 0) {
        loadSession(parsed[0].id, parsed);
      } else {
        createNewSession();
      }
    } else {
      createNewSession();
    }
  }, []);

  const createNewSession = () => {
    const newId = Date.now().toString();
    const newSession = { id: newId, title: "New Chat", updatedAt: new Date().toISOString() };
    setSessions(prev => [newSession, ...prev]);
    setActiveSessionId(newId);
    setMessages([{
      id: "welcome", role: "assistant", 
      content: "Welcome to the **Higher Education Assistant**. Ask me about AICTE norms, educational policies, or university guidelines."
    }]);
  };

  const loadSession = (id: string, currentSessions = sessions) => {
    setActiveSessionId(id);
    const msgs = localStorage.getItem(`rag_messages_${id}`);
    if (msgs) {
      setMessages(JSON.parse(msgs));
    } else {
      setMessages([{ id: "welcome", role: "assistant", content: "Welcome! Ask me a question." }]);
    }
  };

  const saveMessages = (msgs: Message[], sessId: string, isNewQuery = false) => {
    localStorage.setItem(`rag_messages_${sessId}`, JSON.stringify(msgs));
    if (isNewQuery) {
      setSessions(prev => {
        const updated = prev.map(s => {
          if (s.id === sessId && s.title === "New Chat" && msgs.length > 1) {
            const firstUserMsg = msgs.find(m => m.role === "user");
            return { ...s, title: firstUserMsg?.content.slice(0, 40) + "...", updatedAt: new Date().toISOString() };
          }
          if (s.id === sessId) return { ...s, updatedAt: new Date().toISOString() };
          return s;
        });
        localStorage.setItem("rag_sessions", JSON.stringify(updated));
        return updated;
      });
    }
  };

  const handleDeleteSession = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const newSessions = sessions.filter(s => s.id !== id);
    setSessions(newSessions);
    localStorage.removeItem(`rag_messages_${id}`);
    if (activeSessionId === id) {
      if (newSessions.length > 0) loadSession(newSessions[0].id, newSessions);
      else createNewSession();
    }
    localStorage.setItem("rag_sessions", JSON.stringify(newSessions));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { id: Date.now().toString(), role: "user", content: input };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    saveMessages(newMessages, activeSessionId, true);
    setInput("");
    setIsLoading(true);

    const tempAssistantId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, {
      id: tempAssistantId, role: "assistant", content: "", isStreaming: true
    }]);

    try {
      const response = await fetch("http://localhost:8000/query/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMessage.content, top_k: 5 }),
      });

      if (!response.ok) throw new Error("Failed to connect to stream.");

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let currentAnswer = "";

      if (reader) {
        let buffer = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || ""; 
          
          for (const chunk of lines) {
            if (!chunk.trim()) continue;
            const eventMatch = chunk.match(/event: (.+)/);
            const dataMatch = chunk.match(/data: ([\s\S]*)/);
            
            if (eventMatch && dataMatch) {
              const eventType = eventMatch[1].trim();
              const dataStr = dataMatch[1].trim();
              let data = {};
              try { data = dataStr ? JSON.parse(dataStr) : {}; } catch (e) {}
              
              if (eventType === "token") {
                currentAnswer += (data as any).text;
              }

              setMessages(prev => {
                const updatedMsgs = prev.map(msg => {
                  if (msg.id !== tempAssistantId) return msg;
                  let updated = { ...msg };
                  
                  if (eventType === "sources") updated.sources = (data as any).sources;
                  else if (eventType === "token") updated.content = currentAnswer;
                  else if (eventType === "verification") updated.verification = { status: (data as any).status, reason: (data as any).reason };
                  else if (eventType === "steps") updated.pipeline_steps = (data as any).steps;
                  else if (eventType === "done") updated.isStreaming = false;
                  else if (eventType === "error") Object.assign(updated, { isError: true, content: currentAnswer + `\n\n**Error:** ${(data as any).message}`, isStreaming: false });
                  
                  return updated;
                });
                
                if (eventType === "done" || eventType === "error") {
                  saveMessages(updatedMsgs, activeSessionId, false);
                }
                
                return updatedMsgs;
              });
            }
          }
        }
      }
    } catch (error: any) {
      setMessages(prev => {
        const msgs = prev.map(msg => msg.id === tempAssistantId ? { ...msg, isError: true, content: `**Error:** ${error.message}`, isStreaming: false } : msg);
        saveMessages(msgs, activeSessionId, false);
        return msgs;
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-surface-base font-sans overflow-hidden">
      <Sidebar 
        sessions={sessions} 
        activeSessionId={activeSessionId} 
        onSelect={(id) => loadSession(id, sessions)} 
        onNewChat={createNewSession}
        onDelete={handleDeleteSession}
      />

      {sidebarOpen && (
        <div className="md:hidden fixed inset-0 z-40 bg-black/20" onClick={() => setSidebarOpen(false)}>
          <div className="w-72 h-full bg-surface-lowest" onClick={e => e.stopPropagation()}>
            <Sidebar 
              sessions={sessions} 
              activeSessionId={activeSessionId} 
              onSelect={(id) => { loadSession(id, sessions); setSidebarOpen(false); }} 
              onNewChat={() => { createNewSession(); setSidebarOpen(false); }}
              onDelete={handleDeleteSession}
            />
          </div>
        </div>
      )}

      <main className="flex-1 flex flex-col h-screen relative w-full">
        <header className="flex items-center justify-between px-6 py-4 bg-surface-lowest backdrop-blur-xl bg-opacity-70 border-b border-surface-high sticky top-0 z-10 transition-colors">
          <div className="flex items-center gap-3">
            <button className="md:hidden p-2 -ml-2 rounded-md text-text-muted hover:bg-surface-low" onClick={() => setSidebarOpen(true)}>
              <Menu className="w-5 h-5" />
            </button>
            <div className="w-10 h-10 bg-gradient-to-br from-brand-900 to-brand-800 rounded-lg flex items-center justify-center shadow-inner">
              <Bot className="text-white w-6 h-6" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-text-main tracking-tight">Smart Retrieval RAG</h1>
              <p className="text-xs text-text-muted font-medium uppercase tracking-[0.05em] hidden sm:block">Higher Ed Assistant</p>
            </div>
          </div>
          <div className="flex items-center gap-2 hidden md:flex">
            <Link href="/analytics" className="text-text-muted hover:text-accent-500 transition-colors p-2 rounded-lg hover:bg-surface-low" title="Analytics Dashboard">
              <BarChart className="w-5 h-5" />
            </Link>
            <Link href="/upload" className="text-text-muted hover:text-accent-500 transition-colors p-2 rounded-lg hover:bg-surface-low" title="Document Management">
              <Settings className="w-5 h-5" />
            </Link>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-8" ref={scrollRef}>
          <div className="max-w-4xl mx-auto space-y-8 pb-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
          </div>
        </div>

        <div className="bg-surface-lowest border-t border-surface-high p-4">
          <div className="max-w-4xl mx-auto relative">
            <form
              onSubmit={handleSubmit}
              className="flex items-end gap-3 bg-surface-lowest p-2 rounded-[24px] border border-surface-high shadow-[0_4px_20px_rgba(9,20,38,0.04)] focus-within:ring-2 focus-within:ring-accent-500 transition-shadow"
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
                placeholder="Ask about AICTE norms, educational policies, or university guidelines..."
                className="flex-1 max-h-48 min-h-[52px] resize-none bg-transparent px-4 py-3 outline-none text-text-main placeholder:text-text-muted"
                rows={1}
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="mb-1 mr-1 p-3 rounded-[16px] bg-gradient-to-br from-brand-900 to-brand-800 text-white hover:opacity-90 disabled:opacity-50 transition-all flex flex-shrink-0 items-center justify-center"
              >
                <Send className="w-5 h-5" />
              </button>
            </form>
            <p className="text-center text-xs text-text-muted mt-3 font-medium tracking-wide">
              AI CAN MAKE MISTAKES. VERIFY CRITICAL FACTS WITH OFFICIAL SOURCES.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}


