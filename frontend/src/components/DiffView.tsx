"use client";

import React, { useState } from "react";
import { ArrowRight, AlertTriangle, CheckCircle2, ShieldCheck, Sparkles, Filter } from "lucide-react";
import { TailoredResume, TailoredBullet, AuditWarning, TailingChange } from "@/types/api";

interface DiffViewProps {
  resume: TailoredResume;
}

export function DiffView({ resume }: DiffViewProps) {
  const [filterType, setFilterType] = useState<"all" | "warnings">("all");

  const allBullets: { company: string; role: string; bullet: TailoredBullet }[] = [];
  resume.experience.forEach((exp) => {
    exp.bullets.forEach((b) => {
      allBullets.push({ company: exp.company, role: exp.role, bullet: b });
    });
  });

  const auditWarnings = resume.audit_warnings || [];

  return (
    <div className="space-y-6">
      {/* Overview Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2">
              <ShieldCheck className="h-5 w-5 text-indigo-600" />
              <span>Factuality Provenance &amp; Diff Comparison</span>
            </h3>
            <p className="text-xs text-slate-600 mt-1 max-w-2xl">
              Inspect how original experience bullets were reframed to align with target qualifications. Every tailored bullet traces back to an immutable original claim.
            </p>
          </div>

          <div className="flex items-center space-x-3 text-xs">
            <span className="px-3 py-1.5 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-800 font-semibold">
              {allBullets.length} Tracked Bullets
            </span>
            {auditWarnings.length > 0 ? (
              <span className="px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 font-semibold flex items-center space-x-1">
                <AlertTriangle className="h-3.5 w-3.5 text-amber-600 mr-1" />
                <span>{auditWarnings.length} Flagged</span>
              </span>
            ) : (
              <span className="px-3 py-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 font-semibold flex items-center space-x-1">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 mr-1" />
                <span>Zero Hallucinations</span>
              </span>
            )}
          </div>
        </div>

        {/* Tailoring Changes Summary */}
        {resume.tailoring_changes && resume.tailoring_changes.length > 0 && (
          <div className="mt-5 pt-4 border-t border-slate-100">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Summary of Modifications
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
              {resume.tailoring_changes.map((change: TailingChange, idx: number) => (
                <div key={idx} className="bg-slate-50 p-2.5 rounded-lg border border-slate-150 text-xs">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-slate-800">{change.section}</span>
                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                        change.change_type === "reframed"
                          ? "bg-indigo-100 text-indigo-700"
                          : change.change_type === "enhanced"
                          ? "bg-blue-100 text-blue-700"
                          : "bg-slate-200 text-slate-700"
                      }`}
                    >
                      {change.change_type}
                    </span>
                  </div>
                  <p className="text-slate-600 text-[11px] leading-relaxed">{change.reasoning}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Audit Warnings Banner */}
      {auditWarnings.length > 0 && (
        <div className="bg-amber-50/80 rounded-xl border border-amber-200 p-5 shadow-xs space-y-3">
          <div className="flex items-center space-x-2 text-amber-900">
            <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0" />
            <h4 className="text-sm font-bold">
              Verification Notice: Claims Flagged for Candidate Review ({auditWarnings.length})
            </h4>
          </div>
          <p className="text-xs text-amber-800">
            The automated auditor flagged ambiguous phrasing or unconfirmed metrics. Please verify that the customized statements accurately reflect your accomplishments.
          </p>

          <div className="space-y-2 mt-2">
            {auditWarnings.map((warn: AuditWarning, idx: number) => (
              <div key={idx} className="bg-white rounded-lg p-3 border border-amber-200 text-xs space-y-1">
                <div className="flex items-center justify-between font-semibold text-slate-800">
                  <span>{warn.bullet_ref}</span>
                  <span className="text-amber-700 font-normal italic">{warn.concern}</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-1 text-[11px]">
                  <div className="text-slate-500 bg-slate-50 p-1.5 rounded">
                    <strong>Original:</strong> {warn.original_text}
                  </div>
                  <div className="text-indigo-700 bg-indigo-50/50 p-1.5 rounded">
                    <strong>Tailored:</strong> {warn.tailored_text}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filter Options */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-bold text-slate-900">
          Side-by-Side Bullet Comparison ({allBullets.length})
        </h4>

        {auditWarnings.length > 0 && (
          <div className="flex items-center space-x-2 text-xs">
            <Filter className="h-3.5 w-3.5 text-slate-400" />
            <button
              type="button"
              onClick={() => setFilterType("all")}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                filterType === "all" ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              All Bullets
            </button>
            <button
              type="button"
              onClick={() => setFilterType("warnings")}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                filterType === "warnings" ? "bg-amber-600 text-white" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              Flagged Only ({auditWarnings.length})
            </button>
          </div>
        )}
      </div>

      {/* Bullet Diff Cards */}
      <div className="space-y-4">
        {allBullets.map((item, idx) => {
          const { company, role, bullet } = item;
          const isIdentical = bullet.original_text.trim() === bullet.tailored_text.trim();

          return (
            <div
              key={idx}
              className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs transition-all hover:border-slate-300"
            >
              <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-150 flex items-center justify-between text-xs">
                <div className="font-semibold text-slate-800">
                  <span>{company}</span>
                  <span className="text-slate-400 mx-1.5">•</span>
                  <span className="text-slate-600 font-normal">{role}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-[10px] text-slate-400">
                    Source Bullet #{bullet.source_bullet_id}
                  </span>
                  <span
                    className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                      isIdentical
                        ? "bg-slate-200 text-slate-600"
                        : "bg-indigo-100 text-indigo-700"
                    }`}
                  >
                    {isIdentical ? "Unchanged" : "Reframed"}
                  </span>
                </div>
              </div>

              <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs sm:text-sm">
                {/* Original Bullet */}
                <div className="space-y-1">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                    Original Bullet Point
                  </span>
                  <div className="p-3 bg-slate-50 rounded-lg text-slate-700 border border-slate-150 leading-relaxed min-h-[60px]">
                    {bullet.original_text}
                  </div>
                </div>

                {/* Customized Bullet */}
                <div className="space-y-1">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-600 flex items-center space-x-1">
                    <Sparkles className="h-3 w-3" />
                    <span>Tailored Bullet Point</span>
                  </span>
                  <div className="p-3 bg-indigo-50/40 rounded-lg text-indigo-950 border border-indigo-200 leading-relaxed min-h-[60px]">
                    {bullet.tailored_text}
                  </div>
                </div>
              </div>

              {/* Rationale Footer */}
              {bullet.rationale && (
                <div className="px-4 py-2.5 bg-slate-50/50 border-t border-slate-100 text-xs text-slate-600 flex items-start space-x-2">
                  <ArrowRight className="h-3.5 w-3.5 text-indigo-500 mt-0.5 shrink-0" />
                  <span>
                    <strong className="text-slate-700">Rationale:</strong> {bullet.rationale}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
