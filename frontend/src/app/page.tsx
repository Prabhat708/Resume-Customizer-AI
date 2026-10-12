"use client";

import React, { useEffect, useState } from "react";
import {
  Sparkles,
  ArrowLeft,
  FileCheck2,
  BarChart3,
  GitCompare,
  Info,
  Printer,
} from "lucide-react";
import { Header } from "@/components/Header";
import { JobDescriptionInput } from "@/components/JobDescriptionInput";
import { ResumeUpload } from "@/components/ResumeUpload";
import { MatchAnalysisCard } from "@/components/MatchAnalysisCard";
import { ResumePreview } from "@/components/ResumePreview";
import { DiffView } from "@/components/DiffView";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { ErrorAlert } from "@/components/ErrorAlert";
import { checkHealth, customizeResume, exportTailoredPdf, ApiError } from "@/lib/api";
import { CustomizeResponse, HealthResponse } from "@/types/api";

type ActiveTab = "preview" | "analysis" | "diff";

export default function Home() {
  // Backend health state
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);

  // Workflow input state
  const [jobDescription, setJobDescription] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Submission & results state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [pdfNotice, setPdfNotice] = useState<string | null>(null);
  const [errorState, setErrorState] = useState<{ code?: string; message: string } | null>(null);
  const [customizationResult, setCustomizationResult] = useState<CustomizeResponse | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>("preview");

  // Check backend health on mount
  useEffect(() => {
    let isMounted = true;
    checkHealth()
      .then((data) => {
        if (isMounted) {
          setHealth(data);
          setHealthLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setHealthError(err instanceof Error ? err.message : "Failed connecting to backend");
          setHealthLoading(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  // Form validity
  const isJdValid = jobDescription.trim().length >= 50;
  const isFormValid = isJdValid && selectedFile !== null && !isSubmitting;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormValid || !selectedFile) return;

    setErrorState(null);
    setIsSubmitting(true);

    try {
      const response = await customizeResume(selectedFile, jobDescription);
      setCustomizationResult(response);
      setActiveTab("preview");
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorState({
          code: err.code,
          message: err.message || "Customization failed. Please verify the resume format and try again.",
        });
      } else if (err instanceof Error) {
        setErrorState({
          message: err.message || "Network error. Please check backend connection.",
        });
      } else {
        setErrorState({
          message: "An unexpected error occurred during resume customization.",
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!customizationResult) return;

    setIsDownloadingPdf(true);
    setPdfNotice(null);
    try {
      const blob = await exportTailoredPdf(customizationResult.tailored_resume);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      const candidateName =
        customizationResult.tailored_resume.contact_info.name.replace(/[^a-zA-Z0-9]/g, "_") || "Tailored";
      link.download = `${candidateName}_ResumeCraft_Customized.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch {
      // Clearly communicate that server-side export is unavailable and browser print is used
      setPdfNotice(
        "Server-side PDF export is not implemented. Opening your browser's Print dialog to Print / Save as PDF."
      );
      window.print();
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const handleReset = () => {
    setCustomizationResult(null);
    setErrorState(null);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans">
      {/* 1. Header with branding and privacy reassurance */}
      <Header health={health} healthError={healthError} loading={healthLoading} />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {/* Loading Overlay */}
        <LoadingOverlay isLoading={isSubmitting} />

        {/* Error Alert (preserves inputs) */}
        {errorState && (
          <div className="mb-6">
            <ErrorAlert
              code={errorState.code}
              message={errorState.message}
              onDismiss={() => setErrorState(null)}
              onRetry={isFormValid ? () => handleSubmit({ preventDefault: () => {} } as React.FormEvent) : undefined}
            />
          </div>
        )}

        {/* WORKFLOW VIEW: If no customization result, show two-step input form */}
        {!customizationResult ? (
          <div className="space-y-8">
            {/* Hero / Value Proposition */}
            <div className="text-center max-w-2xl mx-auto">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                Align Your Real Experience with Target Roles
              </h1>
              <p className="mt-2.5 text-sm sm:text-base text-slate-600 leading-relaxed">
                ResumeCraft tailors professional summaries, groups verified skills, and reframes experience bullets with transparent evidence scoring — with zero fabricated claims.
              </p>
            </div>

            {/* Two-Step Form */}
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
                {/* Step 1: Job Description Input */}
                <div className="h-full">
                  <JobDescriptionInput
                    value={jobDescription}
                    onChange={(val) => {
                      setJobDescription(val);
                      if (errorState) setErrorState(null);
                    }}
                    disabled={isSubmitting}
                  />
                </div>

                {/* Step 2: Resume Upload */}
                <div className="h-full">
                  <ResumeUpload
                    file={selectedFile}
                    onFileSelect={(f) => {
                      setSelectedFile(f);
                      if (errorState) setErrorState(null);
                    }}
                    disabled={isSubmitting}
                  />
                </div>
              </div>

              {/* Primary Action Button */}
              <div className="flex flex-col sm:flex-row items-center justify-between bg-white border border-slate-200 rounded-xl p-5 shadow-xs gap-4">
                <div className="flex items-center space-x-3 text-xs text-slate-500">
                  <span className="flex items-center space-x-1.5">
                    <span
                      className={`h-2 w-2 rounded-full ${
                        isJdValid ? "bg-emerald-500" : "bg-slate-300"
                      }`}
                    />
                    <span>Job Description ({jobDescription.length >= 50 ? "Ready" : "Min 50 chars"})</span>
                  </span>
                  <span>•</span>
                  <span className="flex items-center space-x-1.5">
                    <span
                      className={`h-2 w-2 rounded-full ${
                        selectedFile ? "bg-emerald-500" : "bg-slate-300"
                      }`}
                    />
                    <span>Resume File ({selectedFile ? "Attached" : "Required"})</span>
                  </span>
                </div>

                <button
                  type="submit"
                  disabled={!isFormValid || isSubmitting}
                  className={`inline-flex items-center justify-center space-x-2 px-6 py-3 rounded-xl text-sm font-bold shadow-xs transition-all ${
                    isFormValid && !isSubmitting
                      ? "bg-indigo-600 hover:bg-indigo-700 text-white cursor-pointer active:scale-[0.99]"
                      : "bg-slate-200 text-slate-400 cursor-not-allowed"
                  }`}
                  aria-label="Customize my resume"
                >
                  <Sparkles className="h-4 w-4" />
                  <span>Customize My Resume</span>
                </button>
              </div>
            </form>

            {/* Feature Assurance Badges */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-200 text-center">
              <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs">
                <div className="text-xs font-bold text-slate-900 mb-0.5">Strict Factuality Guarantee</div>
                <p className="text-[11px] text-slate-500">No invented employers, dates, qualifications, or metrics.</p>
              </div>
              <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs">
                <div className="text-xs font-bold text-slate-900 mb-0.5">Transparent Match Scoring</div>
                <p className="text-[11px] text-slate-500">Deterministic formula-driven score with verifiable quotes.</p>
              </div>
              <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs">
                <div className="text-xs font-bold text-slate-900 mb-0.5">Bullet-Level Provenance</div>
                <p className="text-[11px] text-slate-500">Every tailored bullet traces back to original candidate experience.</p>
              </div>
            </div>
          </div>
        ) : (
          /* RESULTS VIEW: Full results interface with Tabs, Actions & Previews */
          <div className="space-y-6">
            {/* Top Toolbar */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between bg-white border border-slate-200 rounded-xl p-4 shadow-xs gap-3">
              <button
                type="button"
                onClick={handleReset}
                className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
                aria-label="Edit job description and resume inputs"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Edit Inputs / New Customization</span>
              </button>

              <div className="flex items-center space-x-3">
                <span className="text-xs text-slate-500 hidden sm:inline">
                  Score: <strong className="text-slate-800">{customizationResult.match_analysis.estimated_score}%</strong>
                </span>
                <button
                  type="button"
                  onClick={handleDownloadPdf}
                  disabled={isDownloadingPdf}
                  className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition-all active:scale-[0.99] cursor-pointer"
                  aria-label="Print or Save resume as PDF"
                >
                  <Printer className="h-3.5 w-3.5" />
                  <span>{isDownloadingPdf ? "Processing..." : "Print / Save as PDF"}</span>
                </button>
              </div>
            </div>

            {/* Notice when browser print fallback is active */}
            {pdfNotice && (
              <div
                className="bg-blue-50 border border-blue-200 rounded-xl p-3 text-xs text-blue-800 flex items-start justify-between gap-2 shadow-2xs"
                role="status"
              >
                <div className="flex items-start space-x-2">
                  <Info className="h-4 w-4 text-blue-600 mt-0.5 shrink-0" />
                  <span>{pdfNotice}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setPdfNotice(null)}
                  className="text-blue-500 hover:text-blue-800 px-1 font-bold"
                  aria-label="Dismiss notice"
                >
                  ×
                </button>
              </div>
            )}

            {/* Navigation Tabs */}
            <nav className="flex space-x-1 border-b border-slate-200 bg-white rounded-xl p-1.5 shadow-2xs" aria-label="Results tabs">
              <button
                type="button"
                onClick={() => setActiveTab("preview")}
                className={`flex-1 inline-flex items-center justify-center space-x-2 py-2.5 px-3 rounded-lg text-xs sm:text-sm font-bold transition-all ${
                  activeTab === "preview"
                    ? "bg-indigo-600 text-white shadow-xs"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
                aria-selected={activeTab === "preview"}
                role="tab"
              >
                <FileCheck2 className="h-4 w-4" />
                <span>Resume Preview</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab("analysis")}
                className={`flex-1 inline-flex items-center justify-center space-x-2 py-2.5 px-3 rounded-lg text-xs sm:text-sm font-bold transition-all ${
                  activeTab === "analysis"
                    ? "bg-indigo-600 text-white shadow-xs"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
                aria-selected={activeTab === "analysis"}
                role="tab"
              >
                <BarChart3 className="h-4 w-4" />
                <span>Match Analysis</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab("diff")}
                className={`flex-1 inline-flex items-center justify-center space-x-2 py-2.5 px-3 rounded-lg text-xs sm:text-sm font-bold transition-all ${
                  activeTab === "diff"
                    ? "bg-indigo-600 text-white shadow-xs"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
                aria-selected={activeTab === "diff"}
                role="tab"
              >
                <GitCompare className="h-4 w-4" />
                <span>Original vs. Tailored Diff</span>
              </button>
            </nav>

            {/* Tab Contents */}
            <div className="pt-2">
              {activeTab === "preview" && (
                <ResumePreview resume={customizationResult.tailored_resume} />
              )}

              {activeTab === "analysis" && (
                <MatchAnalysisCard analysis={customizationResult.match_analysis} />
              )}

              {activeTab === "diff" && (
                <DiffView resume={customizationResult.tailored_resume} />
              )}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-2">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-700">ResumeCraft</span>
            <span>•</span>
            <span>AI Resume Customizer</span>
          </div>
          <div>
            <span>Processed for customization • Resumes are not intentionally persisted by the application</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
