"use client";

import React from "react";
import { ShieldCheck, CheckCircle2, XCircle, Sparkles } from "lucide-react";
import { HealthResponse } from "@/types/api";

interface HeaderProps {
  health: HealthResponse | null;
  healthError: string | null;
  loading: boolean;
}

export function Header({ health, healthError, loading }: HeaderProps) {
  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-30 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between py-3 gap-3">
          {/* Logo & Product Name */}
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-xs">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-slate-900 tracking-tight text-xl">
                  ResumeCraft
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-150">
                  AI Tailoring
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">
                Align your verified resume with target job descriptions without fabrication
              </p>
            </div>
          </div>

          {/* Privacy Reassurance & Backend Status */}
          <div className="flex items-center flex-wrap gap-2 text-xs">
            {/* Privacy Badge */}
            <div className="inline-flex items-center text-slate-600 bg-slate-50 px-2.5 py-1 rounded-md border border-slate-200">
              <ShieldCheck className="h-3.5 w-3.5 mr-1.5 text-indigo-600 shrink-0" />
              <span>Processed for customization • Not intentionally persisted</span>
            </div>

            {/* Backend Connectivity Status */}
            <div>
              {loading ? (
                <span className="inline-flex items-center text-slate-400 bg-slate-50 px-2.5 py-1 rounded-md border border-slate-200">
                  <span className="h-2 w-2 rounded-full bg-slate-300 animate-pulse mr-1.5" />
                  Connecting...
                </span>
              ) : health ? (
                <span className="inline-flex items-center text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200 font-medium">
                  <CheckCircle2 className="h-3.5 w-3.5 mr-1.5 text-emerald-600 shrink-0" />
                  API Online (v{health.version})
                </span>
              ) : (
                <span
                  title={healthError || "Check localhost:8000"}
                  className="inline-flex items-center text-amber-700 bg-amber-50 px-2.5 py-1 rounded-md border border-amber-200"
                >
                  <XCircle className="h-3.5 w-3.5 mr-1.5 text-amber-600 shrink-0" />
                  API Disconnected
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
