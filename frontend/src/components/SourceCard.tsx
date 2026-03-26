import React from 'react';
import { FileText } from 'lucide-react';

interface SourceDocument {
  filename: string;
  department: string;
  page: number | null;
  relevance_score: number;
}

interface SourceCardProps {
  sources: SourceDocument[];
  isExpanded: boolean;
  onToggle: () => void;
  latencyMs?: Record<string, number>;
}

export function SourceCard({ sources, isExpanded, onToggle, latencyMs }: SourceCardProps) {
  return (
    <div className="bg-surface-lowest border border-surface-high rounded-xl overflow-hidden w-full max-w-lg shadow-[0_4px_20px_rgba(9,20,38,0.04)] transition-all">
      <button
        onClick={onToggle}
        className="w-full px-4 py-2.5 flex items-center justify-between hover:bg-surface-base transition-colors"
      >
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-accent-500" />
          <span className="text-sm font-semibold text-text-main">
            {sources.length} Sources
          </span>
        </div>
        <span className="text-xs font-medium text-text-muted uppercase tracking-wider">
          {isExpanded ? "Hide" : "Expand"}
        </span>
      </button>

      {isExpanded && (
        <div className="px-4 pb-3 pt-1 border-t border-surface-high space-y-2 bg-surface-lowest">
          {sources.length === 0 ? (
            <p className="text-xs text-text-muted italic py-2">No sources matched the query.</p>
          ) : (
            sources.map((src, i) => (
              <div key={i} className="flex justify-between items-start text-xs p-2 rounded-md bg-surface-low border border-surface-high">
                <div className="flex gap-2">
                  <span className="font-mono bg-surface-base text-text-main px-1.5 py-0.5 rounded border border-surface-high">{src.department}</span>
                  <span className="font-medium text-text-main truncate max-w-[200px]" title={src.filename}>{src.filename}</span>
                </div>
                {src.page && <span className="text-text-muted whitespace-nowrap">p. {src.page}</span>}
              </div>
            ))
          )}

          {/* Timing Data */}
          {latencyMs && (
            <div className="flex gap-4 mt-3 pt-2 border-t border-dashed border-surface-high text-[10px] text-text-muted font-mono">
              <span>Ret: {latencyMs.retrieval}ms</span>
              <span>Gen: {latencyMs.generation}ms</span>
              <span>Chk: {latencyMs.verification}ms</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
