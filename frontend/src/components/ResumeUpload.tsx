"use client";

import React, { useRef, useState } from "react";
import { UploadCloud, FileText, CheckCircle2, AlertCircle, X, RefreshCw } from "lucide-react";

interface ResumeUploadProps {
  file: File | null;
  onFileSelect: (file: File | null) => void;
  error?: string | null;
  disabled?: boolean;
}

const MAX_FILE_SIZE_MB = 5;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
const ALLOWED_EXTENSIONS = [".pdf", ".docx"];

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export function ResumeUpload({
  file,
  onFileSelect,
  error,
  disabled = false,
}: ResumeUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndSetFile = (candidateFile: File) => {
    setValidationError(null);

    // Extension check
    const nameLower = candidateFile.name.toLowerCase();
    const hasValidExt = ALLOWED_EXTENSIONS.some((ext) => nameLower.endsWith(ext));
    if (!hasValidExt) {
      setValidationError("Unsupported file format. Please upload a PDF (.pdf) or Word document (.docx).");
      return;
    }

    // Size check (5 MB)
    if (candidateFile.size > MAX_FILE_SIZE_BYTES) {
      setValidationError(
        `File size (${formatFileSize(candidateFile.size)}) exceeds the maximum allowed limit of ${MAX_FILE_SIZE_MB} MB.`
      );
      return;
    }

    // Empty check
    if (candidateFile.size === 0) {
      setValidationError("The selected file is empty (0 bytes). Please upload a valid document.");
      return;
    }

    onFileSelect(candidateFile);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (disabled) return;
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    onFileSelect(null);
    setValidationError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleReplaceClick = () => {
    if (disabled) return;
    fileInputRef.current?.click();
  };

  const displayError = error || validationError;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <label className="text-sm font-semibold text-slate-900 flex items-center space-x-2">
          <span className="flex items-center justify-center w-5 h-5 rounded-full bg-indigo-50 text-indigo-700 text-xs font-bold mr-1">
            2
          </span>
          <UploadCloud className="h-4 w-4 text-indigo-600 inline mr-1" />
          <span>Upload Resume</span>
        </label>
        <span className="text-xs text-slate-400 font-medium">PDF or DOCX (Max {MAX_FILE_SIZE_MB} MB)</span>
      </div>

      <p className="text-xs text-slate-500 mb-3">
        Upload your existing resume. The parser extracts your real experience, skills, and metrics in-memory.
      </p>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        onChange={handleFileInputChange}
        disabled={disabled}
        className="hidden"
        id="resume-file-input"
        aria-label="Upload resume file"
      />

      {/* Selected File State */}
      {file ? (
        <div className="flex-1 flex flex-col justify-center">
          <div className="border border-indigo-200 bg-indigo-50/40 rounded-xl p-5 transition-all">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3 min-w-0">
                <div className="h-10 w-10 rounded-lg bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-xs">
                  <FileText className="h-5 w-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center space-x-2">
                    <p className="text-sm font-semibold text-slate-900 truncate" title={file.name}>
                      {file.name}
                    </p>
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  </div>
                  <div className="flex items-center space-x-2 text-xs text-slate-500 mt-0.5">
                    <span className="font-mono">{formatFileSize(file.size)}</span>
                    <span>•</span>
                    <span className="uppercase text-[10px] font-semibold tracking-wider text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">
                      {file.name.split(".").pop() || "doc"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-1 shrink-0 ml-3">
                <button
                  type="button"
                  onClick={handleReplaceClick}
                  disabled={disabled}
                  title="Replace file"
                  className="p-1.5 text-slate-500 hover:text-indigo-600 hover:bg-white rounded-md transition-colors"
                  aria-label="Replace selected file"
                >
                  <RefreshCw className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={handleRemove}
                  disabled={disabled}
                  title="Remove file"
                  className="p-1.5 text-slate-500 hover:text-red-600 hover:bg-white rounded-md transition-colors"
                  aria-label="Remove selected file"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>

            <div className="mt-3 pt-3 border-t border-indigo-100/80 flex items-center justify-between text-xs text-indigo-700">
              <span className="font-medium">File verified and ready for customization</span>
              <button
                type="button"
                onClick={handleReplaceClick}
                disabled={disabled}
                className="underline hover:text-indigo-900 font-semibold"
              >
                Change file
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* Drag-and-Drop Area */
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleReplaceClick}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              handleReplaceClick();
            }
          }}
          className={`flex-1 flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-xl cursor-pointer transition-all min-h-[220px] text-center ${
            isDragging
              ? "border-indigo-500 bg-indigo-50/50"
              : displayError
              ? "border-red-300 bg-red-50/20 hover:border-red-400"
              : "border-slate-300 bg-slate-50/50 hover:border-indigo-400 hover:bg-indigo-50/20"
          } ${disabled ? "opacity-60 cursor-not-allowed" : ""}`}
          aria-label="Drag and drop resume here, or click to browse files"
        >
          <div className="h-12 w-12 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3">
            <UploadCloud className="h-6 w-6" />
          </div>
          <p className="text-sm font-semibold text-slate-800 mb-1">
            <span className="text-indigo-600 hover:text-indigo-700">Click to upload</span> or drag and drop
          </p>
          <p className="text-xs text-slate-500 max-w-xs">
            Supports text-based PDF (.pdf) and Microsoft Word (.docx) files up to {MAX_FILE_SIZE_MB} MB
          </p>
        </div>
      )}

      {/* Error Message */}
      {displayError && (
        <div className="mt-2.5 flex items-start text-xs text-red-600 space-x-1.5" role="alert">
          <AlertCircle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
          <span>{displayError}</span>
        </div>
      )}
    </div>
  );
}
