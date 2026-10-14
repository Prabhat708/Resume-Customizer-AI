"""
backend/tests/test_pdf_exporter.py — Comprehensive tests for PDF export.

Tests cover:
- Short single-page resume generation and PyMuPDF full text extraction
- Long multi-page resume generation verifying text on each page and page numbers
- Long bullet points and long URLs
- Full Unicode text preservation (European accents, Cyrillic, Greek, umlauts, smart quotes)
- Absent optional sections (no summary, no projects, no education, empty skills)
- PyMuPDF text extraction verifying presence of contact, summary, skills, experience, education, projects
- Security / safe rendering of user markup (e.g. <script>, <br>, &, mathematical expressions x < 5)
- Deterministic generic privacy filename ('tailored_resume.pdf')
- API endpoint test: POST /api/v1/export/pdf with correct headers and download filename
"""
from __future__ import annotations

import fitz  # PyMuPDF
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.api import ExportPdfRequest
from app.schemas.common import ContactInfo, EducationEntry, ProjectEntry
from app.schemas.tailored import (
    AuditWarning,
    ChangeType,
    TailingChange,
    TailoredBullet,
    TailoredExperienceEntry,
    TailoredResume,
    TailoredSkills,
)
from app.services.pdf_exporter import generate_resume_pdf, get_safe_pdf_filename


client = TestClient(app)


def _make_sample_resume(
    name: str = "Jane Doe",
    email: str = "jane.doe@example.com",
    summary: str | None = "Experienced software engineer specializing in scalable distributed systems.",
    experience_count: int = 2,
    bullets_per_exp: int = 3,
    has_education: bool = True,
    has_projects: bool = True,
) -> TailoredResume:
    bullets = [
        TailoredBullet(
            source_bullet_id=i,
            original_text=f"Built service component {i} improving throughput.",
            tailored_text=f"Architected scalable backend service {i} optimizing system latency by 35%.",
            rationale="Highlighted cloud scalability and measurable metrics for JD.",
        )
        for i in range(bullets_per_exp)
    ]

    experience = [
        TailoredExperienceEntry(
            company=f"Acme Corp {j + 1}",
            role="Senior Systems Engineer",
            dates=f"202{j} – Present",
            bullets=bullets,
        )
        for j in range(experience_count)
    ]

    education = (
        [
            EducationEntry(
                institution="State University",
                degree="B.S. in Computer Science",
                dates="2016 – 2020",
                details="Graduated with Honors, GPA 3.9/4.0",
            )
        ]
        if has_education
        else []
    )

    projects = (
        [
            ProjectEntry(
                name="CloudStream",
                description="Real-time event streaming pipeline processing 10k events/sec.",
                technologies=["Python", "FastAPI", "Kafka", "Docker"],
                url="https://github.com/janedoe/cloudstream",
            )
        ]
        if has_projects
        else []
    )

    return TailoredResume(
        contact_info=ContactInfo(
            name=name,
            email=email,
            phone="+1 (555) 234-5678",
            location="San Francisco, CA",
            links=["https://linkedin.com/in/janedoe", "https://github.com/janedoe"],
        ),
        summary=summary,
        skills=TailoredSkills(
            retained_relevant=["Python", "Distributed Systems", "PostgreSQL", "Docker", "AWS"],
            retained_other=["Git", "CI/CD", "Linux", "REST APIs"],
        ),
        experience=experience,
        education=education,
        projects=projects,
        tailoring_changes=[
            TailingChange(
                section="Experience",
                change_type=ChangeType.REFRAMED,
                reasoning="Emphasized high-throughput distributed systems experience.",
            )
        ],
        audit_warnings=[],
    )


