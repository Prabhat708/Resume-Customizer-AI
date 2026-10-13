"""
app/services/pdf_exporter.py — Professional, ATS-readable Resume PDF generator.

Key Design & ATS Standards:
- Built strictly with ReportLab Platypus (SimpleDocTemplate, Paragraph, Spacer, Table).
- Generates directly from the validated TailoredResume Pydantic schema (never HTML scraping).
- Single-column linear reading order for ATS parsers and text extractors.
- Embedded TrueType Unicode font family (Arial/SegoeUI) when available with Helvetica fallback.
- TrueType embedding preserves international characters (accents, umlauts, Cyrillic, Greek, Polish)
  in extracted text rather than replacing them with lossy ASCII approximations.
- Comprehensive XML character escaping (prevents ReportLab XML markup injection or parser crashes).
- Dynamic page layout supporting multi-page resumes without clipping or overlapping.
- Handles missing optional sections cleanly (no orphan headers).
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
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
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


def _sanitize_and_escape(text: Optional[str]) -> str:
    """
    Safely sanitizes and escapes raw user text for ReportLab Paragraphs.
    
    1. Replaces common typographical punctuation entities with clean equivalents.
    2. If TrueType Unicode fonts are available, preserves international Unicode characters.
    3. If running under Type-1 Helvetica fallback, normalizes characters to latin-1 / ascii.
    4. Escapes XML special characters (<, >, &).
    """
    if not text:
        return ""

    s = str(text)
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
    Two-pass canvas to dynamically compute and render 'Page X of Y' footers
    cleanly when multi-page documents are generated.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count: int):
        # Only show page numbers if document spans more than 1 page
        if page_count > 1:
            self.saveState()
            self.setFont(_REGULAR_FONT, 8)
            self.setFillColor(colors.HexColor("#64748B"))  # Slate-500
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(letter[0] - 36, 20, page_text)
            self.restoreState()


# ── PDF Exporter Service ──────────────────────────────────────────────────────

def generate_resume_pdf(resume: TailoredResume) -> bytes:
    """
    Generate an ATS-optimized, high-fidelity PDF from the validated TailoredResume schema.
    Returns the raw PDF binary content as bytes.
    """
    _initialize_fonts()
    buffer = io.BytesIO()

    # Geometry: Letter size, 0.5 in (36 pt) side margins, 0.5 in (36 pt) top/bottom
    margin = 36
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
        title=f"{resume.contact_info.name} - Resume",
        author=resume.contact_info.name,
    )

    content_width = letter[0] - (2 * margin)

    # Styles
    base_styles = getSampleStyleSheet()

    name_style = ParagraphStyle(
        "ResumeName",
        parent=base_styles["Normal"],
        fontName=_BOLD_FONT,
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0F172A"),  # Slate-900
        spaceAfter=3,
    )

    contact_style = ParagraphStyle(
        "ResumeContact",
        parent=base_styles["Normal"],
        fontName=_REGULAR_FONT,
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#334155"),  # Slate-700
        spaceAfter=10,
    )

    section_heading_style = ParagraphStyle(
        "ResumeSectionHeading",
        parent=base_styles["Normal"],
        fontName=_BOLD_FONT,
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor("#1E293B"),  # Slate-800
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "ResumeBody",
        parent=base_styles["Normal"],
        fontName=_REGULAR_FONT,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=4,
    )

    bullet_style = ParagraphStyle(
        "ResumeBullet",
        parent=base_styles["Normal"],
        fontName=_REGULAR_FONT,
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1E293B"),
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=2.5,
    )

    entry_title_style = ParagraphStyle(
        "ResumeEntryTitle",
        parent=base_styles["Normal"],
        fontName=_BOLD_FONT,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0F172A"),
    )

    entry_subtitle_style = ParagraphStyle(
        "ResumeEntrySubtitle",
        parent=base_styles["Normal"],
        fontName=_ITALIC_FONT,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#475569"),
    )

    entry_date_style = ParagraphStyle(
        "ResumeEntryDate",
        parent=base_styles["Normal"],
        fontName=_REGULAR_FONT,
        fontSize=8.5,
        leading=11,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#475569"),
    )

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

    def add_section_divider(heading_text: str):
        story.append(Spacer(1, 4))
        story.append(Paragraph(heading_text.upper(), section_heading_style))
        story.append(
            HRFlowable(
                width="100%",
                thickness=0.75,
                color=colors.HexColor("#CBD5E1"),  # Slate-300
                spaceBefore=1,
                spaceAfter=5,
            )
        )

    # 2. Professional Summary (Optional)
    if resume.summary and resume.summary.strip():
        add_section_divider("Professional Summary")
        summary_escaped = _sanitize_and_escape(resume.summary.strip())
        story.append(Paragraph(summary_escaped, body_style))

    # 3. Technical & Core Skills
    has_relevant_skills = bool(resume.skills.retained_relevant)
    has_other_skills = bool(resume.skills.retained_other)

    if has_relevant_skills or has_other_skills:
        add_section_divider("Technical Skills")
        if has_relevant_skills:
            relevant_str = ", ".join(
                _sanitize_and_escape(s) for s in resume.skills.retained_relevant
            )
            story.append(
                Paragraph(
                    f"<b>Relevant Skills:</b> {relevant_str}",
                    body_style,
                )
            )
        if has_other_skills:
            other_str = ", ".join(
                _sanitize_and_escape(s) for s in resume.skills.retained_other
            )
            story.append(
                Paragraph(
                    f"<b>Additional Skills:</b> {other_str}",
                    body_style,
                )
            )

    # 4. Professional Experience
    if resume.experience:
        add_section_divider("Professional Experience")

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
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
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

            exp_elements.append(Spacer(1, 4))
            # Keep company header with at least its first bullet point
            if len(exp_elements) > 2:
                story.append(KeepTogether(exp_elements[:2]))
                for remaining_elem in exp_elements[2:]:
                    story.append(remaining_elem)
            else:
                story.append(KeepTogether(exp_elements))

    # Calculate content volume and Page 1 accumulated content to determine balanced pagination
    base_p1_chars = (
        len(resume.contact_info.name or "")
        + len(resume.summary or "")
        + sum(len(s) for s in (resume.skills.retained_relevant + resume.skills.retained_other))
        + sum(len(b.tailored_text) for exp in resume.experience for b in exp.bullets)
        + sum(len(exp.role) + len(exp.company or "") for exp in resume.experience)
    )

    total_content_chars = (
        base_p1_chars
        + sum(len(p.description) + len(p.name or "") for p in (resume.projects or []))
        + sum(len(e.degree) + len(e.institution) for e in (resume.education or []))
        + sum(len(a) for a in (getattr(resume, "achievements", None) or []))
        + sum(len(c) for c in (getattr(resume, "certifications", None) or []))
    )

    is_multipage = (
        total_content_chars > 2000
        and len(resume.experience) > 0
        and (len(resume.projects or []) > 0 or len(resume.education or []) > 0)
    )

    # If Experience alone fills Page 1 comfortably (>= 1650 chars) or there are no projects,
    # insert page break here. Otherwise, allow Key Projects to start on Page 1 to avoid empty voids.
    page_has_broken = False
    if is_multipage and (base_p1_chars >= 1650 or not resume.projects):
        story.append(PageBreak())
        page_has_broken = True

    # 5. Projects (Optional)
    if resume.projects:
        add_section_divider("Key Projects")
        accumulated_chars = base_p1_chars

        for idx, proj in enumerate(resume.projects):
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
                proj_header = f"<b>{name_text}</b>{url_str}{tech_str}"
                proj_elements.append(Paragraph(proj_header, entry_title_style))

            # Split multi-bullet descriptions cleanly
            for line in desc_text.splitlines():
                line_clean = _clean_bullet_text(line.strip())
                if line_clean:
                    proj_elements.append(Paragraph(f"&bull;&nbsp;&nbsp;{_sanitize_and_escape(line_clean)}", bullet_style))
            proj_elements.append(Spacer(1, 3))
            story.append(KeepTogether(proj_elements))

            accumulated_chars += len(proj.description) + len(proj.name or "")
            # If multi-page and we haven't broken yet, break when Page 1 reaches balanced capacity (~1,650+ content chars)
            # and there are remaining projects to continue seamlessly on Page 2
            if (
                is_multipage
                and not page_has_broken
                and accumulated_chars >= 1650
                and idx < len(resume.projects) - 1
            ):
                story.append(PageBreak())
                add_section_divider("Key Projects (Continued)")
                page_has_broken = True

    # If multi-page and page has not broken yet before Education/Achievements/Certifications
    if (
        is_multipage
        and not page_has_broken
        and (resume.education or getattr(resume, "achievements", None) or getattr(resume, "certifications", None))
    ):
        story.append(PageBreak())
        page_has_broken = True

    # 6. Education (Optional)
    if resume.education:
        add_section_divider("Education")

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

            edu_elements.append(Spacer(1, 3))
            story.append(KeepTogether(edu_elements))

    # 7. Achievements (Optional)
    achievements = getattr(resume, "achievements", None)
    if achievements:
        add_section_divider("Achievements")
        for ach in achievements:
            ach_clean = _clean_bullet_text(ach.strip())
            if ach_clean:
                story.append(Paragraph(f"&bull;&nbsp;&nbsp;{_sanitize_and_escape(ach_clean)}", bullet_style))
        story.append(Spacer(1, 3))

    # 8. Certifications (Optional)
    certifications = getattr(resume, "certifications", None)
    if certifications:
        add_section_divider("Certifications")
        for cert in certifications:
            cert_clean = _clean_bullet_text(cert.strip())
            if cert_clean:
                story.append(Paragraph(f"&bull;&nbsp;&nbsp;{_sanitize_and_escape(cert_clean)}", bullet_style))
        story.append(Spacer(1, 3))

    # Build PDF with multi-page NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()


def get_safe_pdf_filename(name: Optional[str] = None) -> str:
    """
    Returns a deterministic, privacy-conscious generic filename for the PDF attachment.
    Standardized to 'tailored_resume.pdf' to prevent leaking candidate identity,
    contact information, or sensitive filesystem paths.
    """
    return "tailored_resume.pdf"
