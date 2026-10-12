"use client";

import React from "react";
import { Loader2 } from "lucide-react";

interface LoadingOverlayProps {
  isLoading: boolean;
}

export function LoadingOverlay({ isLoading }: LoadingOverlayProps) {
  if (!isLoading) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 transition-all"
      role="dialog"
      aria-modal="true"
      aria-label="Customizing resume in progress"
    >
      <div className="bg-white rounded-2xl max-w-sm w-full p-8 shadow-xl border border-slate-200 text-center space-y-4">
        <div className="mx-auto w-12 h-12 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>

        <div className="space-y-1.5">
          <h3 className="text-base font-bold text-slate-900">
            Processing Customization Request
          </h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            Uploading document and sending job description to the customization service. Please wait...
          </p>
        </div>

        <p className="text-[11px] text-slate-400 pt-3 border-t border-slate-100">
          Uploaded resumes are processed for customization and are not intentionally persisted by the application.
        </p>
      </div>
    </div>
  );
}