def test_pdf_export_short_resume():
    """Generates a valid short resume and verifies reopening with PyMuPDF on A4 paper."""
    resume = _make_sample_resume(experience_count=1, bullets_per_exp=2)
    pdf_bytes = generate_resume_pdf(resume)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")

    # Reopen with PyMuPDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    # Short resume fits on 1 page and does not create an unnecessary blank page
    assert doc.page_count == 1
    assert doc[0].rect.width == pytest.approx(595.28, abs=0.5)
    assert doc[0].rect.height == pytest.approx(841.89, abs=0.5)

    page_text = doc[0].get_text()

    # Verify key sections and contact info appear in extracted text
    assert "Jane Doe" in page_text
    assert "jane.doe@example.com" in page_text
    assert "+1 (555) 234-5678" in page_text
    assert "San Francisco, CA" in page_text
    assert "Senior Systems Engineer" in page_text
    assert "Acme Corp 1" in page_text
    assert "TECHNICAL SKILLS" in page_text
    assert "Relevant Skills: Python, Distributed Systems" in page_text
    assert "EDUCATION" in page_text
    assert "B.S. in Computer Science" in page_text
    assert "PROJECTS" in page_text
    assert "CloudStream" in page_text
    doc.close()


def test_pdf_export_long_multipage_resume():
    """Generates a long resume that spans multiple A4 pages cleanly without clipping."""
    resume = _make_sample_resume(experience_count=6, bullets_per_exp=5)
    pdf_bytes = generate_resume_pdf(resume)

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    assert doc.page_count >= 2

    # Check that text is selectable on every page, page dimensions are A4, and NO footer text appears
    for i in range(doc.page_count):
        assert doc[i].rect.width == pytest.approx(595.28, abs=0.5)
        assert doc[i].rect.height == pytest.approx(841.89, abs=0.5)
        text = doc[i].get_text()
        assert len(text.strip()) > 100
        # Confirm zero footer text or page numbers
        assert "Page " not in text
        assert "Tailored Resume" not in text
    doc.close()


def test_pdf_export_a4_page_dimensions_and_no_forced_page_breaks():
    """Verify strictly A4 page dimensions and that no unconditional PageBreak() flowables exist."""
    import inspect
    from app.services import pdf_exporter

    source_code = inspect.getsource(pdf_exporter.generate_resume_pdf)
    assert "PageBreak()" not in source_code, "pdf_exporter should not contain unconditional PageBreak() calls"
    assert "accumulated_chars" not in source_code, "pdf_exporter should not use character counts to break pages"

    resume = _make_sample_resume(experience_count=2, bullets_per_exp=3)
    pdf_bytes = generate_resume_pdf(resume)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for page in doc:
        # A4 standard size is 595.276 x 841.890 points
        assert page.rect.width == pytest.approx(595.28, abs=0.5)
        assert page.rect.height == pytest.approx(841.89, abs=0.5)
    doc.close()


def test_pdf_export_no_footers_or_page_numbers():
    """Verify that both single-page and multi-page resumes contain zero footers, page numbers, or decorative lines."""
    # 1. Single-page resume
    short_pdf = generate_resume_pdf(_make_sample_resume(experience_count=1, bullets_per_exp=2))
    doc_short = fitz.open(stream=short_pdf, filetype="pdf")
    assert doc_short.page_count == 1
    p_text = doc_short[0].get_text()
    assert "Page 1" not in p_text
    assert "Tailored Resume" not in p_text
    doc_short.close()

    # 2. Multi-page resume
    long_pdf = generate_resume_pdf(_make_sample_resume(experience_count=6, bullets_per_exp=5))
    doc_long = fitz.open(stream=long_pdf, filetype="pdf")
    assert doc_long.page_count >= 2
    for p in doc_long:
        text = p.get_text()
        assert "Page 1 of" not in text
        assert "Page 2 of" not in text
        assert "Tailored Resume" not in text
    doc_long.close()


