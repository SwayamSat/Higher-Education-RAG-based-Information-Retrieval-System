import React from 'react';
import { Search, Edit3, CheckCircle, RefreshCcw } from 'lucide-react';

export interface PipelineStepData {
  agentName: "Router" | "Retrieval" | "Generator" | "Fact-Check" | "Correction";
  durationMs: number;
  status: "success" | "warning" | "error";
  iteration?: number;
}

export function PipelineStep({ data }: { data: PipelineStepData }) {
  const getIcon = () => {
    switch (data.agentName) {
      case "Retrieval": return <Search className="w-4 h-4" />;
      case "Generator": return <Edit3 className="w-4 h-4" />;
      case "Fact-Check": return <CheckCircle className="w-4 h-4" />;
      case "Correction": return <RefreshCcw className="w-4 h-4" />;
      default: return <span className="w-4 h-4 flex items-center justify-center font-bold">R</span>;
    }
  };

  const getStatusColor = () => {
    switch (data.status) {
      case "success": return "bg-green-500";
      case "warning": return "bg-yellow-500";
      case "error": return "bg-red-500";
      default: return "bg-gray-500";
    }
  };

  return (
    <div className="flex flex-col items-center gap-2 min-w-[100px]">
      <div className="w-10 h-10 rounded-[16px] bg-surface-lowest border border-surface-high shadow-sm flex items-center justify-center text-text-muted relative">
        {getIcon()}
        <div className={`absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-surface-lowest ${getStatusColor()}`} />
      </div>
      <div className="text-center">
        <p className="text-xs font-semibold text-text-main">{data.agentName}</p>
        <p className="text-[10px] text-text-muted font-mono">{data.durationMs}ms</p>
      </div>
      {data.iteration && (
        <span className="text-[9px] uppercase tracking-wider bg-surface-high text-text-muted px-1.5 py-0.5 rounded-sm">
          Loop {data.iteration}
        </span>
      )}
    </div>
  );
}
