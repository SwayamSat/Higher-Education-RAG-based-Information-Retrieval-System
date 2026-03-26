import React, { useState } from 'react';
import { User, Bot } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { SourceCard } from './SourceCard';
import { Badge, BadgeVariant } from './Badge';
import { PipelineStep, PipelineStepData } from './PipelineStep';
import { FeedbackButtons } from './FeedbackButtons';

export type SourceDocument = {
  filename: string;
  department: string;
  page: number | null;
  relevance_score: number;
};

export type VerificationResult = {
  status: "Verified" | "Unverified" | "Partial" | "Blocked";
  reason: string;
};

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceDocument[];
  confidence?: "High" | "Medium" | "Low";
  verification?: VerificationResult;
  latency_ms?: Record<string, number>;
  pipeline_steps?: PipelineStepData[];
  isError?: boolean;
  isStreaming?: boolean;
};

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const [showSources, setShowSources] = useState(false);
  const [showPipeline, setShowPipeline] = useState(false);

  const getConfidenceVariant = (conf?: string): BadgeVariant => {
    if (conf === "High") return "success";
    if (conf === "Medium") return "warning";
    if (conf === "Low") return "error";
    return "neutral";
  };

  const getVerificationVariant = (status?: string): BadgeVariant => {
    if (status === "Verified") return "success";
    if (status === "Unverified" || status === "Blocked") return "error";
    if (status === "Partial") return "warning";
    return "neutral";
  };

  const handleFeedback = async (isPositive: boolean) => {
    try {
      await fetch("http://localhost:8000/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query_id: message.id, rating: isPositive ? 1 : 0 }),
      });
    } catch (e) {
      console.error("Failed to submit feedback", e);
    }
  };

  return (
    <div className={`flex gap-4 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center shadow-sm
        ${isUser ? "bg-brand-900" : "bg-gradient-to-br from-brand-900 to-brand-800"}`}
      >
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : (
          <Bot className="w-5 h-5 text-surface-lowest" />
        )}
      </div>

      <div
        className={`max-w-[85%] flex flex-col gap-3
        ${isUser ? "items-end" : "items-start"}`}
      >
        <div
          className={`px-6 py-4 rounded-[24px] shadow-[0_4px_20px_rgba(9,20,38,0.04)] ${isUser
              ? "bg-brand-800 text-white rounded-tr-sm"
              : message.isError
                ? "bg-rose-50 text-rose-900 border border-rose-200 rounded-tl-sm"
                : "bg-surface-lowest border border-surface-high rounded-tl-sm w-full"
            }`}
        >
          <div className={`prose prose-sm max-w-none ${isUser ? "text-white prose-invert" : "text-text-main"}`}>
            <ReactMarkdown>{message.content}</ReactMarkdown>
            {message.isStreaming && (
              <span className="inline-block w-2 h-4 bg-brand-500 animate-pulse ml-1 align-middle rounded-sm"></span>
            )}
          </div>
        </div>

        {!isUser && !message.isError && (
          <div className="w-full flex flex-col gap-3">
            <div className="flex justify-between items-start gap-4 w-full">
              <div className="flex-1">
                {message.sources && message.sources.length > 0 && (
                  <SourceCard 
                    sources={message.sources}
                    isExpanded={showSources}
                    onToggle={() => setShowSources(!showSources)}
                    latencyMs={message.latency_ms}
                  />
                )}
              </div>

              <div className="flex flex-col gap-2 shrink-0 items-end">
                {message.confidence && (
                  <Badge 
                    type="confidence"
                    variant={getConfidenceVariant(message.confidence)}
                    label={`${message.confidence} Confidence`}
                  />
                )}
                {message.verification && (
                  <Badge
                    type="verification"
                    variant={getVerificationVariant(message.verification.status)}
                    label={`${message.verification.status} Fact-Check`}
                    tooltip={message.verification.reason}
                  />
                )}
              </div>
            </div>

            {/* Actions Row */}
            {(!message.isStreaming && message.content.length > 0) && (
               <div className="flex items-center justify-between mt-2 pt-2 border-t border-surface-high/50 px-1">
                 <div className="flex items-center gap-3">
                   {message.pipeline_steps && message.pipeline_steps.length > 0 && (
                     <button 
                       onClick={() => setShowPipeline(!showPipeline)}
                       className="text-xs font-semibold text-text-muted hover:text-accent-500 transition-colors uppercase tracking-wider"
                     >
                       {showPipeline ? "Hide Pipeline" : "Show Pipeline"}
                     </button>
                   )}
                 </div>
                 <FeedbackButtons onFeedback={handleFeedback} />
               </div>
            )}
            
            {/* Pipeline Visualization */}
            {showPipeline && message.pipeline_steps && (
              <div className="w-full bg-surface-lowest border border-surface-high rounded-xl p-4 shadow-sm overflow-x-auto">
                <p className="text-xs font-semibold text-text-muted mb-4 uppercase tracking-wider">Agent Pipeline Execution</p>
                <div className="flex items-center gap-4">
                  {message.pipeline_steps.map((step, idx) => (
                    <React.Fragment key={idx}>
                      <PipelineStep data={step} />
                      {idx < message.pipeline_steps!.length - 1 && (
                        <div className="h-0.5 w-6 bg-surface-high shrink-0" />
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
