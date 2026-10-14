"""
app/services/pdf_exporter.py — Professional, ATS-readable Resume PDF generator.

Key Design & ATS Standards:
- Built strictly with ReportLab Platypus (SimpleDocTemplate, Paragraph, Spacer, Table).
- Generates directly from the validated TailoredResume Pydantic schema (never HTML scraping).
- Single-column linear reading order for ATS parsers and text extractors.
- A4 page dimensions (reportlab.lib.pagesizes.A4) with consistent professional margins.
- Content-driven dynamic pagination: zero forced PageBreak() calls; ReportLab calculates rendered height.
- Section headings and entry lead-ins protected with KeepTogether to prevent orphan headings.
- Embedded TrueType Unicode font family (Arial/SegoeUI) when available with Helvetica fallback.
- TrueType embedding preserves international characters (accents, umlauts, Cyrillic, Greek, Polish)
  in extracted text rather than replacing them with lossy ASCII approximations.
- Clean ATS layout: zero footers, page numbering, or decorative footer lines per ATS standards.
- Handles missing optional sections cleanly (no orphan headers or empty spacers).
- Generates deterministic, privacy-conscious filenames.
"""
from __future__ import annotations

import io
import os
import re
import unicodedata
from xml.sax.saxutils import escape as sax_escape
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.tailored import TailoredResume


# ── TrueType Unicode Font Setup ───────────────────────────────────────────────

_UNICODE_FONT_AVAILABLE = False
_REGULAR_FONT = "Helvetica"
_BOLD_FONT = "Helvetica-Bold"
_ITALIC_FONT = "Helvetica-Oblique"
_BOLD_ITALIC_FONT = "Helvetica-Bold"


def _initialize_fonts() -> None:
    """
    Attempts to register TrueType fonts with full Unicode support (e.g. Arial or Segoe UI)
    so European, Cyrillic, Greek, and Latin-extended characters are embedded directly
    and fully preserved upon PDF text extraction.
    Falls back gracefully to Type-1 Helvetica if system TrueType fonts are not found.
    """
    global _UNICODE_FONT_AVAILABLE, _REGULAR_FONT, _BOLD_FONT, _ITALIC_FONT, _BOLD_ITALIC_FONT

    if _UNICODE_FONT_AVAILABLE:
        return

    # Check candidate system font directories (Windows, Linux, macOS)
    candidates = []
    windir = os.environ.get("WINDIR", r"C:\Windows")
    win_fonts = os.path.join(windir, "Fonts")

    candidates.append(
        (
            "ResumeFont",
            os.path.join(win_fonts, "arial.ttf"),
            os.path.join(win_fonts, "arialbd.ttf"),
            os.path.join(win_fonts, "ariali.ttf"),
            os.path.join(win_fonts, "arialbi.ttf"),
        )
    )
    candidates.append(
        (
            "ResumeFont",
            os.path.join(win_fonts, "segoeui.ttf"),
            os.path.join(win_fonts, "segoeuib.ttf"),
            os.path.join(win_fonts, "segoeuii.ttf"),
            os.path.join(win_fonts, "segoeuiz.ttf"),
        )
    )
    # Common Linux paths
    candidates.append(
        (
            "ResumeFont",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
        )
    )

    for font_family, reg_p, bold_p, italic_p, bi_p in candidates:
        if os.path.exists(reg_p) and os.path.exists(bold_p):
            try:
                pdfmetrics.registerFont(TTFont(f"{font_family}", reg_p, "utf-8"))
                pdfmetrics.registerFont(TTFont(f"{font_family}-Bold", bold_p, "utf-8"))

                has_italic = os.path.exists(italic_p)
                has_bi = os.path.exists(bi_p)

                if has_italic:
                    pdfmetrics.registerFont(TTFont(f"{font_family}-Italic", italic_p, "utf-8"))
                else:
                    pdfmetrics.registerFont(TTFont(f"{font_family}-Italic", reg_p, "utf-8"))

                if has_bi:
                    pdfmetrics.registerFont(TTFont(f"{font_family}-BoldItalic", bi_p, "utf-8"))
                else:
                    pdfmetrics.registerFont(TTFont(f"{font_family}-BoldItalic", bold_p, "utf-8"))

                pdfmetrics.registerFontFamily(
                    font_family,
                    normal=f"{font_family}",
                    bold=f"{font_family}-Bold",
                    italic=f"{font_family}-Italic",
                    boldItalic=f"{font_family}-BoldItalic",
                )

                _UNICODE_FONT_AVAILABLE = True
                _REGULAR_FONT = f"{font_family}"
                _BOLD_FONT = f"{font_family}-Bold"
                _ITALIC_FONT = f"{font_family}-Italic"
                _BOLD_ITALIC_FONT = f"{font_family}-BoldItalic"
                break
            except Exception:
                continue


