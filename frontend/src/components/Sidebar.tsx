import React from 'react';
import { MessageSquarePlus, MessageSquare, Trash2 } from 'lucide-react';

export interface ChatSession {
  id: string;
  title: string;
  updatedAt: string;
}

interface SidebarProps {
  sessions: ChatSession[];
  activeSessionId?: string;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDelete: (id: string, e: React.MouseEvent) => void;
}

export function Sidebar({ sessions, activeSessionId, onSelect, onNewChat, onDelete }: SidebarProps) {
  return (
    <aside className="w-72 bg-surface-low border-r border-surface-high flex flex-col h-full bg-opacity-50 hidden md:flex">
      <div className="p-4">
        <button 
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-surface-lowest border border-surface-high rounded-[16px] shadow-[0_4px_20px_rgba(9,20,38,0.04)] hover:border-accent-400 hover:text-accent-500 transition-colors text-sm font-semibold text-text-main"
        >
          <MessageSquarePlus className="w-4 h-4" />
          New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 pb-4">
        <p className="px-3 text-xs font-semibold text-text-muted uppercase tracking-wider mb-2 mt-4">Recent Sessions</p>
        <div className="space-y-1">
          {sessions.length === 0 ? (
            <p className="px-3 text-sm text-text-muted italic py-4">No recent chats</p>
          ) : (
            sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => onSelect(session.id)}
                className={`w-full text-left group flex items-center justify-between px-3 py-2.5 rounded-[12px] transition-colors ${
                  activeSessionId === session.id 
                    ? "bg-surface-lowest border border-surface-high shadow-sm" 
                    : "hover:bg-surface-high border border-transparent"
                }`}
              >
                <div className="flex items-center gap-3 overflow-hidden">
                  <MessageSquare className={`w-4 h-4 shrink-0 ${activeSessionId === session.id ? "text-accent-500" : "text-text-muted"}`} />
                  <div className="overflow-hidden">
                    <p className={`text-sm truncate ${activeSessionId === session.id ? "font-semibold text-text-main" : "text-text-muted group-hover:text-text-main"}`}>
                      {session.title}
                    </p>
                    <p className="text-[10px] text-text-muted font-mono mt-0.5">
                      {new Date(session.updatedAt).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div 
                  className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-rose-100 hover:text-rose-600 rounded-md transition-colors shrink-0"
                  onClick={(e) => onDelete(session.id, e)}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </div>
              </button>
            ))
          )}
        </div>
      </div>
    </aside>
  );
}