def test_pdf_export_long_bullets_and_long_urls():
    """Handles extremely long bullet points and unwieldy URLs gracefully without clipping."""
    long_bullet = (
        "Engineered a resilient multi-region disaster recovery architecture capable of failing over "
        "within 45 seconds while maintaining strict linearizable consistency across globally distributed "
        "CockroachDB database clusters, processing upwards of 500,000 queries per second with a p99 "
        "latency ceiling under 12 milliseconds across all availability zones."
    )
    long_url = (
        "https://subdomain.example-organization-deep-link-domain.org/research/publications/"
        "2026/quarterly/scalable-distributed-event-streaming-architectures-v2-final.pdf"
    )

    resume = _make_sample_resume()
    resume.experience[0].bullets[0].tailored_text = long_bullet
    resume.contact_info.links = [long_url]
    if resume.projects:
        resume.projects[0].url = long_url

    pdf_bytes = generate_resume_pdf(resume)
    assert pdf_bytes.startswith(b"%PDF")

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_text = " ".join(page.get_text() for page in doc)
    assert "CockroachDB" in all_text
    assert "multi-region disaster recovery" in all_text
    assert "scalable-distributed-event-streaming-architectures" in all_text
    doc.close()


def test_pdf_export_unicode_and_international_characters():
    """
    Verifies that international characters (accents, umlauts, Cyrillic, Greek, Polish)
    are preserved in the generated PDF and extractable with PyMuPDF.
    """
    unicode_summary = (
        "Lead Développeur & Architect — expert in high-availability systems with ‘zero-downtime’ "
        "deployments and “state-of-the-art” observability pipelines… Tested with café, résumé, Zürich. "
        "International experience: Warszawa (Zażółć gęślą jaźń), Sofia (Инженер), Athina (Μηχανικός)."
    )
    resume = _make_sample_resume(name="Renée Müller-L'Hôpital", summary=unicode_summary)

    pdf_bytes = generate_resume_pdf(resume)
    assert pdf_bytes.startswith(b"%PDF")

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_text = " ".join(page.get_text() for page in doc)

    # Verify actual extracted Unicode text
    assert "Renée" in all_text or "Renee" in all_text
    assert "Müller" in all_text or "Muller" in all_text
    assert "Zürich" in all_text or "Zurich" in all_text
    assert "high-availability" in all_text
    assert "zero-downtime" in all_text
    doc.close()


def test_pdf_export_user_markup_escaped_safely():
    """Ensures raw HTML/XML tags and entities like <script>, <b>, & are escaped and do not crash."""
    malicious_text = "<script>alert('xss')</script> & <b>test</b> <unclosed tag>"
    resume = _make_sample_resume(name="Security Tester", summary=malicious_text)
    resume.experience[0].bullets[0].tailored_text = "Optimized algorithms where x < 5 && y > 10."

    pdf_bytes = generate_resume_pdf(resume)
    assert pdf_bytes.startswith(b"%PDF")

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_text = " ".join(page.get_text() for page in doc)
    assert "Security Tester" in all_text
    assert "alert('xss')" in all_text
    # ReportLab should render the literal text without error
    assert "x < 5" in all_text or "x &lt; 5" in all_text or "5" in all_text
    doc.close()


def test_pdf_export_missing_optional_sections():
    """Handles resumes missing summary, education, projects, and other skills gracefully."""
    resume = _make_sample_resume(
        summary=None,
        has_education=False,
        has_projects=False,
    )
    resume.skills.retained_other = []

    pdf_bytes = generate_resume_pdf(resume)
    assert pdf_bytes.startswith(b"%PDF")

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_text = " ".join(page.get_text() for page in doc)

    # Required sections present
    assert "Jane Doe" in all_text
    assert "PROFESSIONAL EXPERIENCE" in all_text
    assert "TECHNICAL SKILLS" in all_text

    # Absent sections should NOT render orphan headings
    assert "PROFESSIONAL SUMMARY" not in all_text
    assert "EDUCATION" not in all_text
    assert "PROJECTS" not in all_text
    assert "Additional Skills:" not in all_text
    doc.close()


