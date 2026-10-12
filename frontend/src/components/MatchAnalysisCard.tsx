"use client";

import React, { useState } from "react";
import {
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Info,
  ChevronDown,
  ChevronUp,
  Calculator,
  ShieldAlert,
} from "lucide-react";
import { MatchAnalysis, RequirementMatch, MissingRequirement } from "@/types/api";

interface MatchAnalysisCardProps {
  analysis: MatchAnalysis;
}

export function MatchAnalysisCard({ analysis }: MatchAnalysisCardProps) {
  const [filter, setFilter] = useState<"all" | "explicit" | "partial" | "missing">("all");
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [showFormulaModal, setShowFormulaModal] = useState(false);

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
      {/* 1. Top Match Score Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-5 border-b border-slate-100">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Estimated Evidence Match Score
              </span>
              <button
                type="button"
                onClick={() => setShowFormulaModal(!showFormulaModal)}
                className="text-[11px] font-medium text-indigo-600 hover:text-indigo-800 underline inline-flex items-center space-x-1"
                aria-label="View mathematical scoring formula"
              >
                <Calculator className="h-3 w-3" />
                <span>{showFormulaModal ? "Hide Formula" : "Formula Details"}</span>
              </button>
            </div>

            <div className="flex items-baseline space-x-3 mt-1.5">
              <span className="text-4xl font-extrabold text-slate-900 tracking-tight">
                {score}%
              </span>
              <span className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${scoreColor}`}>
                {score >= 75
                  ? "Strong Evidence Alignment"
                  : score >= 50
                  ? "Moderate Alignment"
                  : "Partial Evidence Match"}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs">
            <div className="text-center px-3 py-2 bg-emerald-50/60 rounded-lg border border-emerald-200 min-w-[70px]">
              <div className="font-bold text-emerald-800 text-sm">{explicitMatches.length}</div>
              <div className="text-emerald-700 text-[11px]">Supported</div>
            </div>
            <div className="text-center px-3 py-2 bg-blue-50/60 rounded-lg border border-blue-200 min-w-[70px]">
              <div className="font-bold text-blue-800 text-sm">{partialMatches.length}</div>
              <div className="text-blue-700 text-[11px]">Partial</div>
            </div>
            <div className="text-center px-3 py-2 bg-amber-50/60 rounded-lg border border-amber-200 min-w-[70px]">
              <div className="font-bold text-amber-800 text-sm">{missingReqs.length}</div>
              <div className="text-amber-700 text-[11px]">Unmentioned</div>
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

        {/* Formula Details Drawer (Collapsible) */}
        {showFormulaModal && (
          <div className="mt-4 p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-2">
            <div className="font-bold text-slate-800 flex items-center space-x-1.5">
              <Calculator className="h-4 w-4 text-indigo-600" />
              <span>Deterministic Heuristic Scoring Formula</span>
            </div>
            <div className="bg-white p-2.5 rounded border border-slate-200 font-mono text-[11px] text-slate-800">
              score = round( &Sigma;(status_weight &times; importance_multiplier) / &Sigma;(importance_multiplier) &times; 100 )
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] text-slate-600">
              <div>
                <strong className="text-slate-800">Status Weights:</strong>
                <ul className="list-disc list-inside mt-0.5 space-y-0.5">
                  <li>Explicitly Supported: 1.0 (Full evidence found)</li>
                  <li>Partially Supported: 0.5 (Ambiguous or related claim)</li>
                  <li>Not Mentioned: 0.0 (No resume evidence)</li>
                </ul>
              </div>
              <div>
                <strong className="text-slate-800">Importance Multipliers:</strong>
                <ul className="list-disc list-inside mt-0.5 space-y-0.5">
                  <li>Required Qualification: 1.5&times; weight</li>
                  <li>Preferred Qualification: 1.0&times; weight</li>
                  <li>Rounding: Standard Half-Up to nearest integer</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Scoring Methodology & Mandatory ATS Disclaimer */}
        <div className="mt-4 pt-3 text-xs text-slate-500 space-y-2">
          <p className="flex items-start space-x-1.5">
            <Info className="h-3.5 w-3.5 mt-0.5 text-indigo-500 shrink-0" />
            <span>
              <strong className="text-slate-700">Methodology:</strong> {analysis.scoring_methodology}
            </span>
          </p>

          <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-[11px] text-slate-600 flex items-start space-x-2">
            <ShieldAlert className="h-4 w-4 text-slate-400 shrink-0 mt-0.5" />
            <div>
              <strong className="text-slate-700">Important Disclaimer:</strong>{" "}
              {analysis.disclaimer}{" "}
              This score is a deterministic heuristic reflecting textual evidence in your uploaded
              resume against extracted requirements. It is not an official Applicant Tracking System
              score, does not represent recruiter decision algorithms, and cannot guarantee interview
              or hiring outcomes.
            </div>
          </div>
        </div>
      </div>

      {/* 2. Filter Navigation */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-2">
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
            filter === "explicit"
              ? "bg-emerald-600 text-white"
              : "text-slate-600 hover:bg-slate-100"
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

      {/* 3. Evaluated Job Requirements List */}
      {filter !== "missing" && (
        <div className="space-y-3">
          <h4 className="text-sm font-bold text-slate-900">
            Extracted Job Requirements &amp; Evidence ({filteredMatches.length})
          </h4>
          {filteredMatches.length === 0 ? (
            <p className="text-xs text-slate-500 p-4 bg-white rounded-lg border border-slate-200">
              No requirements match the current filter selection.
            </p>
          ) : (
            filteredMatches.map((req: RequirementMatch, idx: number) => {
              const isExpanded = expandedIndex === idx;
              return (
                <div
                  key={idx}
                  className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs transition-all hover:border-slate-300"
                >
                  <div
                    className="flex items-start justify-between gap-3 cursor-pointer"
                    onClick={() => toggleExpand(idx)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        toggleExpand(idx);
                      }
                    }}
                    aria-expanded={isExpanded}
                  >
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
                            {req.importance} (
                            {req.importance === "required" ? "1.5×" : "1.0×"})
                          </span>
                          <span
                            className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                              req.status === "explicitly_supported"
                                ? "bg-emerald-50 text-emerald-700"
                                : "bg-blue-50 text-blue-700"
                            }`}
                          >
                            {req.status === "explicitly_supported"
                              ? "Explicit Evidence (1.0 wt)"
                              : "Partial Evidence (0.5 wt)"}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 mt-1">{req.notes}</p>
                      </div>
                    </div>

                    <button
                      type="button"
                      className="p-1 text-slate-400 hover:text-slate-600 rounded transition-colors"
                      aria-label={
                        isExpanded
                          ? "Collapse requirement details"
                          : "Expand requirement details"
                      }
                    >
                      {isExpanded ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </button>
                  </div>

                  {/* Expandable Evidence Quote */}
                  {isExpanded && (
                    <div className="mt-3 pt-3 border-t border-slate-100 text-xs space-y-1.5">
                      <span className="font-semibold text-slate-700 block">
                        Verbatim Evidence from Source Resume:
                      </span>
                      {req.evidence_quote ? (
                        <blockquote className="bg-slate-50 border-l-2 border-indigo-400 p-2.5 rounded-r text-slate-700 italic">
                          &ldquo;{req.evidence_quote}&rdquo;
                        </blockquote>
                      ) : (
                        <p className="text-slate-500 italic text-[11px]">
                          Inferred from related qualifications or context; no exact verbatim quote captured.
                        </p>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      {/* 4. Missing / Unmentioned Requirements Section */}
      {(filter === "all" || filter === "missing") && missingReqs.length > 0 && (
        <div className="space-y-3 pt-2">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <h4 className="text-sm font-bold text-slate-900">
              Requirements Not Mentioned in Source Resume ({missingReqs.length})
            </h4>
          </div>
          <p className="text-xs text-slate-500">
            These qualifications were specified in the job description but not evidenced in your
            uploaded resume. To protect candidate credibility, ResumeCraft strictly refuses to
            invent or inject ungrounded claims.
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
                    {miss.importance} (0.0 wt)
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
