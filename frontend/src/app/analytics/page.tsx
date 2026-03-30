"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { ArrowLeft, Activity, Clock, CheckCircle, BarChart3, ThumbsUp } from 'lucide-react';

export default function AnalyticsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/analytics")
      .then(res => res.json())
      .then(json => {
        setData(json);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load analytics", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-surface-base font-sans p-6 md:p-12 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-brand-900"></div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-surface-base font-sans p-6 md:p-12 space-y-8 max-w-5xl mx-auto">
        <Link href="/" className="inline-flex items-center gap-2 text-text-muted hover:text-accent-500 mb-4 text-sm font-semibold">
          <ArrowLeft className="w-4 h-4" /> Back to Chat
        </Link>
        <h1 className="text-3xl font-bold text-text-main tracking-tight">System Analytics</h1>
        <div className="bg-surface-lowest p-8 rounded-[24px] border border-surface-high shadow-sm text-center">
          <p className="text-text-muted italic">No data available. Send some queries first.</p>
        </div>
      </div>
    );
  }

  const { total_queries, average_latencies, verification_rates, feedback_summary, note } = data;
  const hasLiveLatency = average_latencies.retrieval_ms > 0 || average_latencies.generation_ms > 0;

  return (
    <div className="min-h-screen bg-surface-base font-sans p-6 md:p-12">
      <div className="max-w-5xl mx-auto space-y-8">

        <div>
          <Link href="/" className="inline-flex items-center gap-2 text-text-muted hover:text-accent-500 transition-colors mb-4 text-sm font-semibold">
            <ArrowLeft className="w-4 h-4" /> Back to Chat
          </Link>
          <h1 className="text-3xl font-bold text-text-main tracking-tight">System Analytics</h1>
          <p className="text-text-muted mt-2">Performance and quality metrics for the RAG pipeline.</p>
        </div>

        {/* Server-restart notice banner */}
        {note && (
          <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 text-amber-800 rounded-[16px] px-5 py-4 text-sm">
            <span className="text-base">⚠️</span>
            <span>{note} Send a new query to start collecting live latency metrics.</span>
          </div>
        )}

        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-surface-lowest p-6 rounded-[24px] border border-surface-high shadow-[0_4px_20px_rgba(9,20,38,0.04)]">
            <div className="flex items-center gap-3 text-text-muted mb-2">
              <Activity className="w-4 h-4" />
              <h3 className="text-xs font-semibold uppercase tracking-wider">Total Queries</h3>
            </div>
            <p className="text-4xl font-bold text-text-main">{total_queries}</p>
            {note && <p className="text-[10px] text-amber-600 mt-1 font-medium">Based on feedback count</p>}
          </div>

          <div className="bg-surface-lowest p-6 rounded-[24px] border border-surface-high shadow-[0_4px_20px_rgba(9,20,38,0.04)]">
            <div className="flex items-center gap-3 text-emerald-600 mb-2">
              <CheckCircle className="w-4 h-4" />
              <h3 className="text-xs font-semibold uppercase tracking-wider">Final Pass Rate</h3>
            </div>
            <p className="text-4xl font-bold text-emerald-700">
              {hasLiveLatency ? `${verification_rates.final_verified_percentage}%` : '—'}
            </p>
            <p className="text-xs text-text-muted mt-1">
              {hasLiveLatency ? `First pass: ${verification_rates.first_pass_verified_percentage}%` : 'Awaiting live data'}
            </p>
          </div>

          <div className="bg-surface-lowest p-6 rounded-[24px] border border-surface-high shadow-[0_4px_20px_rgba(9,20,38,0.04)]">
            <div className="flex items-center gap-3 text-accent-600 mb-2">
              <Clock className="w-4 h-4" />
              <h3 className="text-xs font-semibold uppercase tracking-wider">Avg Latency</h3>
            </div>
            <p className="text-4xl font-bold text-accent-700">
              {hasLiveLatency
                ? `${Math.round(average_latencies.retrieval_ms + average_latencies.generation_ms + average_latencies.verification_ms)}ms`
                : '—'}
            </p>
            {!hasLiveLatency && <p className="text-xs text-text-muted mt-1">Awaiting live data</p>}
          </div>

          <div className="bg-surface-lowest p-6 rounded-[24px] border border-surface-high shadow-[0_4px_20px_rgba(9,20,38,0.04)]">
            <div className="flex items-center gap-3 text-brand-600 mb-2">
              <ThumbsUp className="w-4 h-4" />
              <h3 className="text-xs font-semibold uppercase tracking-wider">Positive Feedback</h3>
            </div>
            <p className="text-4xl font-bold text-brand-700">{feedback_summary.positive_percentage}%</p>
            <p className="text-xs text-text-muted mt-1">{feedback_summary.total_feedback} total ratings</p>
          </div>
        </div>

        {/* Detailed Latency Breakdown */}
        <div className="bg-surface-lowest p-8 rounded-[24px] border border-surface-high shadow-[0_4px_20px_rgba(9,20,38,0.04)]">
          <div className="flex items-center gap-3 mb-6">
            <BarChart3 className="w-5 h-5 text-text-main" />
            <h2 className="text-xl font-bold text-text-main">Average Latency Breakdown</h2>
          </div>

          {!hasLiveLatency ? (
            <p className="text-text-muted italic text-sm text-center py-4">
              Latency data resets when the server restarts. Send a query to populate this section.
            </p>
          ) : (
            <div className="space-y-4">
              {[
                { label: "Retrieval", value: average_latencies.retrieval_ms, color: "bg-blue-500" },
                { label: "Generation", value: average_latencies.generation_ms, color: "bg-purple-500" },
                { label: "Verification", value: average_latencies.verification_ms, color: "bg-emerald-500" },
                { label: "Self-Correction (if needed)", value: average_latencies.correction_ms, color: "bg-orange-500" },
              ].map((item, idx) => {
                const total = Math.max(1, average_latencies.retrieval_ms + average_latencies.generation_ms + average_latencies.verification_ms + average_latencies.correction_ms);
                const percentage = Math.round((item.value / total) * 100);
                return (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between text-sm font-semibold">
                      <span className="text-text-main">{item.label}</span>
                      <span className="text-text-muted font-mono">{item.value}ms</span>
                    </div>
                    <div className="w-full bg-surface-low rounded-full h-2.5 overflow-hidden">
                      <div className={`h-2.5 rounded-full ${item.color}`} style={{ width: `${percentage}%` }}></div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
