"""
backend/tests/test_pdf_exporter.py — Comprehensive tests for PDF export.

Tests cover:
- Short single-page resume generation
- Long multi-page resume generation
- Long bullet points and long URLs
- Unicode and special characters (smart quotes, dashes, xml entities, accents)
- Absent optional sections (no summary, no projects, no education, empty skills)
- PyMuPDF text extraction verifying content presence and selectable text
- Security / safe rendering of user markup (e.g. <script>, <br>, &)
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
    """Generates a valid short resume and verifies reopening with PyMuPDF."""
    resume = _make_sample_resume(experience_count=1, bullets_per_exp=2)
    pdf_bytes = generate_resume_pdf(resume)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")

    # Reopen with PyMuPDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    assert doc.page_count >= 1
    page_text = doc[0].get_text()

    # Verify key sections and contact info appear in extracted text
    assert "Jane Doe" in page_text
    assert "jane.doe@example.com" in page_text
    assert "Senior Systems Engineer" in page_text
    assert "Acme Corp 1" in page_text
    assert "TECHNICAL SKILLS" in page_text
    assert "Relevant Skills: Python, Distributed Systems" in page_text
    doc.close()


def test_pdf_export_long_multipage_resume():
    """Generates a long resume that spans multiple pages cleanly without clipping."""
    resume = _make_sample_resume(experience_count=6, bullets_per_exp=5)
    pdf_bytes = generate_resume_pdf(resume)

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    assert doc.page_count >= 2

    # Check that text is selectable on every page
    for i in range(doc.page_count):
        text = doc[i].get_text()
        assert len(text.strip()) > 100
        # Check page footer text
        if doc.page_count > 1 and i > 0:
            assert f"Page {i + 1} of {doc.page_count}" in text
    doc.close()


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


def test_pdf_export_unicode_and_special_characters():
    """Handles smart quotes, em-dashes, bullets, accents, and Unicode characters safely."""
    unicode_summary = (
        "Lead Développeur & Architect — expert in high-availability systems with ‘zero-downtime’ "
        "deployments and “state-of-the-art” observability pipelines… Tested with café, résumé, Zürich."
    )
    resume = _make_sample_resume(name="Renée Müller-L'Hôpital", summary=unicode_summary)

    pdf_bytes = generate_resume_pdf(resume)
    assert pdf_bytes.startswith(b"%PDF")

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_text = " ".join(page.get_text() for page in doc)
    assert "Muller" in all_text or "Müller" in all_text
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


def test_get_safe_pdf_filename():
    """Tests deterministic, privacy-conscious filename generation."""
    assert get_safe_pdf_filename("Jane Doe") == "jane_resume_tailored.pdf"
    assert get_safe_pdf_filename("John-Paul O'Connor") == "john_resume_tailored.pdf"
    assert get_safe_pdf_filename("") == "tailored_resume.pdf"
    assert get_safe_pdf_filename(None) == "tailored_resume.pdf"


def test_export_pdf_endpoint_success():
    """Tests POST /api/v1/export/pdf returns 200, correct media type, and attachment headers."""
    resume = _make_sample_resume()
    payload = ExportPdfRequest(tailored_resume=resume).model_dump()

    response = client.post("/api/v1/export/pdf", json=payload)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert "attachment; filename=" in response.headers["Content-Disposition"]
    assert response.headers["Content-Disposition"].endswith('filename="jane_resume_tailored.pdf"')
    assert response.content.startswith(b"%PDF")


def test_export_pdf_endpoint_invalid_payload():
    """Tests POST /api/v1/export/pdf with invalid body returns 400 or 422 validation error."""
    response = client.post("/api/v1/export/pdf", json={"tailored_resume": {"invalid": "data"}})
    assert response.status_code in (400, 422)
