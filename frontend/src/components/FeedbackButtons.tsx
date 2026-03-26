import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown } from 'lucide-react';

interface FeedbackButtonsProps {
  onFeedback: (isPositive: boolean) => void;
}

export function FeedbackButtons({ onFeedback }: FeedbackButtonsProps) {
  const [submitted, setSubmitted] = useState<boolean | null>(null);

  const handleVote = (isPositive: boolean) => {
    if (submitted !== null) return;
    setSubmitted(isPositive);
    onFeedback(isPositive);
  };

  return (
    <div className="flex items-center gap-1">
      <button 
        onClick={() => handleVote(true)}
        disabled={submitted !== null}
        className={`p-1.5 rounded-md transition-colors ${
          submitted === true 
            ? "text-emerald-600 bg-emerald-50" 
            : "text-text-muted hover:text-text-main hover:bg-surface-low disabled:opacity-50"
        }`}
        title="Good response"
      >
        <ThumbsUp className={`w-4 h-4 ${submitted === true ? "fill-current" : ""}`} />
      </button>
      <button 
        onClick={() => handleVote(false)}
        disabled={submitted !== null}
        className={`p-1.5 rounded-md transition-colors ${
          submitted === false 
            ? "text-rose-600 bg-rose-50" 
            : "text-text-muted hover:text-text-main hover:bg-surface-low disabled:opacity-50"
        }`}
        title="Bad response"
      >
        <ThumbsDown className={`w-4 h-4 ${submitted === false ? "fill-current" : ""}`} />
      </button>
      {submitted !== null && (
        <span className="text-[10px] uppercase font-semibold text-text-muted ml-2 tracking-wider animate-in fade-in">
          Thanks!
        </span>
      )}
    </div>
  );
}
