import React, { useCallback, useState } from 'react';
import { UploadCloud, File, AlertCircle } from 'lucide-react';

interface FileUploadProps {
  onUpload: (file: File, department: string) => Promise<void>;
  isUploading: boolean;
}

export function FileUpload({ onUpload, isUploading }: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [department, setDepartment] = useState("General");
  const [error, setError] = useState("");

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    setError("");

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type !== "application/pdf") {
        setError("Only PDF files are supported.");
        return;
      }
      await onUpload(file, department);
    }
  }, [onUpload, department]);

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    setError("");
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.type !== "application/pdf") {
        setError("Only PDF files are supported.");
        return;
      }
      await onUpload(file, department);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      <div className="flex items-center gap-4">
        <label className="text-sm font-semibold text-text-main">Target Department:</label>
        <select 
          value={department} 
          onChange={(e) => setDepartment(e.target.value)}
          className="bg-surface-lowest border border-surface-high rounded-md px-3 py-1.5 text-sm w-48 focus:ring-2 focus:ring-accent-500 outline-none transition-shadow"
          disabled={isUploading}
        >
          <option value="General">General</option>
          <option value="AICTE">AICTE</option>
          <option value="UGC">UGC</option>
          <option value="University">University</option>
        </select>
      </div>

      <div 
        className={`relative border-2 border-dashed rounded-[24px] p-12 text-center transition-all flex flex-col items-center justify-center min-h-[240px]
          ${dragActive ? "border-accent-500 bg-brand-50 bg-opacity-50" : "border-surface-high bg-surface-lowest hover:border-accent-400"}
          ${isUploading ? "opacity-50 pointer-events-none" : ""}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input 
          type="file" 
          accept=".pdf" 
          onChange={handleChange} 
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
          disabled={isUploading}
        />
        
        {isUploading ? (
          <div className="flex flex-col items-center gap-3">
            <UploadCloud className="w-12 h-12 text-accent-500 animate-bounce" />
            <p className="text-lg font-semibold text-text-main">Uploading & Indexing...</p>
            <p className="text-sm text-text-muted">This might take a moment.</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div className="w-16 h-16 rounded-full bg-surface-low flex items-center justify-center mb-2 shadow-sm">
              <File className="w-8 h-8 text-brand-900" />
            </div>
            <p className="text-lg font-semibold text-text-main">Drag & Drop PDF here</p>
            <p className="text-sm text-text-muted">or click to browse files</p>
          </div>
        )}
      </div>
      
      {error && (
        <div className="flex items-center gap-2 text-rose-600 bg-rose-50 px-4 py-3 rounded-lg text-sm font-medium border border-rose-200">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}
    </div>
  );
}
