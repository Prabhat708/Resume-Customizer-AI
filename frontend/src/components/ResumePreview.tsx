"use client";

import React from "react";
import { Mail, Phone, MapPin, Globe, Briefcase, GraduationCap, FolderGit2, Award } from "lucide-react";
import { TailoredResume, TailoredExperienceEntry, EducationEntry, ProjectEntry } from "@/types/api";

interface ResumePreviewProps {
  resume: TailoredResume;
}

function normalizeTechNames(text?: string | null): string {
  if (!text) return "";
  return text
    .replace(/\bASP\.\s+NET\b/gi, "ASP.NET")
    .replace(/\bReact\.\s+js\b/gi, "React.js")
    .replace(/\bNode\.\s+js\b/gi, "Node.js")
    .replace(/\bVue\.\s+js\b/gi, "Vue.js")
    .replace(/\bNext\.\s+js\b/gi, "Next.js");
}

export function ResumePreview({ resume }: ResumePreviewProps) {
  const { contact_info, summary, skills, experience, education, projects, achievements, certifications } = resume;

  // Calculate content volume to align multi-page pagination with ReportLab PDF export
  const totalContentChars =
    (contact_info.name?.length || 0) +
    (summary?.length || 0) +
    skills.retained_relevant.reduce((acc, s) => acc + s.length, 0) +
    skills.retained_other.reduce((acc, s) => acc + s.length, 0) +
    experience.reduce((acc, exp) => acc + exp.bullets.reduce((bAcc, b) => bAcc + b.tailored_text.length, 0), 0) +
    (projects?.reduce((acc, p) => acc + p.description.length, 0) || 0) +
    (education?.reduce((acc, e) => acc + e.degree.length + e.institution.length, 0) || 0) +
    (achievements?.reduce((acc, a) => acc + a.length, 0) || 0) +
    (certifications?.reduce((acc, c) => acc + c.length, 0) || 0);

  const isMultiPage =
    totalContentChars > 2000 &&
    experience.length > 0 &&
    ((projects && projects.length > 0) || (education && education.length > 0));

  // 1. Header / Contact Info Component
  const renderHeader = () => (
    <header className="resume-header border-b border-slate-200 pb-4 print:pb-1.5 mb-5 print:mb-2 text-center sm:text-left">
      <h2 className="text-2xl sm:text-3xl print:text-xl font-extrabold text-slate-900 tracking-tight">
        {contact_info.name}
      </h2>

      <div className="flex flex-wrap items-center justify-center sm:justify-start gap-y-1.5 gap-x-3.5 print:gap-y-0.5 print:gap-x-2 mt-2 print:mt-1 text-xs print:text-[10.5px] text-slate-600">
        {contact_info.email && (
          <span className="inline-flex items-center space-x-1">
            <Mail className="h-3.5 w-3.5 print:h-3 print:w-3 text-slate-400" />
            <span>{contact_info.email}</span>
          </span>
        )}
        {contact_info.phone && (
          <span className="inline-flex items-center space-x-1">
            <Phone className="h-3.5 w-3.5 print:h-3 print:w-3 text-slate-400" />
            <span>{contact_info.phone}</span>
          </span>
        )}
        {contact_info.location && (
          <span className="inline-flex items-center space-x-1">
            <MapPin className="h-3.5 w-3.5 print:h-3 print:w-3 text-slate-400" />
            <span>{contact_info.location}</span>
          </span>
        )}
        {contact_info.links &&
          contact_info.links.map((link, idx) => (
            <span key={idx} className="inline-flex items-center space-x-1">
              <Globe className="h-3.5 w-3.5 print:h-3 print:w-3 text-slate-400" />
              <a
                href={link.startsWith("http") ? link : `https://${link}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 hover:underline"
              >
                {link.replace(/^https?:\/\//, "")}
              </a>
            </span>
          ))}
      </div>
    </header>
  );

  // 2. Summary Component
  const renderSummary = () =>
    summary ? (
      <section className="resume-section mb-5 print:mb-2" aria-labelledby="resume-summary-heading">
        <h3 id="resume-summary-heading" className="resume-section-heading text-xs print:text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2 print:mb-1 border-b border-slate-200 pb-1 print:pb-0.5 flex items-center space-x-1.5">
          <span>Professional Summary</span>
        </h3>
        <p className="resume-entry-body text-xs sm:text-sm print:text-[10.5px] print:leading-[14.5px] text-slate-700 leading-relaxed bg-slate-50/70 p-3 print:p-1.5 rounded-lg border border-slate-100">
          {normalizeTechNames(summary)}
        </p>
      </section>
    ) : null;

  // 3. Skills Component
  const renderSkills = () =>
    skills.retained_relevant.length > 0 || skills.retained_other.length > 0 ? (
      <section className="resume-section mb-5 print:mb-2" aria-labelledby="resume-skills-heading">
        <h3 id="resume-skills-heading" className="resume-section-heading text-xs print:text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2 print:mb-1 border-b border-slate-200 pb-1 print:pb-0.5 flex items-center space-x-1.5">
          <Award className="h-3.5 w-3.5 text-indigo-500 print:hidden" />
          <span>Technical &amp; Core Skills</span>
        </h3>

        <div className="space-y-2 print:space-y-1">
          {skills.retained_relevant.length > 0 && (
            <div>
              <span className="text-[11px] print:text-[10px] font-semibold text-indigo-900 block mb-1 print:mb-0.5">
                Highlighted for Target Role:
              </span>
              <div className="flex flex-wrap gap-1.5 print:gap-1">
                {skills.retained_relevant.map((skill, idx) => (
                  <span
                    key={idx}
                    className="resume-tag px-2 py-0.5 print:px-1 print:py-0 text-xs print:text-[9.5px] font-medium bg-indigo-50 text-indigo-800 rounded-md border border-indigo-200"
                  >
                    {normalizeTechNames(skill)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {skills.retained_other.length > 0 && (
            <div>
              <span className="text-[11px] print:text-[10px] font-semibold text-slate-600 block mb-1 print:mb-0.5">
                Additional Background:
              </span>
              <div className="flex flex-wrap gap-1.5 print:gap-1">
                {skills.retained_other.map((skill, idx) => (
                  <span
                    key={idx}
                    className="resume-tag px-2 py-0.5 print:px-1 print:py-0 text-xs print:text-[9.5px] text-slate-700 bg-slate-100 rounded-md border border-slate-200"
                  >
                    {normalizeTechNames(skill)}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>
    ) : null;

  // 4. Experience Component
  const renderExperience = () =>
    experience && experience.length > 0 ? (
      <section className="resume-section mb-5 print:mb-2" aria-labelledby="resume-experience-heading">
        <h3 id="resume-experience-heading" className="resume-section-heading text-xs print:text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-3 print:mb-1.5 border-b border-slate-200 pb-1 print:pb-0.5 flex items-center space-x-1.5">
          <Briefcase className="h-3.5 w-3.5 text-indigo-500 print:hidden" />
          <span>Professional Experience</span>
        </h3>

        <div className="space-y-4 print:space-y-2">
          {experience.map((entry: TailoredExperienceEntry, idx: number) => {
            const showCompany =
              entry.company &&
              !["organization", "present", "company"].includes(entry.company.toLowerCase().trim());
            return (
              <div key={idx} className="space-y-1.5 print:space-y-0.5 break-inside-avoid">
                <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between">
                  <div>
                    <h4 className="resume-entry-title text-sm print:text-xs font-bold text-slate-900">{entry.role}</h4>
                    {showCompany && (
                      <p className="text-xs print:text-[11px] font-semibold text-indigo-700">{entry.company}</p>
                    )}
                  </div>
                  {entry.dates && (
                    <span className="text-xs print:text-[10px] text-slate-500 font-mono sm:text-right mt-0.5 sm:mt-0">
                      {entry.dates}
                    </span>
                  )}
                </div>

                {entry.bullets && entry.bullets.length > 0 && (
                  <ul className="resume-bullet-list list-disc list-outside pl-4 space-y-1 print:space-y-0.5 mt-1 print:mt-0.5 text-xs sm:text-sm print:text-[10.5px] text-slate-700">
                    {entry.bullets.map((bullet, bIdx) => (
                      <li key={bIdx} className="resume-bullet-text leading-relaxed print:leading-[14.5px] pl-1">
                        {normalizeTechNames(bullet.tailored_text)}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            );
          })}
        </div>
      </section>
    ) : null;

  // 5. Projects Component
  const renderProjects = (items?: ProjectEntry[], title: string = "Key Projects") => {
    const list = items || projects;
    if (!list || list.length === 0) return null;
    return (
      <section className="resume-section mb-5 print:mb-2" aria-labelledby={`resume-${title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-heading`}>
        <h3 id={`resume-${title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-heading`} className="resume-section-heading text-xs print:text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-3 print:mb-1 border-b border-slate-200 pb-1 print:pb-0.5 flex items-center space-x-1.5">
          <FolderGit2 className="h-3.5 w-3.5 text-indigo-500 print:hidden" />
          <span>{title}</span>
        </h3>

        <div className="space-y-3.5 print:space-y-1.5">
          {list.map((proj: ProjectEntry, idx: number) => {
            const showTitle = proj.name && proj.name.toLowerCase().trim() !== "project";
            const descLines = proj.description.split("\n").filter((l) => l.trim());
            return (
              <div key={idx} className="resume-project-item text-xs sm:text-sm print:text-[10.5px] space-y-1 print:space-y-0.5 break-inside-avoid">
                <div className="flex items-baseline justify-between">
                  {showTitle && <h4 className="font-bold text-slate-900 print:text-xs">{proj.name}</h4>}
                  {proj.url && (
                    <a
                      href={proj.url.startsWith("http") ? proj.url : `https://${proj.url}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs print:text-[10px] text-indigo-600 hover:underline"
                    >
                      {proj.url}
                    </a>
                  )}
                </div>
                {descLines.length > 1 ? (
                  <ul className="resume-bullet-list list-disc list-outside pl-4 space-y-1 print:space-y-0.5 text-slate-700">
                    {descLines.map((line, lIdx) => (
                      <li key={lIdx} className="resume-bullet-text leading-relaxed print:leading-[14px] pl-1">
                        {normalizeTechNames(line.replace(/^[\s•*–—◦\u25e6\u2022\u25aa\u25cf\u25cb\u25b8\u27a4\u2713\u2714\u2043\u2219]+|^\s*\(?\d+[\.\)]\s*/, ""))}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="resume-entry-body text-slate-700 leading-relaxed print:leading-[14px]">{normalizeTechNames(proj.description)}</p>
                )}
                {proj.technologies && proj.technologies.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-0.5 print:pt-0">
                    {proj.technologies.map((t, tIdx) => (
                      <span key={tIdx} className="resume-tag px-1.5 py-0.5 print:px-1 print:py-0 text-[10px] print:text-[9px] bg-slate-100 text-slate-600 rounded">
                        {normalizeTechNames(t)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>
    );
  };

  // 6. Education Component
  const renderEducation = () =>
    education && education.length > 0 ? (
      <section className="resume-section mb-5 print:mb-2" aria-labelledby="resume-education-heading">
        <h3 id="resume-education-heading" className="resume-section-heading text-xs print:text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-3 print:mb-1 border-b border-slate-200 pb-1 print:pb-0.5 flex items-center space-x-1.5">
          <GraduationCap className="h-3.5 w-3.5 text-indigo-500 print:hidden" />
          <span>Education</span>
        </h3>

        <div className="space-y-2.5 print:space-y-1">
          {education.map((edu: EducationEntry, idx: number) => {
            const showInstitution =
              edu.institution &&
              !["educational institution", "institution"].includes(edu.institution.toLowerCase().trim());
            return (
              <div key={idx} className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between text-xs sm:text-sm print:text-[10.5px] break-inside-avoid">
                <div>
                  <h4 className="font-bold text-slate-900 print:text-xs">{edu.degree}</h4>
                  {showInstitution && <p className="text-slate-600 print:text-[10.5px]">{edu.institution}</p>}
                  {edu.details && <p className="text-xs print:text-[10px] text-slate-500 mt-0.5">{edu.details}</p>}
                </div>
                {edu.dates && <span className="text-xs print:text-[10px] text-slate-500 font-mono mt-0.5 sm:mt-0">{edu.dates}</span>}
              </div>
            );
          })}
        </div>
      </section>
    ) : null;

  // 7. Achievements Component
  const renderAchievements = () =>
    achievements && achievements.length > 0 ? (
      <section className="resume-section mb-5 print:mb-2" aria-labelledby="resume-achievements-heading">
        <h3 id="resume-achievements-heading" className="resume-section-heading text-xs print:text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2 print:mb-1 border-b border-slate-200 pb-1 print:pb-0.5 flex items-center space-x-1.5">
          <Award className="h-3.5 w-3.5 text-indigo-500 print:hidden" />
          <span>Achievements</span>
        </h3>
        <ul className="resume-bullet-list list-disc list-outside pl-4 space-y-1 print:space-y-0.5 text-xs sm:text-sm print:text-[10.5px] text-slate-700">
          {achievements.map((ach, idx) => (
            <li key={idx} className="resume-bullet-text leading-relaxed print:leading-[14px] pl-1 break-inside-avoid">
              {normalizeTechNames(ach.replace(/^[\s•*–—◦\u25e6\u2022\u25aa\u25cf\u25cb\u25b8\u27a4\u2713\u2714\u2043\u2219]+|^\s*\(?\d+[\.\)]\s*/, ""))}
            </li>
          ))}
        </ul>
      </section>
    ) : null;

  // 8. Certifications Component
  const renderCertifications = () =>
    certifications && certifications.length > 0 ? (
      <section className="resume-section" aria-labelledby="resume-certifications-heading">
        <h3 id="resume-certifications-heading" className="resume-section-heading text-xs print:text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2 print:mb-1 border-b border-slate-200 pb-1 print:pb-0.5 flex items-center space-x-1.5">
          <Award className="h-3.5 w-3.5 text-indigo-500 print:hidden" />
          <span>Certifications</span>
        </h3>
        <ul className="resume-bullet-list list-disc list-outside pl-4 space-y-1 print:space-y-0.5 text-xs sm:text-sm print:text-[10.5px] text-slate-700">
          {certifications.map((cert, idx) => (
            <li key={idx} className="resume-bullet-text leading-relaxed print:leading-[14px] pl-1 break-inside-avoid">
              {normalizeTechNames(cert.replace(/^[\s•*–—◦\u25e6\u2022\u25aa\u25cf\u25cb\u25b8\u27a4\u2713\u2714\u2043\u2219]+|^\s*\(?\d+[\.\)]\s*/, ""))}
            </li>
          ))}
        </ul>
      </section>
    ) : null;

  return (
    <div className="space-y-4 print:space-y-0">
      {/* Top Pagination Status Indicator (Screen Only) */}
      <div className="flex items-center justify-between bg-indigo-50/70 border border-indigo-200/80 rounded-lg px-4 py-2.5 text-xs text-indigo-900 max-w-4xl mx-auto print:hidden">
        <div className="flex items-center space-x-2">
          <span className="font-bold">Resume Layout:</span>
          <span>{isMultiPage ? "2 Pages (Synchronized with PDF Export)" : "1 Page"}</span>
        </div>
        <span className="text-[11px] text-indigo-700 bg-white/90 px-2 py-0.5 rounded border border-indigo-200 font-medium">
          Clean ATS layout &bull; Zero footers
        </span>
      </div>

      {isMultiPage ? (
        <>
          {/* Page 1: Header, Summary, Skills, Experience, Key Projects */}
          <article className="resume-sheet bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8 max-w-4xl mx-auto font-sans text-slate-800 leading-normal print-page-1 print:p-0 print:border-none print:shadow-none print:max-w-none">
            {renderHeader()}
            {renderSummary()}
            {renderSkills()}
            {renderExperience()}
            {renderProjects()}
          </article>

          {/* Visual Page Break Separator (Screen Only) */}
          <div className="flex items-center justify-center my-6 print:hidden text-xs text-slate-400 space-x-3 max-w-4xl mx-auto">
            <div className="h-px bg-slate-200 flex-1"></div>
            <span className="font-medium bg-slate-100 px-3 py-1 rounded-full border border-slate-200">
              Page Break (Page 1 of 2 &rarr; Page 2 of 2)
            </span>
            <div className="h-px bg-slate-200 flex-1"></div>
          </div>

          {/* Page 2: Education, Achievements, Certifications */}
          <article className="resume-sheet bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8 max-w-4xl mx-auto font-sans text-slate-800 leading-normal print-page-2 print:p-0 print:border-none print:shadow-none print:max-w-none">
            {renderEducation()}
            {renderAchievements()}
            {renderCertifications()}
          </article>
        </>
      ) : (
        /* Single-Page Layout for concise resumes */
        <article className="resume-sheet bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8 max-w-4xl mx-auto font-sans text-slate-800 leading-normal print:p-0 print:border-none print:shadow-none print:max-w-none">
          {renderHeader()}
          {renderSummary()}
          {renderSkills()}
          {renderExperience()}
          {renderProjects()}
          {renderEducation()}
          {renderAchievements()}
          {renderCertifications()}
        </article>
      )}
    </div>
  );
}

