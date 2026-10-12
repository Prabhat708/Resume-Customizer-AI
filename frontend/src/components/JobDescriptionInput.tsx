"use client";

import React from "react";
import { FileText, AlertCircle } from "lucide-react";

interface JobDescriptionInputProps {
  value: string;
  onChange: (val: string) => void;
  error?: string | null;
  disabled?: boolean;
}

const MIN_CHAR_RECOMMENDED = 50;

export function JobDescriptionInput({
  value,
  onChange,
  error,
  disabled = false,
}: JobDescriptionInputProps) {
  const charCount = value.length;
  const wordCount = value.trim() ? value.trim().split(/\s+/).length : 0;
  const isTooShort = charCount > 0 && charCount < MIN_CHAR_RECOMMENDED;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <label
          htmlFor="job-description-input"
          className="text-sm font-semibold text-slate-900 flex items-center space-x-2"
        >
          <span className="flex items-center justify-center w-5 h-5 rounded-full bg-indigo-50 text-indigo-700 text-xs font-bold mr-1">
            1
          </span>
          <FileText className="h-4 w-4 text-indigo-600 inline mr-1" />
          <span>Target Job Description</span>
        </label>
        <div className="flex items-center space-x-2 text-xs text-slate-500 font-mono">
          <span>{wordCount} words</span>
          <span>•</span>
          <span className={isTooShort ? "text-amber-600 font-medium" : ""}>
            {charCount} chars
          </span>
        </div>
      </div>

      <p className="text-xs text-slate-500 mb-3">
        Paste the target job description or requirements below. The customizer extracts mandatory and preferred qualifications for evidence matching.
      </p>

      <div className="relative flex-1 flex flex-col min-h-[220px]">
        <textarea
          id="job-description-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          placeholder="Paste full job description here (role summary, required technical qualifications, preferred experience, responsibilities)..."
          rows={10}
          className={`w-full flex-1 p-3.5 text-sm rounded-lg border bg-slate-50/50 text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:ring-2 focus:bg-white transition-all resize-y font-sans ${
            error
              ? "border-red-300 focus:ring-red-400"
              : isTooShort
              ? "border-amber-300 focus:ring-amber-400"
              : "border-slate-200 focus:ring-indigo-500 focus:border-indigo-500"
          }`}
          aria-invalid={Boolean(error || isTooShort)}
          aria-describedby={error ? "jd-error" : isTooShort ? "jd-warning" : undefined}
        />
      </div>

      {/* Inline Validation Messages */}
      {error && (
        <div id="jd-error" className="mt-2.5 flex items-start text-xs text-red-600 space-x-1.5" role="alert">
          <AlertCircle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {!error && isTooShort && (
        <div id="jd-warning" className="mt-2.5 flex items-start text-xs text-amber-600 space-x-1.5">
          <AlertCircle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
          <span>Job description is very short ({charCount}/50 chars). Providing full responsibilities and qualifications improves match accuracy.</span>
        </div>
      )}
    </div>
  );
}
