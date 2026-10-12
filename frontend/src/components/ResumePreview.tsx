"use client";

import React from "react";
import { Mail, Phone, MapPin, Globe, Briefcase, GraduationCap, FolderGit2, Award } from "lucide-react";
import { TailoredResume, TailoredExperienceEntry, EducationEntry, ProjectEntry } from "@/types/api";

interface ResumePreviewProps {
  resume: TailoredResume;
}

export function ResumePreview({ resume }: ResumePreviewProps) {
  const { contact_info, summary, skills, experience, education, projects } = resume;

  return (
    <article className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-10 max-w-4xl mx-auto font-sans text-slate-800 leading-normal">
      {/* 1. Header / Contact Info */}
      <header className="border-b border-slate-200 pb-5 mb-6 text-center sm:text-left">
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          {contact_info.name}
        </h2>

        <div className="flex flex-wrap items-center justify-center sm:justify-start gap-y-1.5 gap-x-4 mt-2.5 text-xs text-slate-600">
          {contact_info.email && (
            <span className="inline-flex items-center space-x-1">
              <Mail className="h-3.5 w-3.5 text-slate-400" />
              <span>{contact_info.email}</span>
            </span>
          )}
          {contact_info.phone && (
            <span className="inline-flex items-center space-x-1">
              <Phone className="h-3.5 w-3.5 text-slate-400" />
              <span>{contact_info.phone}</span>
            </span>
          )}
          {contact_info.location && (
            <span className="inline-flex items-center space-x-1">
              <MapPin className="h-3.5 w-3.5 text-slate-400" />
              <span>{contact_info.location}</span>
            </span>
          )}
          {contact_info.links &&
            contact_info.links.map((link, idx) => (
              <span key={idx} className="inline-flex items-center space-x-1">
                <Globe className="h-3.5 w-3.5 text-slate-400" />
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

      {/* 2. Professional Summary */}
      {summary && (
        <section className="mb-6" aria-labelledby="resume-summary-heading">
          <h3 id="resume-summary-heading" className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center space-x-1.5">
            <span>Professional Summary</span>
          </h3>
          <p className="text-sm text-slate-700 leading-relaxed bg-slate-50/70 p-3.5 rounded-lg border border-slate-100">
            {summary}
          </p>
        </section>
      )}

      {/* 3. Skills Section (Grouped by relevance) */}
      {(skills.retained_relevant.length > 0 || skills.retained_other.length > 0) && (
        <section className="mb-6" aria-labelledby="resume-skills-heading">
          <h3 id="resume-skills-heading" className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center space-x-1.5">
            <Award className="h-3.5 w-3.5 text-indigo-500" />
            <span>Technical &amp; Core Skills</span>
          </h3>

          <div className="space-y-2.5">
            {/* Target-Role Relevant Skills */}
            {skills.retained_relevant.length > 0 && (
              <div>
                <span className="text-xs font-semibold text-indigo-900 block mb-1.5">
                  Highlighted for Target Role:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {skills.retained_relevant.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 text-xs font-medium bg-indigo-50 text-indigo-800 rounded-md border border-indigo-200"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Additional Verified Skills */}
            {skills.retained_other.length > 0 && (
              <div>
                <span className="text-xs font-semibold text-slate-600 block mb-1.5">
                  Additional Background:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {skills.retained_other.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 text-xs text-slate-700 bg-slate-100 rounded-md border border-slate-200"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* 4. Professional Experience */}
      {experience && experience.length > 0 && (
        <section className="mb-6" aria-labelledby="resume-experience-heading">
          <h3 id="resume-experience-heading" className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-1.5">
            <Briefcase className="h-3.5 w-3.5 text-indigo-500" />
            <span>Professional Experience</span>
          </h3>

          <div className="space-y-5">
            {experience.map((entry: TailoredExperienceEntry, idx: number) => (
              <div key={idx} className="space-y-1.5">
                <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">{entry.role}</h4>
                    <p className="text-xs font-semibold text-indigo-700">{entry.company}</p>
                  </div>
                  {entry.dates && (
                    <span className="text-xs text-slate-500 font-mono sm:text-right mt-0.5 sm:mt-0">
                      {entry.dates}
                    </span>
                  )}
                </div>

                {entry.bullets && entry.bullets.length > 0 && (
                  <ul className="list-disc list-outside pl-4 space-y-1.5 mt-2 text-xs sm:text-sm text-slate-700">
                    {entry.bullets.map((bullet, bIdx) => (
                      <li key={bIdx} className="leading-relaxed pl-1">
                        {bullet.tailored_text}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 5. Projects */}
      {projects && projects.length > 0 && (
        <section className="mb-6" aria-labelledby="resume-projects-heading">
          <h3 id="resume-projects-heading" className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-1.5">
            <FolderGit2 className="h-3.5 w-3.5 text-indigo-500" />
            <span>Key Projects</span>
          </h3>

          <div className="space-y-4">
            {projects.map((proj: ProjectEntry, idx: number) => (
              <div key={idx} className="text-xs sm:text-sm space-y-1">
                <div className="flex items-baseline justify-between">
                  <h4 className="font-bold text-slate-900">{proj.name}</h4>
                  {proj.url && (
                    <a
                      href={proj.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-indigo-600 hover:underline"
                    >
                      View Project
                    </a>
                  )}
                </div>
                <p className="text-slate-700 leading-relaxed">{proj.description}</p>
                {proj.technologies && proj.technologies.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-1">
                    {proj.technologies.map((t, tIdx) => (
                      <span key={tIdx} className="px-1.5 py-0.5 text-[10px] bg-slate-100 text-slate-600 rounded">
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 6. Education */}
      {education && education.length > 0 && (
        <section aria-labelledby="resume-education-heading">
          <h3 id="resume-education-heading" className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-1.5">
            <GraduationCap className="h-3.5 w-3.5 text-indigo-500" />
            <span>Education</span>
          </h3>

          <div className="space-y-3">
            {education.map((edu: EducationEntry, idx: number) => (
              <div key={idx} className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between text-xs sm:text-sm">
                <div>
                  <h4 className="font-bold text-slate-900">{edu.degree}</h4>
                  <p className="text-slate-600">{edu.institution}</p>
                  {edu.details && <p className="text-xs text-slate-500 mt-0.5">{edu.details}</p>}
                </div>
                {edu.dates && <span className="text-xs text-slate-500 font-mono mt-0.5 sm:mt-0">{edu.dates}</span>}
              </div>
            ))}
          </div>
        </section>
      )}
    </article>
  );
}
