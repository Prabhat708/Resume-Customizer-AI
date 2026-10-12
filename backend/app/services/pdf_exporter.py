"""
app/services/pdf_exporter.py — Professional, ATS-readable Resume PDF generator.

Key Design & ATS Standards:
- Built strictly with ReportLab Platypus (SimpleDocTemplate, Paragraph, Spacer, Table).
- Generates directly from the validated TailoredResume Pydantic schema (never HTML scraping).
- Single-column linear reading order for ATS parsers and text extractors.
- Standard Type 1 fonts (Helvetica, Helvetica-Bold) for universal ATS compatibility and selectable text.
- Comprehensive XML character escaping (prevents ReportLab XML markup injection or parser crashes).
- Robust Unicode character normalization (smart quotes, dashes, bullets, accents).
- Dynamic page layout supporting multi-page resumes without clipping or overlapping.
- Handles missing optional sections cleanly (no orphan headers).
"""
from __future__ import annotations

import io
import re
import unicodedata
from xml.sax.saxutils import escape as sax_escape
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
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
    
    1. Replaces common typographical Unicode entities with Latin equivalents.
    2. Decomposes/normalizes any remaining complex Unicode characters.
    3. Replaces unencodable characters with safe ASCII approximations.
    4. Escapes XML special characters (<, >, &).
    """
    if not text:
        return ""

    s = str(text)
    for src, target in _CHAR_REPLACEMENTS.items():
        s = s.replace(src, target)

    # Normalize unicode to avoid Helvetica Type-1 encoding exceptions
    # Normalize to NFKD to separate accents, then encode to latin-1 or ascii
    try:
        s.encode("latin-1")
    except UnicodeEncodeError:
        # For characters beyond latin-1, attempt NFKD normalization
        normalized = unicodedata.normalize("NFKD", s)
        s = "".join(c for c in normalized if not unicodedata.combining(c))
        # Final fallback: encode ascii with replacement
        s = s.encode("ascii", errors="replace").decode("ascii")

    # SAX escape for XML safe rendering in ReportLab
    return sax_escape(s)


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
            self.setFont("Helvetica", 8)
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
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0F172A"),  # Slate-900
        spaceAfter=3,
    )

    contact_style = ParagraphStyle(
        "ResumeContact",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#334155"),  # Slate-700
        spaceAfter=10,
    )

    section_heading_style = ParagraphStyle(
        "ResumeSectionHeading",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
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
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=4,
    )

    bullet_style = ParagraphStyle(
        "ResumeBullet",
        parent=base_styles["Normal"],
        fontName="Helvetica",
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
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0F172A"),
    )

    entry_subtitle_style = ParagraphStyle(
        "ResumeEntrySubtitle",
        parent=base_styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#475569"),
    )

    entry_date_style = ParagraphStyle(
        "ResumeEntryDate",
        parent=base_styles["Normal"],
        fontName="Helvetica",
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
            role_text = _sanitize_and_escape(exp.role)
            comp_text = _sanitize_and_escape(exp.company)
            date_text = _sanitize_and_escape(exp.dates) if exp.dates else ""

            # Table for header: Left col (Role, Company), Right col (Dates)
            left_p = Paragraph(f"<b>{role_text}</b> — <i>{comp_text}</i>", entry_title_style)
            right_p = Paragraph(date_text, entry_date_style)

            # Two columns: ~75% and 25%
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
                    # Use tailored text as the customized bullet
                    bullet_text = _sanitize_and_escape(b.tailored_text)
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

    # 5. Education (Optional)
    if resume.education:
        add_section_divider("Education")

        for edu in resume.education:
            deg_text = _sanitize_and_escape(edu.degree)
            inst_text = _sanitize_and_escape(edu.institution)
            date_text = _sanitize_and_escape(edu.dates) if edu.dates else ""

            left_p = Paragraph(f"<b>{deg_text}</b> — {inst_text}", entry_title_style)
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
            story.append(edu_table)

            if edu.details:
                details_text = _sanitize_and_escape(edu.details)
                story.append(Paragraph(details_text, entry_subtitle_style))

            story.append(Spacer(1, 3))

    # 6. Projects (Optional)
    if resume.projects:
        add_section_divider("Projects")

        for proj in resume.projects:
            name_text = _sanitize_and_escape(proj.name)
            desc_text = _sanitize_and_escape(proj.description)

            tech_str = ""
            if proj.technologies:
                tech_list = ", ".join(_sanitize_and_escape(t) for t in proj.technologies)
                tech_str = f" | <i>Technologies: {tech_list}</i>"

            url_str = ""
            if proj.url:
                clean_url = _sanitize_and_escape(proj.url)
                url_str = f" ({clean_url})"

            proj_header = f"<b>{name_text}</b>{url_str}{tech_str}"
            story.append(Paragraph(proj_header, entry_title_style))
            story.append(Paragraph(f"&bull;&nbsp;&nbsp;{desc_text}", bullet_style))
            story.append(Spacer(1, 3))

    # Build PDF with multi-page NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()


def get_safe_pdf_filename(name: Optional[str] = None) -> str:
    """
    Returns a deterministic, privacy-conscious filename for the PDF attachment.
    Does not expose sensitive personal info, phone numbers, or arbitrary paths.
    """
    if not name:
        return "tailored_resume.pdf"

    # Extract first name or alpha characters only
    clean = re.sub(r"[^a-zA-Z0-9]", "_", name).strip("_")
    # Take at most the first token / 20 chars
    parts = [p for p in clean.split("_") if p]
    if parts:
        prefix = parts[0].lower()[:20]
        return f"{prefix}_resume_tailored.pdf"
    return "tailored_resume.pdf"
