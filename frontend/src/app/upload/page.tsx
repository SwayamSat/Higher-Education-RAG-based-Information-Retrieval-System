"use client";

import React, { useState, useEffect } from 'react';
import { FileUpload } from '../../components/FileUpload';
import { FileText, Trash2, ArrowLeft, RefreshCw } from 'lucide-react';
import Link from 'next/link';

export default function UploadPage() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isReindexing, setIsReindexing] = useState(false);

  const fetchDocuments = async () => {
    try {
      const res = await fetch("http://localhost:8000/documents");
      const data = await res.json();
      setDocuments(data.items || []);
    } catch (e) {
      console.error("Failed to fetch documents", e);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleUpload = async (file: File, department: string) => {
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("department", department);
      
      const res = await fetch("http://localhost:8000/documents/upload", {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        await fetchDocuments();
      } else {
        alert("Upload failed.");
      }
    } catch (e) {
      console.error(e);
      alert("Upload failed.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this document from the index?")) return;
    try {
      const res = await fetch(`http://localhost:8000/documents/${id}`, { method: "DELETE" });
      if (res.ok) {
        await fetchDocuments();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleReindex = async () => {
    setIsReindexing(true);
    try {
      await fetch("http://localhost:8000/documents/reindex", { method: "POST" });
      alert("Re-indexing started in background. Documents will be updated soon.");
    } catch (e) {
      console.error(e);
    } finally {
      setIsReindexing(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface-base font-sans p-6 md:p-12">
      <div className="max-w-4xl mx-auto space-y-8">
        
        <div className="flex items-center justify-between">
          <div>
            <Link href="/" className="inline-flex items-center gap-2 text-text-muted hover:text-accent-500 transition-colors mb-4 text-sm font-semibold">
              <ArrowLeft className="w-4 h-4" /> Back to Chat
            </Link>
            <h1 className="text-3xl font-bold text-text-main tracking-tight">Document Management</h1>
            <p className="text-text-muted mt-2">Upload AICTE norms, UGC guidelines, and educational policies to the knowledge base.</p>
          </div>
          <button 
            onClick={handleReindex}
            disabled={isReindexing}
            className="flex items-center gap-2 px-4 py-2 bg-surface-lowest text-text-main border border-surface-high rounded-[16px] shadow-sm hover:border-accent-400 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isReindexing ? "animate-spin" : ""}`} />
            <span className="text-sm font-semibold">Full Re-index</span>
          </button>
        </div>

        <div className="bg-surface-lowest p-8 rounded-[24px] border border-surface-high shadow-[0_4px_20px_rgba(9,20,38,0.04)]">
          <FileUpload onUpload={handleUpload} isUploading={isUploading} />
        </div>

        <div className="bg-surface-lowest rounded-[24px] border border-surface-high shadow-[0_4px_20px_rgba(9,20,38,0.04)] overflow-hidden">
          <div className="p-6 border-b border-surface-high">
            <h2 className="text-xl font-bold text-text-main">Indexed Documents</h2>
          </div>
          
          <div className="divide-y divide-surface-high">
            {documents.length === 0 ? (
              <p className="p-8 text-center text-text-muted italic">No documents indexed yet.</p>
            ) : (
              documents.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-4 hover:bg-surface-low transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-brand-50 flex items-center justify-center">
                      <FileText className="w-5 h-5 text-brand-900" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-text-main">{doc.filename}</h3>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-xs bg-surface-base border border-surface-high px-2 py-0.5 rounded text-text-muted">
                          {doc.department}
                        </span>
                        <span className="text-[10px] text-text-muted font-mono">
                          ID: {doc.id.substring(0, 8)}...
                        </span>
                        <span className="text-[10px] text-text-muted font-mono">
                          {new Date(doc.upload_date).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  <button 
                    onClick={() => handleDelete(doc.id)}
                    className="p-2 text-text-muted hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                    title="Delete document"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