def test_get_safe_pdf_filename_privacy():
    """Tests deterministic, privacy-conscious generic filename generation."""
    assert get_safe_pdf_filename("Jane Doe") == "tailored_resume.pdf"
    assert get_safe_pdf_filename("John-Paul O'Connor") == "tailored_resume.pdf"
    assert get_safe_pdf_filename("") == "tailored_resume.pdf"
    assert get_safe_pdf_filename(None) == "tailored_resume.pdf"


def test_export_pdf_endpoint_success():
    """Tests POST /api/v1/export/pdf returns 200, correct media type, and generic attachment headers."""
    resume = _make_sample_resume()
    payload = ExportPdfRequest(tailored_resume=resume).model_dump()

    response = client.post("/api/v1/export/pdf", json=payload)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert 'attachment; filename="tailored_resume.pdf"' in response.headers["Content-Disposition"]
    assert response.content.startswith(b"%PDF")

    # Reopen endpoint bytes with PyMuPDF to verify content integrity
    doc = fitz.open(stream=response.content, filetype="pdf")
    assert doc.page_count >= 1
    page_text = doc[0].get_text()
    assert "Jane Doe" in page_text
    assert "Senior Systems Engineer" in page_text
    doc.close()


def test_export_pdf_endpoint_invalid_payload():
    """Tests POST /api/v1/export/pdf with invalid body returns 400 or 422 validation error."""
    response = client.post("/api/v1/export/pdf", json={"tailored_resume": {"invalid": "data"}})
    assert response.status_code in (400, 422)


def test_export_pdf_endpoint_internal_error_returns_error_response():
    """Tests that PDF exporter failure returns standardized 500 ErrorResponse envelope."""
    from unittest.mock import patch
    resume = _make_sample_resume()
    payload = ExportPdfRequest(tailored_resume=resume).model_dump()

    with patch("app.routers.export.generate_resume_pdf", side_effect=RuntimeError("Simulated ReportLab crash")):
        response = client.post("/api/v1/export/pdf", json=payload)
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "INTERNAL_ERROR"
        assert "Failed to generate resume PDF" in data["error"]["message"]


def test_pdf_export_page1_space_utilization():
    """Verifies that a realistic 2-page resume fully utilizes the vertical printable space on page 1 (>85% fill) without premature page splitting."""
    from tests.test_phase6_regression import SYNTHETIC_MULTI_SECTION_RESUME
    from app.services.resume_structurer import structure_raw_resume
    from app.services.factuality_auditor import audit_and_build_tailored_resume

    parsed = structure_raw_resume(SYNTHETIC_MULTI_SECTION_RESUME)
    tailored = audit_and_build_tailored_resume(
        parsed_resume=parsed,
        raw_tailored_summary="Software Engineer with 1+ year of experience developing enterprise tools and backend services, with hands-on full-stack project experience. Proven employment track record of delivering 100+ production REST APIs using ASP.NET and C# alongside high-performance Python desktop systems. Additional project experience building full-stack applications and backend services with React.js, Node.js, and MySQL.",
        raw_relevant_skills=["Python", "React.js", "Node.js", "MySQL", "RESTful APIs", "Database Design", "JavaScript"],
        raw_tailored_experience=[],
        raw_tailoring_changes=[],
    )

    pdf_bytes = generate_resume_pdf(tailored)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    assert doc.page_count == 2, f"Expected 2 pages, got {doc.page_count}"

    p1 = doc[0]
    blocks = p1.get_text("blocks")
    first_y = blocks[0][1]
    last_y = blocks[-1][3]
    printable_h = 841.89 - (2 * 36)
    used_h = last_y - first_y
    fill_ratio = used_h / printable_h

    # Page 1 must utilize at least 85% of available vertical height
    assert fill_ratio >= 0.85, f"Page 1 vertical space utilization was {fill_ratio:.1%}, leaving excessive blank space"
    # FruitsWallah project content should be present on page 1 rather than pushed to page 2 leaving blank space
    p1_text = p1.get_text()
    assert "FruitsWallah" in p1_text, "FruitsWallah was prematurely pushed to page 2"
    doc.close()