# Initialize font registration
_initialize_fonts()


# ── Character Normalization & Safe XML Escaping ──────────────────────────────

_CHAR_REPLACEMENTS = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2013": "-",
    "\u2014": "--",
    "\u2026": "...",
    "\u2022": "*",
    "\u00a0": " ",  # Non-breaking space
    "\t": " ",
}


def normalize_technology_names(text: Optional[str]) -> Optional[str]:
    """Normalize corrupted dot-spacing in technology names (e.g. 'React. js' -> 'React.js', 'ASP. NET' -> 'ASP.NET')."""
    if not text:
        return text
    text = re.sub(r"\bASP\.\s+NET\b", "ASP.NET", text, flags=re.IGNORECASE)
    text = re.sub(r"\bReact\.\s+js\b", "React.js", text, flags=re.IGNORECASE)
    text = re.sub(r"\bNode\.\s+js\b", "Node.js", text, flags=re.IGNORECASE)
    text = re.sub(r"\bVue\.\s+js\b", "Vue.js", text, flags=re.IGNORECASE)
    text = re.sub(r"\bNext\.\s+js\b", "Next.js", text, flags=re.IGNORECASE)
    return text


def _sanitize_and_escape(text: Optional[str]) -> str:
    """
    Safely sanitizes and escapes raw user text for ReportLab Paragraphs.
    
    1. Normalizes technology names (e.g. ASP.NET, React.js, Node.js).
    2. Replaces common typographical punctuation entities with clean equivalents.
    3. If TrueType Unicode fonts are available, preserves international Unicode characters.
    4. If running under Type-1 Helvetica fallback, normalizes characters to latin-1 / ascii.
    5. Escapes XML special characters (<, >, &).
    """
    if not text:
        return ""

    s = normalize_technology_names(str(text))
    for src, target in _CHAR_REPLACEMENTS.items():
        s = s.replace(src, target)

    if not _UNICODE_FONT_AVAILABLE:
        # Fallback for pure Type-1 Helvetica
        try:
            s.encode("latin-1")
        except UnicodeEncodeError:
            normalized = unicodedata.normalize("NFKD", s)
            s = "".join(c for c in normalized if not unicodedata.combining(c))
            s = s.encode("ascii", errors="replace").decode("ascii")

    # SAX escape for XML safe rendering in ReportLab
    return sax_escape(s)


def _clean_bullet_text(text: str) -> str:
    """Strip any leading bullet symbols or numbered list prefixes without stripping leading numbers that are part of text (e.g. '160 Days of DSA', '3rd place')."""
    if not text:
        return ""
    return re.sub(
        r"^[\s•*–—◦\u25e6\u2022\u25aa\u25cf\u25cb\u25b8\u27a4\u2713\u2714\u2043\u2219]+|^\s*\(?\d+[\.\)]\s*",
        "",
        text,
    ).strip()


class NumberedCanvas(canvas.Canvas):
    """
    Canvas for ATS PDF generation.
    Footer text, separator lines, and page numbers have been completely removed
    to ensure a clean, distraction-free document layout per ATS specifications.
    """
    pass


# ── PDF Exporter Service ──────────────────────────────────────────────────────

