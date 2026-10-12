"use client";

import React, { useState } from "react";
import { CheckCircle2, AlertTriangle, HelpCircle, Info, ChevronDown, ChevronUp } from "lucide-react";
import { MatchAnalysis, RequirementMatch, MissingRequirement } from "@/types/api";

interface MatchAnalysisCardProps {
  analysis: MatchAnalysis;
}

export function MatchAnalysisCard({ analysis }: MatchAnalysisCardProps) {
  const [filter, setFilter] = useState<"all" | "explicit" | "partial" | "missing">("all");
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const score = analysis.estimated_score;
  const scoreColor =
    score >= 75
      ? "text-emerald-700 bg-emerald-50 border-emerald-200"
      : score >= 50
      ? "text-blue-700 bg-blue-50 border-blue-200"
      : "text-amber-700 bg-amber-50 border-amber-200";

  const scoreBarColor =
    score >= 75 ? "bg-emerald-500" : score >= 50 ? "bg-blue-500" : "bg-amber-500";

  const explicitMatches = analysis.breakdown.filter((r) => r.status === "explicitly_supported");
  const partialMatches = analysis.breakdown.filter((r) => r.status === "partially_supported");
  const missingReqs = analysis.missing_requirements || [];

  const toggleExpand = (idx: number) => {
    setExpandedIndex(expandedIndex === idx ? null : idx);
  };

  const filteredMatches = analysis.breakdown.filter((r) => {
    if (filter === "explicit") return r.status === "explicitly_supported";
    if (filter === "partial") return r.status === "partially_supported";
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Top Match Score Banner */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-5 border-b border-slate-100">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Estimated Job Match Score
            </span>
            <div className="flex items-baseline space-x-3 mt-1">
              <span className="text-4xl font-extrabold text-slate-900 tracking-tight">
                {score}%
              </span>
              <span className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${scoreColor}`}>
                {score >= 75 ? "Strong Evidence Alignment" : score >= 50 ? "Moderate Match" : "Growth Opportunity"}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <div className="text-center px-3 py-2 bg-slate-50 rounded-lg border border-slate-150">
              <div className="font-bold text-slate-800 text-sm">{explicitMatches.length}</div>
              <div className="text-slate-500">Supported</div>
            </div>
            <div className="text-center px-3 py-2 bg-slate-50 rounded-lg border border-slate-150">
              <div className="font-bold text-slate-800 text-sm">{partialMatches.length}</div>
              <div className="text-slate-500">Partial</div>
            </div>
            <div className="text-center px-3 py-2 bg-slate-50 rounded-lg border border-slate-150">
              <div className="font-bold text-slate-800 text-sm">{missingReqs.length}</div>
              <div className="text-slate-500">Unmentioned</div>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
            <div
              className={`h-2.5 rounded-full transition-all duration-500 ${scoreBarColor}`}
              style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
              role="progressbar"
              aria-valuenow={score}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>
        </div>

        {/* Scoring Methodology & Disclaimer */}
        <div className="mt-4 pt-3 text-xs text-slate-500 space-y-1.5">
          <p className="flex items-start space-x-1.5">
            <Info className="h-3.5 w-3.5 mt-0.5 text-indigo-500 shrink-0" />
            <span>
              <strong className="text-slate-700">Methodology:</strong> {analysis.scoring_methodology}
            </span>
          </p>
          <p className="text-[11px] text-slate-400 italic pl-5">
            {analysis.disclaimer}
          </p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-200 pb-2">
        <button
          type="button"
          onClick={() => setFilter("all")}
          className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
            filter === "all" ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          All Requirements ({analysis.breakdown.length})
        </button>
        <button
          type="button"
          onClick={() => setFilter("explicit")}
          className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
            filter === "explicit" ? "bg-emerald-600 text-white" : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          Fully Supported ({explicitMatches.length})
        </button>
        <button
          type="button"
          onClick={() => setFilter("partial")}
          className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
            filter === "partial" ? "bg-blue-600 text-white" : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          Partially Supported ({partialMatches.length})
        </button>
        <button
          type="button"
          onClick={() => setFilter("missing")}
          className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
            filter === "missing" ? "bg-amber-600 text-white" : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          Not Mentioned ({missingReqs.length})
        </button>
      </div>

      {/* Requirement Matches Breakdown */}
      {filter !== "missing" && (
        <div className="space-y-3">
          <h4 className="text-sm font-bold text-slate-900">Evaluated Job Requirements</h4>
          {filteredMatches.length === 0 ? (
            <p className="text-xs text-slate-500 p-4 bg-white rounded-lg border border-slate-200">
              No requirements match the current filter.
            </p>
          ) : (
            filteredMatches.map((req: RequirementMatch, idx: number) => {
              const isExpanded = expandedIndex === idx;
              return (
                <div
                  key={idx}
                  className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs transition-all hover:border-slate-300"
                >
                  <div className="flex items-start justify-between gap-3 cursor-pointer" onClick={() => toggleExpand(idx)}>
                    <div className="flex items-start space-x-2.5 flex-1">
                      {req.status === "explicitly_supported" ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-600 mt-0.5 shrink-0" />
                      ) : (
                        <HelpCircle className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" />
                      )}
                      <div>
                        <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                          <span className="text-sm font-semibold text-slate-900">
                            {req.requirement}
                          </span>
                          <span
                            className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                              req.importance === "required"
                                ? "bg-purple-50 text-purple-700 border border-purple-200"
                                : "bg-slate-100 text-slate-600"
                            }`}
                          >
                            {req.importance}
                          </span>
                          <span
                            className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                              req.status === "explicitly_supported"
                                ? "bg-emerald-50 text-emerald-700"
                                : "bg-blue-50 text-blue-700"
                            }`}
                          >
                            {req.status === "explicitly_supported" ? "Explicit Evidence" : "Partial Evidence"}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 mt-1">{req.notes}</p>
                      </div>
                    </div>

                    <button
                      type="button"
                      className="p-1 text-slate-400 hover:text-slate-600 rounded transition-colors"
                      aria-label={isExpanded ? "Collapse requirement details" : "Expand requirement details"}
                    >
                      {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </button>
                  </div>

                  {/* Expandable Evidence Quote */}
                  {isExpanded && req.evidence_quote && (
                    <div className="mt-3 pt-3 border-t border-slate-100 text-xs">
                      <span className="font-semibold text-slate-700 block mb-1">
                        Verbatim Evidence from Resume:
                      </span>
                      <blockquote className="bg-slate-50 border-l-2 border-indigo-400 p-2.5 rounded-r text-slate-700 italic">
                        &ldquo;{req.evidence_quote}&rdquo;
                      </blockquote>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Missing / Unmentioned Requirements Section */}
      {(filter === "all" || filter === "missing") && missingReqs.length > 0 && (
        <div className="space-y-3 pt-2">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <h4 className="text-sm font-bold text-slate-900">
              Requirements Not Mentioned in Original Resume ({missingReqs.length})
            </h4>
          </div>
          <p className="text-xs text-slate-500">
            These skills or qualifications were listed in the job description but not found in your resume. ResumeCraft does not fabricate unverified claims; review if you have genuine experience to add.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {missingReqs.map((miss: MissingRequirement, idx: number) => (
              <div
                key={idx}
                className="bg-amber-50/50 rounded-xl border border-amber-200 p-4 text-xs space-y-1.5 shadow-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-900">{miss.requirement}</span>
                  <span
                    className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                      miss.importance === "required"
                        ? "bg-amber-200/80 text-amber-900"
                        : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {miss.importance}
                  </span>
                </div>
                <p className="text-amber-800 leading-relaxed">{miss.guidance}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
