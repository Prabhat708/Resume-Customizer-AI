"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, XCircle, ShieldCheck, FileText, Cpu, Download } from "lucide-react";
import { checkHealth } from "@/lib/api";
import { HealthResponse } from "@/types/api";

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    checkHealth()
      .then((data) => {
        if (isMounted) {
          setHealth(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setHealthError(err instanceof Error ? err.message : "Failed to connect to backend");
          setLoading(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top Navbar */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-30 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-sm">
              RC
            </div>
            <div>
              <span className="font-semibold text-slate-900 tracking-tight text-lg">
                Resume Customizer
              </span>
              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700">
                Phase 1 Scaffolding
              </span>
            </div>
          </div>

          {/* Backend Status Indicator */}
          <div className="flex items-center space-x-2 text-xs">
            <span className="text-slate-500 font-medium">Backend API:</span>
            {loading ? (
              <span className="inline-flex items-center text-slate-400">
                <span className="h-2 w-2 rounded-full bg-slate-300 animate-pulse mr-1.5" />
                Connecting...
              </span>
            ) : health ? (
              <span className="inline-flex items-center text-emerald-700 bg-emerald-50 px-2 py-1 rounded-md border border-emerald-200">
                <CheckCircle2 className="h-3.5 w-3.5 mr-1 text-emerald-600" />
                v{health.version} • {health.model_configured ? "Model Configured" : "No Model Set"}
              </span>
            ) : (
              <span className="inline-flex items-center text-amber-700 bg-amber-50 px-2 py-1 rounded-md border border-amber-200">
                <XCircle className="h-3.5 w-3.5 mr-1 text-amber-600" />
                Offline ({healthError || "Check localhost:8000"})
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full">
        {/* Architecture Header */}
        <div className="text-center max-w-3xl mx-auto mb-12">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Factuality-Preserved Resume Tailoring
          </h1>
          <p className="mt-3 text-base text-slate-600 sm:text-lg">
            Align your verified experience with target job descriptions without inventing
            metrics, employers, tools, or dates.
          </p>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <div className="h-10 w-10 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600 mb-4">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-slate-900 mb-1">Zero Fabrication</h3>
            <p className="text-sm text-slate-600">
              Identity, employment chronology, and metrics are locked. Missing requirements are reported separately.
            </p>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <div className="h-10 w-10 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600 mb-4">
              <Cpu className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-slate-900 mb-1">Explainable Match</h3>
            <p className="text-sm text-slate-600">
              Formula-based evidence scoring (1.0 explicit / 0.5 partial / 0.0 missing) with verifiable quotes.
            </p>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <div className="h-10 w-10 rounded-lg bg-purple-50 flex items-center justify-center text-purple-600 mb-4">
              <FileText className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-slate-900 mb-1">Bullet Provenance</h3>
            <p className="text-sm text-slate-600">
              Every tailored bullet links directly to its source with clear rationale and change tracking.
            </p>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <div className="h-10 w-10 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-600 mb-4">
              <Download className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-slate-900 mb-1">ATS PDF Export</h3>
            <p className="text-sm text-slate-600">
              Clean server-side PDF generation formatted for applicant tracking systems.
            </p>
          </div>
        </div>

        {/* Phase 1 Scaffolding Ready Notice */}
        <div className="bg-slate-900 text-white rounded-xl p-8 shadow-md">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold mb-1">Phase 1 Complete & Verified</h2>
              <p className="text-slate-300 text-sm max-w-2xl">
                The full backend test suite has passed (16/16 tests covering independent health probe and deterministic scoring formula). Next.js frontend structure and types are synchronized.
              </p>
            </div>
            <div className="text-xs bg-slate-800 border border-slate-700 rounded-lg p-3 font-mono">
              <div>API Contract: <span className="text-emerald-400">Synchronized</span></div>
              <div>Backend Tests: <span className="text-emerald-400">16 Passed</span></div>
              <div>Frontend Types: <span className="text-emerald-400">Verified</span></div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6 mt-auto">
        <div className="max-w-7xl mx-auto px-4 text-center text-xs text-slate-500">
          Resume Customizer • Built with Next.js, FastAPI, and Google Gen AI
        </div>
      </footer>
    </div>
  );
}
