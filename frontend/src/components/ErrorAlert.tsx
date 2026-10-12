"use client";

import React from "react";
import { AlertCircle, X, RefreshCw } from "lucide-react";

interface ErrorAlertProps {
  code?: string;
  message: string;
  onDismiss?: () => void;
  onRetry?: () => void;
}

export function ErrorAlert({ code, message, onDismiss, onRetry }: ErrorAlertProps) {
  return (
    <div
      className="bg-red-50 border border-red-200 rounded-xl p-4 text-xs text-red-800 shadow-xs flex items-start justify-between gap-3"
      role="alert"
    >
      <div className="flex items-start space-x-2.5 flex-1">
        <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 shrink-0" />
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-red-900">Customization Request Failed</span>
            {code && (
              <span className="font-mono text-[10px] bg-red-100 text-red-700 px-1.5 py-0.5 rounded font-semibold">
                {code}
              </span>
            )}
          </div>
          <p className="text-red-700 leading-relaxed">{message}</p>
        </div>
      </div>

      <div className="flex items-center space-x-1 shrink-0">
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center space-x-1 px-2.5 py-1 text-xs font-semibold bg-white border border-red-200 text-red-700 rounded-md hover:bg-red-50 transition-colors"
          >
            <RefreshCw className="h-3 w-3" />
            <span>Retry</span>
          </button>
        )}
        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            className="p-1 text-red-500 hover:text-red-800 rounded transition-colors"
            aria-label="Dismiss error notification"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}