def generate_resume_pdf(resume: TailoredResume) -> bytes:
    """
    Generate an ATS-optimized, high-fidelity PDF from the validated TailoredResume schema.
    Uses A4 paper geometry and pure content-driven ReportLab Platypus pagination.
    Returns the raw PDF binary content as bytes.
    """
    _initialize_fonts()
    buffer = io.BytesIO()

    # Geometry: A4 page size (595.28 x 841.89 pt), 36 pt (0.5 in) margins (printable width: 523.28 pt)
    margin = 36
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
        title=f"{resume.contact_info.name} - Resume",
        author=resume.contact_info.name,
    )

    content_width = A4[0] - (2 * margin)

    # Reusable typography styles
    base_styles = getSampleStyleSheet()

    name_style = ParagraphStyle(
        "ResumeName",
        parent=base_styles["Normal"],
        fontName=_BOLD_FONT,
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0F172A"),  # Slate-900
        spaceAfter=2,
    )

    contact_style = ParagraphStyle(
        "ResumeContact",
        parent=base_styles["Normal"],
        fontName=_REGULAR_FONT,
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#334155"),  # Slate-700
        spaceBefore=2,
        spaceAfter=6,
    )

    section_heading_style = ParagraphStyle(
        "ResumeSectionHeading",
        parent=base_styles["Normal"],
        fontName=_BOLD_FONT,
        fontSize=10.5,
        leading=13.5,
        textColor=colors.HexColor("#1E293B"),  # Slate-800
        spaceBefore=0,
        spaceAfter=0,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "ResumeBody",
        parent=base_styles["Normal"],
        fontName=_REGULAR_FONT,
        fontSize=10,
        leading=13.5,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=2.5,
    )

    bullet_style = ParagraphStyle(
        "ResumeBullet",
        parent=base_styles["Normal"],
        fontName=_REGULAR_FONT,
        fontSize=10,
        leading=13.5,
        textColor=colors.HexColor("#1E293B"),
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=2.0,
    )

    entry_title_style = ParagraphStyle(
        "ResumeEntryTitle",
        parent=base_styles["Normal"],
        fontName=_BOLD_FONT,
        fontSize=10.5,
        leading=13.5,
        textColor=colors.HexColor("#0F172A"),
        keepWithNext=True,
    )

    entry_subtitle_style = ParagraphStyle(
        "ResumeEntrySubtitle",
        parent=base_styles["Normal"],
        fontName=_ITALIC_FONT,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
    )

    entry_date_style = ParagraphStyle(
        "ResumeEntryDate",
        parent=base_styles["Normal"],
        fontName=_REGULAR_FONT,
        fontSize=9,
        leading=12,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#475569"),
    )

    def make_section_header(title: str) -> List:
        return [
            Spacer(1, 8),
            Paragraph(title.upper(), section_heading_style),
            HRFlowable(
                width="100%",
                thickness=0.75,
                color=colors.HexColor("#CBD5E1"),  # Slate-300
                spaceBefore=1.5,
                spaceAfter=4,
            ),
        ]

    story = []

    # 1. Contact Header
    name_escaped = _sanitize_and_escape(resume.contact_info.name)
    story.append(Paragraph(name_escaped, name_style))

    contact_parts = []
    if resume.contact_info.email:
        contact_parts.append(_sanitize_and_escape(resume.contact_info.email))
    if resume.contact_info.phone:
        contact_parts.append(_sanitize_and_escape(resume.contact_info.phone))
    if resume.contact_info.location:
        contact_parts.append(_sanitize_and_escape(resume.contact_info.location))
    if resume.contact_info.links:
        for link in resume.contact_info.links:
            clean_link = _sanitize_and_escape(link.replace("https://", "").replace("http://", "").rstrip("/"))
            contact_parts.append(clean_link)

    if contact_parts:
        contact_line = " &nbsp;|&nbsp; ".join(contact_parts)
        story.append(Paragraph(contact_line, contact_style))

    # 2. Professional Summary (Optional)
    if resume.summary and resume.summary.strip():
        summary_escaped = _sanitize_and_escape(resume.summary.strip())
        summary_para = Paragraph(summary_escaped, body_style)
        # Keep section heading together with its summary paragraph
        story.append(KeepTogether(make_section_header("Professional Summary") + [summary_para]))

    # 3. Technical & Core Skills
    has_relevant_skills = bool(resume.skills.retained_relevant)
    has_other_skills = bool(resume.skills.retained_other)

    if has_relevant_skills or has_other_skills:
        skills_flowables = []
        if has_relevant_skills:
            relevant_str = ", ".join(
                _sanitize_and_escape(s) for s in resume.skills.retained_relevant
            )
            skills_flowables.append(
                Paragraph(
                    f"<b>Relevant Skills:</b> {relevant_str}",
                    body_style,
                )
            )
        if has_other_skills:
            other_str = ", ".join(
                _sanitize_and_escape(s) for s in resume.skills.retained_other
            )
            skills_flowables.append(
                Paragraph(
                    f"<b>Additional Skills:</b> {other_str}",
                    body_style,
                )
            )

        if skills_flowables:
            # Keep section heading together with at least the first skill line
            story.append(KeepTogether(make_section_header("Technical Skills") + skills_flowables[:1]))
            for extra_skill in skills_flowables[1:]:
                story.append(extra_skill)

    # 4. Professional Experience
    if resume.experience:
        exp_header = make_section_header("Professional Experience")
        first_exp = True

        for exp in resume.experience:
            exp_elements = []

            # Company, Role, and Dates table row
            role_text = _sanitize_and_escape(exp.role) if exp.role and exp.role.lower() not in ["role", "software engineer - present"] else ""
            comp_text = _sanitize_and_escape(exp.company) if exp.company and exp.company.lower() not in ["organization", "company", "present"] else ""
            date_text = _sanitize_and_escape(exp.dates) if exp.dates else ""

            if role_text and comp_text:
                header_str = f"<b>{role_text}</b> — <i>{comp_text}</i>"
            elif role_text:
                header_str = f"<b>{role_text}</b>"
            elif comp_text:
                header_str = f"<b>{comp_text}</b>"
            else:
                header_str = "<b>Software Engineer</b>"

            left_p = Paragraph(header_str, entry_title_style)
            right_p = Paragraph(date_text, entry_date_style)

            # Two columns: ~72% and 28%
            col1_w = content_width * 0.72
            col2_w = content_width * 0.28
            header_table = Table([[left_p, right_p]], colWidths=[col1_w, col2_w])
            header_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 1),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                    ]
                )
            )
            exp_elements.append(header_table)

            # Bullets
            if exp.bullets:
                for b in exp.bullets:
                    cleaned_b = _clean_bullet_text(b.tailored_text)
                    if cleaned_b:
                        bullet_text = _sanitize_and_escape(cleaned_b)
                        exp_elements.append(
                            Paragraph(f"&bull;&nbsp;&nbsp;{bullet_text}", bullet_style)
                        )

            exp_elements.append(Spacer(1, 5))

            # Keep company header with at least its first bullet point.
            # Allow remaining bullets to flow naturally across page boundaries when necessary.
            keep_chunk = exp_elements[:2]
            flow_chunk = exp_elements[2:]

            if first_exp:
                story.append(KeepTogether(exp_header + keep_chunk))
                for remaining_elem in flow_chunk:
                    story.append(remaining_elem)
                first_exp = False
            else:
                story.append(KeepTogether(keep_chunk))
                for remaining_elem in flow_chunk:
                    story.append(remaining_elem)

    # 5. Key Projects (Optional)
    if resume.projects:
        proj_header = make_section_header("Key Projects")
        first_proj = True

        for proj in resume.projects:
            proj_elements = []
            name_text = _sanitize_and_escape(proj.name) if proj.name and proj.name.lower() != "project" else ""
            desc_text = proj.description

            tech_str = ""
            if proj.technologies:
                tech_list = ", ".join(_sanitize_and_escape(t) for t in proj.technologies)
                tech_str = f" | <i>Technologies: {tech_list}</i>"

            url_str = ""
            if proj.url:
                clean_url = _sanitize_and_escape(proj.url)
                url_str = f" ({clean_url})"

            if name_text:
                proj_header_text = f"<b>{name_text}</b>{url_str}{tech_str}"
                proj_elements.append(Paragraph(proj_header_text, entry_title_style))

            # Split multi-bullet descriptions cleanly
            for line in desc_text.splitlines():
                line_clean = _clean_bullet_text(line.strip())
                if line_clean:
                    proj_elements.append(Paragraph(f"&bull;&nbsp;&nbsp;{_sanitize_and_escape(line_clean)}", bullet_style))

            proj_elements.append(Spacer(1, 5))

            # Keep project heading with at least its first bullet point.
            # Allow remaining bullets to flow naturally so projects split between bullets when necessary
            # without forcing the entire project onto the next page when only part of it needs to move.
            keep_chunk = proj_elements[:2]
            flow_chunk = proj_elements[2:]

            if first_proj:
                story.append(KeepTogether(proj_header + keep_chunk))
                for rem in flow_chunk:
                    story.append(rem)
                first_proj = False
            else:
                story.append(KeepTogether(keep_chunk))
                for rem in flow_chunk:
                    story.append(rem)

    # 6. Education (Optional)
    if resume.education:
        edu_header = make_section_header("Education")
        first_edu = True

        for edu in resume.education:
            deg_text = _sanitize_and_escape(edu.degree)
            inst_text = _sanitize_and_escape(edu.institution) if edu.institution and edu.institution.lower() not in ["educational institution", "institution"] else ""
            date_text = _sanitize_and_escape(edu.dates) if edu.dates else ""

            if deg_text and inst_text:
                header_str = f"<b>{deg_text}</b> — {inst_text}"
            elif deg_text:
                header_str = f"<b>{deg_text}</b>"
            elif inst_text:
                header_str = f"<b>{inst_text}</b>"
            else:
                header_str = ""

            left_p = Paragraph(header_str, entry_title_style)
            right_p = Paragraph(date_text, entry_date_style)

            col1_w = content_width * 0.75
            col2_w = content_width * 0.25
            edu_table = Table([[left_p, right_p]], colWidths=[col1_w, col2_w])
            edu_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 1),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                    ]
                )
            )
            edu_elements = [edu_table]

            if edu.details:
                details_text = _sanitize_and_escape(edu.details)
                edu_elements.append(Paragraph(details_text, entry_subtitle_style))

            edu_elements.append(Spacer(1, 4))

            if first_edu:
                story.append(KeepTogether(edu_header + edu_elements))
                first_edu = False
            else:
                story.append(KeepTogether(edu_elements))

    # 7. Achievements (Optional)
    achievements = getattr(resume, "achievements", None)
    if achievements:
        ach_header = make_section_header("Achievements")
        ach_elements = []
        for ach in achievements:
            ach_clean = _clean_bullet_text(ach.strip())
            if ach_clean:
                ach_elements.append(Paragraph(f"&bull;&nbsp;&nbsp;{_sanitize_and_escape(ach_clean)}", bullet_style))
        ach_elements.append(Spacer(1, 4))

        if ach_elements:
            story.append(KeepTogether(ach_header + ach_elements[:1]))
            for rem in ach_elements[1:]:
                story.append(rem)

    # 8. Certifications (Optional)
    certifications = getattr(resume, "certifications", None)
    if certifications:
        cert_header = make_section_header("Certifications")
        cert_elements = []
        for cert in certifications:
            cert_clean = _clean_bullet_text(cert.strip())
            if cert_clean:
                cert_elements.append(Paragraph(f"&bull;&nbsp;&nbsp;{_sanitize_and_escape(cert_clean)}", bullet_style))
        cert_elements.append(Spacer(1, 4))

        if cert_elements:
            story.append(KeepTogether(cert_header + cert_elements[:1]))
            for rem in cert_elements[1:]:
                story.append(rem)

    # Build PDF on A4 (clean ATS layout with zero footers or page numbers)
    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()


def get_safe_pdf_filename(name: Optional[str] = None) -> str:
    """
    Returns a deterministic, privacy-conscious generic filename for the PDF attachment.
    Standardized to 'tailored_resume.pdf' to prevent leaking candidate identity,
    contact information, or sensitive filesystem paths.
    """
    return "tailored_resume.pdf"
