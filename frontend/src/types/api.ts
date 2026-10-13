/**
 * src/types/api.ts — Strongly-typed TypeScript interfaces mirroring backend Pydantic schemas.
 * 
 * Strict synchronization with:
 * - app/schemas/common.py
 * - app/schemas/resume.py
 * - app/schemas/tailored.py
 * - app/schemas/analysis.py
 * - app/schemas/error.py
 * - app/schemas/api.py
 */

export type SupportStatus = "explicitly_supported" | "partially_supported" | "not_mentioned";
export type ImportanceLevel = "required" | "preferred";
export type ChangeType = "reframed" | "enhanced" | "unchanged" | "reordered";
export type EvidenceLevel = "work_experience" | "projects" | "skills" | "none";

export interface ContactInfo {
  name: string;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  links: string[];
}

export interface EducationEntry {
  institution: string;
  degree: string;
  dates?: string | null;
  details?: string | null;
}

export interface ProjectEntry {
  name: string;
  description: string;
  technologies: string[];
  url?: string | null;
}

export interface ExperienceBullet {
  bullet_id: number;
  text: string;
}

export interface ExperienceEntry {
  company: string;
  role: string;
  dates?: string | null;
  bullets: ExperienceBullet[];
}

export interface ParsedResume {
  contact_info: ContactInfo;
  summary?: string | null;
  skills: string[];
  experience: ExperienceEntry[];
  education: EducationEntry[];
  projects: ProjectEntry[];
  achievements?: string[];
  certifications?: string[];
  raw_text: string;
}

export interface RequirementMatch {
  requirement: string;
  importance: ImportanceLevel;
  status: SupportStatus;
  evidence_level?: EvidenceLevel | null;
  evidence_quote?: string | null;
  notes: string;
}

export interface MissingRequirement {
  requirement: string;
  importance: ImportanceLevel;
  guidance: string;
}

export interface MatchAnalysis {
  estimated_score: number;
  scoring_methodology: string;
  disclaimer: string;
  breakdown: RequirementMatch[];
  missing_requirements: MissingRequirement[];
}

export interface TailoredBullet {
  source_bullet_id: number;
  original_text: string;
  tailored_text: string;
  rationale: string;
}

export interface TailoredExperienceEntry {
  company: string;
  role: string;
  dates?: string | null;
  bullets: TailoredBullet[];
}

export interface TailoredSkills {
  retained_relevant: string[];
  retained_other: string[];
}

export interface TailingChange {
  section: string;
  change_type: ChangeType;
  reasoning: string;
}

export interface AuditWarning {
  bullet_ref: string;
  original_text: string;
  tailored_text: string;
  concern: string;
}

export interface TailoredResume {
  contact_info: ContactInfo;
  summary?: string | null;
  skills: TailoredSkills;
  experience: TailoredExperienceEntry[];
  education: EducationEntry[];
  projects: ProjectEntry[];
  achievements?: string[];
  certifications?: string[];
  tailoring_changes: TailingChange[];
  audit_warnings: AuditWarning[];
}

export interface CustomizeResponse {
  match_analysis: MatchAnalysis;
  original_resume: ParsedResume;
  tailored_resume: TailoredResume;
}

export interface ExportPdfRequest {
  tailored_resume: TailoredResume;
}

export interface ErrorDetail {
  code: string;
  message: string;
  details?: unknown;
}

export interface ErrorResponse {
  error: ErrorDetail;
}

export interface HealthResponse {
  status: string;
  version: string;
  model_configured: boolean;
}

export const ErrorCode = {
  INVALID_FILE_TYPE: "INVALID_FILE_TYPE",
  FILE_TOO_LARGE: "FILE_TOO_LARGE",
  ENCRYPTED_OR_CORRUPT_FILE: "ENCRYPTED_OR_CORRUPT_FILE",
  INSUFFICIENT_TEXT_CONTENT: "INSUFFICIENT_TEXT_CONTENT",
  INVALID_JOB_DESCRIPTION: "INVALID_JOB_DESCRIPTION",
  AI_PROVIDER_ERROR: "AI_PROVIDER_ERROR",
  AI_FACTUALITY_REJECTED: "AI_FACTUALITY_REJECTED",
  INTERNAL_ERROR: "INTERNAL_ERROR",
} as const;
