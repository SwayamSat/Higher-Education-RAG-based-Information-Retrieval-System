import React from 'react';
import { CheckCircle2, XCircle, Info } from 'lucide-react';

export type BadgeType = "confidence" | "verification";
export type BadgeVariant = "success" | "warning" | "error" | "neutral";

interface BadgeProps {
  type: BadgeType;
  variant: BadgeVariant;
  label: string;
  tooltip?: string;
}

export function Badge({ type, variant, label, tooltip }: BadgeProps) {
  const baseClasses = "group relative px-2.5 py-1 rounded-md text-xs font-semibold border flex items-center gap-1.5 cursor-help shadow-sm transition-colors";
  
  const variantStyles = {
    success: "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100",
    warning: "bg-yellow-50 text-yellow-700 border-yellow-200 hover:bg-yellow-100",
    error: "bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100",
    neutral: "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100",
  };

  const getIcon = () => {
    if (type === "confidence") {
      const dotColors = {
        success: "bg-green-500",
        warning: "bg-yellow-500",
        error: "bg-red-500",
        neutral: "bg-gray-500",
      };
      const pingColors = {
        success: "bg-green-400",
        warning: "bg-yellow-400",
        error: "bg-red-400",
        neutral: "bg-gray-400",
      };
      
      return (
        <span className="relative flex h-2 w-2">
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${pingColors[variant]}`}></span>
          <span className={`relative inline-flex rounded-full h-2 w-2 ${dotColors[variant]}`}></span>
        </span>
      );
    }
    
    // Verification icons
    if (variant === "success") return <CheckCircle2 className="w-3.5 h-3.5" />;
    if (variant === "error") return <XCircle className="w-3.5 h-3.5" />;
    return <Info className="w-3.5 h-3.5" />;
  };

  return (
    <div className={`${baseClasses} ${variantStyles[variant]}`}>
      {getIcon()}
      {label}
      
      {tooltip && (
        <div className="absolute opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity bg-brand-900 text-white text-[11px] rounded py-1 px-2 right-0 bottom-full mb-1 w-48 text-right z-20 shadow-xl font-normal leading-tight">
          {tooltip}
        </div>
      )}
    </div>
  );
}
