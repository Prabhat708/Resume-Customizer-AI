"use client";

import React, { useState } from "react";
import {
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  ShieldCheck,
  Sparkles,
  Filter,
  FileText,
  Layers,
  HelpCircle,
  ArrowUpDown,
  MinusCircle,
} from "lucide-react";
import {
  TailoredResume,
  TailoredBullet,
  AuditWarning,
  TailingChange,
  ParsedResume,
  MissingRequirement,
} from "@/types/api";

interface DiffViewProps {
  resume?: TailoredResume;
  tailoredResume?: TailoredResume;
  originalResume?: ParsedResume;
  missingRequirements?: MissingRequirement[];
}

export function DiffView({
  resume,
  tailoredResume: tailoredResumeProp,
  originalResume,
  missingRequirements = [],
}: DiffViewProps) {
  const tailored = tailoredResumeProp || resume;
  const [filterType, setFilterType] = useState<"all" | "reframed" | "reordered" | "unchanged" | "warnings">("all");

  if (!tailored) {
    return (
      <div className="p-8 text-center bg-white rounded-xl border border-slate-200 text-slate-500 text-sm">
        No customized resume data available for comparison.
      </div>
    );
  }

  // Normalization helper to prevent trivial punctuation/whitespace differences from fabricating reframed classifications
  const normalizeBullet = (text: string) =>
    text
      .replace(/^[\s•*–—◦\u25e6\u2022\u25aa\u25cf\u25cb\u25b8\u27a4\u2713\u2714\u2043\u2219]+|^\s*\(?\d+[\.\)]\s*/, "")
      .replace(/[.\s]+$/, "")
      .trim()
      .toLowerCase()
      .replace(/\s+/g, " ");

  // 1. Process bullets with provenance, rewording, and reordering classifications
  interface ProcessedBulletItem {
    company: string;
    role: string;
    bullet: TailoredBullet;
    currentIndex: number;
    originalIndex: number;
    isIdentical: boolean;
    isMeaningfullyReworded: boolean;
    isReordered: boolean;
    isPureReorder: boolean;
  }

  const allBullets: ProcessedBulletItem[] = [];

  // Track omitted bullets from original resume
  interface OmittedBulletItem {
    company: string;
    role: string;
    originalIndex: number;
    text: string;
  }
  const omittedBullets: OmittedBulletItem[] = [];

  tailored.experience.forEach((tailoredExp, expIdx) => {
    // Locate corresponding original experience entry by matching company/role, substring, or index fallback
    const origExp =
      originalResume?.experience?.find(
        (oe) =>
          oe.company.trim().toLowerCase() === tailoredExp.company.trim().toLowerCase() ||
          oe.role.trim().toLowerCase() === tailoredExp.role.trim().toLowerCase() ||
          (oe.company &&
            tailoredExp.company &&
            (oe.company.toLowerCase().includes(tailoredExp.company.toLowerCase()) ||
              tailoredExp.company.toLowerCase().includes(oe.company.toLowerCase())))
      ) ||
      (originalResume?.experience?.length === 1
        ? originalResume.experience[0]
        : originalResume?.experience?.[expIdx]);

    const tailoredSourceIds = new Set<number>();

    tailoredExp.bullets.forEach((b, idx) => {
      const normOrig = normalizeBullet(b.original_text);
      const normTailored = normalizeBullet(b.tailored_text);
      const isIdentical = normOrig === normTailored;
      const isMeaningfullyReworded = !isIdentical;
      const isReordered = b.source_bullet_id !== idx;
      const isPureReorder = isIdentical && isReordered;
      tailoredSourceIds.add(b.source_bullet_id);

      allBullets.push({
        company: tailoredExp.company,
        role: tailoredExp.role,
        bullet: b,
        currentIndex: idx,
        originalIndex: b.source_bullet_id,
        isIdentical,
        isMeaningfullyReworded,
        isReordered,
        isPureReorder,
      });
    });

    // Check if any original bullets for this entry were omitted/consolidated
    if (origExp && origExp.bullets) {
      origExp.bullets.forEach((ob, oIdx) => {
        const bulletId = typeof ob.bullet_id === "number" ? ob.bullet_id : oIdx;
        if (!tailoredSourceIds.has(bulletId)) {
          omittedBullets.push({
            company: origExp.company,
            role: origExp.role,
            originalIndex: bulletId,
            text: ob.text,
          });
        }
      });
    }
  });

  const auditWarnings = tailored.audit_warnings || [];
  const reframedCount = allBullets.filter((b) => b.isMeaningfullyReworded).length;
  const pureReorderCount = allBullets.filter((b) => b.isPureReorder).length;
  const unchangedCount = allBullets.filter((b) => !b.isMeaningfullyReworded && !b.isReordered).length;
  const totalReorderedCount = allBullets.filter((b) => b.isReordered).length;

  const filteredBullets = allBullets.filter((item) => {
    if (filterType === "warnings") {
      return auditWarnings.some(
        (w) =>
          w.bullet_ref.includes(item.company) ||
          w.original_text.trim() === item.bullet.original_text.trim()
      );
    }
    if (filterType === "reframed") {
      return item.isMeaningfullyReworded;
    }
    if (filterType === "reordered") {
      return item.isReordered;
    }
    if (filterType === "unchanged") {
      return !item.isMeaningfullyReworded && !item.isReordered;
    }
    return true;
  });

  // Summary comparison
  const origSummary = originalResume?.summary?.trim() || "";
  const tailoredSummary = tailored.summary?.trim() || "";
  const hasSummaryDiff = origSummary !== "" || tailoredSummary !== "";
  const isSummaryIdentical =
    origSummary !== "" && tailoredSummary !== "" && origSummary === tailoredSummary;

  // Skills comparison
  const originalSkills = originalResume?.skills || [];
  const relevantSkills = tailored.skills.retained_relevant || [];
  const otherSkills = tailored.skills.retained_other || [];
  const omittedSkills = originalSkills.filter(
    (s) => !relevantSkills.includes(s) && !otherSkills.includes(s)
  );

  return (
    <div className="space-y-6">
      {/* 1. Factuality & Provenance Overview Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2">
              <ShieldCheck className="h-5 w-5 text-indigo-600" />
              <span>Factuality Provenance &amp; Diff Comparison</span>
            </h3>
            <p className="text-xs text-slate-600 mt-1 max-w-2xl leading-relaxed">
              Independent verification of summary, skills, and experience claims against customized phrasing.
              AI customization reframes verified achievements to match job description keywords
              without inventing ungrounded metrics or unsupported employment history.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs">
            {/* Independent Summary Badge */}
            {hasSummaryDiff && (
              <span
                className={`px-2.5 py-1 rounded-md font-semibold border ${
                  isSummaryIdentical
                    ? "bg-slate-100 border-slate-200 text-slate-700"
                    : "bg-indigo-50 border-indigo-200 text-indigo-700"
                }`}
              >
                Summary: {isSummaryIdentical ? "Unchanged" : origSummary ? "Reframed" : "Generated"}
              </span>
            )}

            {/* Independent Skills Badge */}
            <span className="px-2.5 py-1 rounded-md bg-blue-50 border border-blue-200 text-blue-800 font-semibold">
              Skills: {relevantSkills.length} Target-Matched, {otherSkills.length} Retained
            </span>

            {/* Independent Bullets Badge */}
            <span className="px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-slate-700 font-semibold">
              Experience: {allBullets.length} Bullets ({reframedCount} Reframed
              {pureReorderCount > 0 ? `, ${pureReorderCount} Pure Reorder` : ""}
              , {unchangedCount} Preserved
              {totalReorderedCount > 0 && pureReorderCount === 0 ? `, ${totalReorderedCount} Reordered` : ""})
            </span>

            {auditWarnings.length > 0 ? (
              <span className="px-2.5 py-1 rounded-md bg-amber-50 border border-amber-200 text-amber-800 font-semibold flex items-center space-x-1">
                <AlertTriangle className="h-3.5 w-3.5 text-amber-600 mr-1" />
                <span>{auditWarnings.length} Requires Review</span>
              </span>
            ) : (
              <span className="px-2.5 py-1 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-800 font-semibold flex items-center space-x-1">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 mr-1" />
                <span>Grounding Verified</span>
              </span>
            )}
          </div>
        </div>

        {/* Factuality Boundary Disclaimer */}
        <div className="mt-4 p-3 bg-amber-50/70 rounded-lg border border-amber-200/80 text-[11px] text-amber-900 flex items-start space-x-2">
          <HelpCircle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <strong className="font-semibold">Candidate Verification Required:</strong> AI-customized
            bullet points are derived directly from your uploaded resume. However, generated text
            is not automatically verified as factually true simply because it was produced by AI.
            Please review all reframed phrasing before submitting.
          </div>
        </div>

        {/* Tailoring Changes Summary */}
        {tailored.tailoring_changes && tailored.tailoring_changes.length > 0 && (
          <div className="mt-5 pt-4 border-t border-slate-100">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
              <Layers className="h-3.5 w-3.5 text-slate-400" />
              <span>Section Modification Rationale</span>
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
              {tailored.tailoring_changes.map((change: TailingChange, idx: number) => (
                <div key={idx} className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-xs">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-slate-800">{change.section}</span>
                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                        change.change_type === "reframed"
                          ? "bg-indigo-100 text-indigo-700"
                          : change.change_type === "reordered"
                          ? "bg-purple-100 text-purple-700"
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

      {/* 2. Audit Warnings Banner */}
      {auditWarnings.length > 0 && (
        <div className="bg-amber-50/90 rounded-xl border border-amber-300 p-5 shadow-xs space-y-3">
          <div className="flex items-center space-x-2 text-amber-950">
            <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0" />
            <h4 className="text-sm font-bold">
              Auditor Notice: Ambiguous or High-Impact Phrasing Flagged ({auditWarnings.length})
            </h4>
          </div>
          <p className="text-xs text-amber-800 leading-relaxed">
            The factuality auditor detected phrasing or metrics that may introduce unconfirmed scope.
            Verify that these statements accurately describe your past experience:
          </p>

          <div className="space-y-2 mt-2">
            {auditWarnings.map((warn: AuditWarning, idx: number) => (
              <div key={idx} className="bg-white rounded-lg p-3 border border-amber-200 text-xs space-y-1.5 shadow-2xs">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between font-semibold text-slate-800 gap-1">
                  <span>{warn.bullet_ref}</span>
                  <span className="text-amber-800 text-[11px] font-medium bg-amber-100/60 px-2 py-0.5 rounded">
                    {warn.concern}
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-1 text-[11px]">
                  <div className="text-slate-600 bg-slate-50 p-2 rounded border border-slate-200">
                    <strong className="text-slate-700 block mb-0.5">Original Claim:</strong>
                    {warn.original_text}
                  </div>
                  <div className="text-indigo-950 bg-indigo-50/60 p-2 rounded border border-indigo-200">
                    <strong className="text-indigo-800 block mb-0.5">Tailored Phrasing:</strong>
                    {warn.tailored_text}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Professional Summary Diff (if either original or tailored exists) */}
      {hasSummaryDiff && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
            <h4 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
              <FileText className="h-4 w-4 text-indigo-600" />
              <span>Professional Summary Diff</span>
            </h4>
            <span
              className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                isSummaryIdentical
                  ? "bg-slate-100 text-slate-600"
                  : "bg-indigo-100 text-indigo-700"
              }`}
            >
              {isSummaryIdentical ? "Unchanged" : origSummary ? "Reframed" : "Generated"}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            {/* Original Summary */}
            <div className="space-y-1">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                Original Summary
              </span>
              <div className="p-3 bg-slate-50 rounded-lg text-slate-700 border border-slate-200 leading-relaxed min-h-[50px]">
                {origSummary || <em className="text-slate-400">None provided in original resume</em>}
              </div>
            </div>

            {/* Tailored Summary */}
            <div className="space-y-1">
              <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-600 flex items-center space-x-1">
                <Sparkles className="h-3 w-3" />
                <span>Tailored Summary</span>
              </span>
              <div className="p-3 bg-indigo-50/40 rounded-lg text-indigo-950 border border-indigo-200 leading-relaxed min-h-[50px]">
                {tailoredSummary || <em className="text-slate-400">None specified</em>}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 4. Skills Categorization & Retention */}
      {(relevantSkills.length > 0 || otherSkills.length > 0 || originalSkills.length > 0) && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
          <h4 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
            <Layers className="h-4 w-4 text-indigo-600" />
            <span>Skills Partitioning &amp; Relevance Alignment</span>
          </h4>
          <p className="text-xs text-slate-500">
            Skills are partitioned into target-role matches and background skills. No unverified
            technologies from the job description are artificially added.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
            {/* Target Role Relevant Skills */}
            <div className="bg-indigo-50/50 p-3.5 rounded-lg border border-indigo-200 text-xs">
              <span className="font-bold text-indigo-900 block mb-1.5 flex items-center justify-between">
                <span>Target-Role Relevant Skills ({relevantSkills.length})</span>
                <span className="text-[10px] uppercase tracking-wider bg-indigo-200/70 text-indigo-800 px-1.5 py-0.2 rounded font-bold">
                  Highlighted
                </span>
              </span>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {relevantSkills.map((s, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 bg-white text-indigo-900 border border-indigo-200 rounded font-medium text-[11px]"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>

            {/* Additional Candidate Skills */}
            <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200 text-xs">
              <span className="font-bold text-slate-800 block mb-1.5 flex items-center justify-between">
                <span>Additional Candidate Skills ({otherSkills.length})</span>
                <span className="text-[10px] uppercase tracking-wider bg-slate-200 text-slate-700 px-1.5 py-0.2 rounded font-bold">
                  Preserved
                </span>
              </span>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {otherSkills.length > 0 ? (
                  otherSkills.map((s, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 bg-white text-slate-700 border border-slate-200 rounded text-[11px]"
                    >
                      {s}
                    </span>
                  ))
                ) : (
                  <span className="text-slate-400 italic text-[11px]">All verified skills aligned with target role</span>
                )}
              </div>
            </div>
          </div>

          {omittedSkills.length > 0 && (
            <div className="pt-2 text-[11px] text-slate-500">
              <strong className="text-slate-600">Omitted or deduplicated from final list:</strong>{" "}
              {omittedSkills.join(", ")}
            </div>
          )}
        </div>
      )}

      {/* 5. Unsupported Job Requirements Alert */}
      {missingRequirements.length > 0 && (
        <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 text-xs space-y-2">
          <div className="flex items-center space-x-2 text-slate-800 font-bold">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
            <span>Job Requirements Not Supported in Source Resume ({missingRequirements.length})</span>
          </div>
          <p className="text-slate-600 text-[11px] leading-relaxed">
            The target job description requested qualifications that were not found in your uploaded resume.
            To preserve strict factuality, these have not been added to your tailored resume:
          </p>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {missingRequirements.map((mr, idx) => (
              <span
                key={idx}
                className="px-2.5 py-1 bg-white border border-slate-200 rounded text-slate-700 text-[11px]"
              >
                {mr.requirement} ({mr.importance})
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 6. Bullets Diff List with Controls */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <h4 className="text-sm font-bold text-slate-900">
            Experience Bullets Side-by-Side Comparison ({allBullets.length})
          </h4>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <Filter className="h-3.5 w-3.5 text-slate-400 mr-1" />
            <button
              type="button"
              onClick={() => setFilterType("all")}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                filterType === "all"
                  ? "bg-slate-900 text-white"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              All ({allBullets.length})
            </button>
            <button
              type="button"
              onClick={() => setFilterType("reframed")}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                filterType === "reframed"
                  ? "bg-indigo-600 text-white"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              Reframed ({reframedCount})
            </button>
            {totalReorderedCount > 0 && (
              <button
                type="button"
                onClick={() => setFilterType("reordered")}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  filterType === "reordered"
                    ? "bg-purple-600 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                Reordered ({totalReorderedCount})
              </button>
            )}
            <button
              type="button"
              onClick={() => setFilterType("unchanged")}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                filterType === "unchanged"
                  ? "bg-slate-700 text-white"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              Unchanged ({unchangedCount})
            </button>
            {auditWarnings.length > 0 && (
              <button
                type="button"
                onClick={() => setFilterType("warnings")}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  filterType === "warnings"
                    ? "bg-amber-600 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                Warnings ({auditWarnings.length})
              </button>
            )}
          </div>
        </div>

        {/* Bullets List */}
        <div className="space-y-4">
          {filteredBullets.map((item, idx) => {
            const { company, role, bullet, isMeaningfullyReworded, isReordered, isPureReorder, originalIndex, currentIndex } =
              item;

            return (
              <div
                key={idx}
                className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs transition-all hover:border-slate-300"
              >
                {/* Header with Provenance */}
                <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between text-xs gap-2">
                  <div className="font-semibold text-slate-800">
                    <span>{company}</span>
                    <span className="text-slate-400 mx-1.5">•</span>
                    <span className="text-slate-600 font-normal">{role}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-[10px] text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                      Source Bullet #{bullet.source_bullet_id}
                    </span>
                    {isReordered && (
                      <span className="text-[10px] font-semibold text-purple-700 bg-purple-50 border border-purple-200 px-2 py-0.5 rounded flex items-center space-x-1">
                        <ArrowUpDown className="h-3 w-3 inline" />
                        <span>Reordered ({originalIndex + 1} &rarr; {currentIndex + 1})</span>
                      </span>
                    )}
                    {isPureReorder ? (
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-purple-100 text-purple-700">
                        Pure Reorder (Preserved verbatim)
                      </span>
                    ) : isMeaningfullyReworded && isReordered ? (
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-100 text-indigo-700">
                        Reframed &amp; Reordered
                      </span>
                    ) : isMeaningfullyReworded ? (
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-100 text-indigo-700">
                        Reframed (Role-aligned)
                      </span>
                    ) : (
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-200 text-slate-700">
                        Unchanged (Preserved verbatim)
                      </span>
                    )}
                  </div>
                </div>

                {/* Side-by-side on desktop, stacked on mobile */}
                <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs sm:text-sm">
                  {/* Original Bullet */}
                  <div className="space-y-1">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                      Original Source Claim (Position #{originalIndex + 1})
                    </span>
                    <div className="p-3 bg-slate-50 rounded-lg text-slate-700 border border-slate-200 leading-relaxed min-h-[60px]">
                      {bullet.original_text}
                    </div>
                  </div>

                  {/* Customized Bullet */}
                  <div className="space-y-1">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-600 flex items-center space-x-1">
                      <Sparkles className="h-3 w-3" />
                      <span>Customized Bullet (Position #{currentIndex + 1})</span>
                    </span>
                    <div className="p-3 bg-indigo-50/40 rounded-lg text-indigo-950 border border-indigo-200 leading-relaxed min-h-[60px]">
                      {bullet.tailored_text}
                    </div>
                  </div>
                </div>

                {/* Rationale Footer */}
                {bullet.rationale && (
                  <div className="px-4 py-2.5 bg-slate-50/60 border-t border-slate-100 text-xs text-slate-600 flex items-start space-x-2">
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

        {/* 7. Omitted Original Bullets (if any original bullets were not carried over) */}
        {omittedBullets.length > 0 && (
          <div className="mt-6 bg-slate-50 rounded-xl border border-slate-200 p-5 space-y-3">
            <div className="flex items-center space-x-2 text-slate-800">
              <MinusCircle className="h-4 w-4 text-slate-500" />
              <h4 className="text-sm font-bold">
                Original Bullets Not Included in Customized Version ({omittedBullets.length})
              </h4>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              These points from your original resume were deprioritized or consolidated to prioritize
              target job requirements within standard resume length constraints:
            </p>
            <div className="space-y-2">
              {omittedBullets.map((ob, idx) => (
                <div
                  key={idx}
                  className="bg-white p-3 rounded-lg border border-slate-200 text-xs text-slate-700 space-y-1"
                >
                  <div className="font-semibold text-slate-600 text-[11px]">
                    {ob.company} &bull; {ob.role} &bull; Original Position #{ob.originalIndex + 1}
                  </div>
                  <div className="text-slate-600">{ob.text}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
