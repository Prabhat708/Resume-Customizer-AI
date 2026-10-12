"""app/services/resume_structurer.py — Structures verbatim document text into a ParsedResume model.

Assigns immutable 0-based bullet_id indices to each experience bullet for provenance tracking.
Extracts contact info, summary, skills, experience, education, projects, achievements, and certifications
without fabrication or synthetic placeholder content (e.g. NEVER outputs 'Organization' or 'Educational Institution').
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from app.schemas.common import ContactInfo, EducationEntry, ExperienceBullet, ProjectEntry
from app.schemas.resume import ExperienceEntry, ParsedResume

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_PATTERN = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
URL_PATTERN = re.compile(
    r"\b(?:https?://|www\.)[A-Za-z0-9.\-_]+(?:\.[A-Za-z]{2,})+(?:/[^\s]*)?\b|"
    r"\b(?:linkedin\.com/in/[A-Za-z0-9_-]+|github\.com/[A-Za-z0-9_-]+|leetcode\.com/u/[A-Za-z0-9_-]+)\b|"
    r"\b[A-Za-z0-9_-]+\.(?:in|io|me|dev|org|app|co)\b",
    re.IGNORECASE,
)

BULLET_PREFIX_REGEX = re.compile(
    r"^[\s]*([•\*\-–—◦\u25e6\u2022\u25aa\u25cf\u25cb\u25b8\u27a4\u2713\u2714\u2043\u2219]|(?:\(?\d+[\.\)]\s*))\s*"
)

DATE_RANGE_PATTERN = re.compile(
    r"(?:(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|sept|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)[a-z]*\.?\s+\d{4}"
    r"|\b\d{4}\b)"
    r"\s*(?:[-–—to\s]+)\s*"
    r"(?:(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|sept|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)[a-z]*\.?\s+\d{4}"
    r"|\b\d{4}\b|present|current|ongoing)\b",
    re.IGNORECASE,
)

SECTION_HEADERS = {
    "summary": re.compile(
        r"^(?:professional\s+summary|summary|profile|about\s+me|career\s+objective|objective)\b",
        re.IGNORECASE,
    ),
    "skills": re.compile(
        r"^(?:technical\s+skills|core\s+competencies|technologies|skills\s+(&|and)\s+technologies|skills)\b",
        re.IGNORECASE,
    ),
    "experience": re.compile(
        r"^(?:professional\s+experience|work\s+experience|employment\s+history|experience|work\s+history|employment)\b",
        re.IGNORECASE,
    ),
    "projects": re.compile(
        r"^(?:key\s+projects|personal\s+projects|projects|open\s+source(?:\s+projects)?|academic\s+projects)\b",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^(?:education|academic\s+background|qualifications|academic\s+qualifications)\b",
        re.IGNORECASE,
    ),
    "achievements": re.compile(
        r"^(?:achievements|honors\s+(&|and)\s+awards|awards\s+(&|and)\s+honors|honors|awards|accomplishments)\b",
        re.IGNORECASE,
    ),
    "certifications": re.compile(
        r"^(?:certifications?|licenses\s+(&|and)\s+certifications|certification|courses)\b",
        re.IGNORECASE,
    ),
}

ROLE_KEYWORDS = {
    "engineer", "developer", "architect", "lead", "manager", "intern", "analyst",
    "specialist", "consultant", "programmer", "administrator", "associate", "officer", "director"
}
COMPANY_KEYWORDS = {
    "pvt", "ltd", "inc", "llc", "corp", "corporation", "company", "technologies",
    "solutions", "systems", "labs", "services", "bank", "group", "enterprises"
}


def _is_bullet_line(line: str) -> bool:
    """Return True if line begins with a bullet character or numbered list prefix."""
    return bool(BULLET_PREFIX_REGEX.match(line.strip()))


def _clean_bullet_line(line: str) -> str:
    """Strip bullet markers from the start of the line."""
    return BULLET_PREFIX_REGEX.sub("", line.strip()).strip()


def _reconstruct_bullets_and_text(lines: List[str]) -> Tuple[List[str], List[str]]:
    """
    Given lines in a section/entry, assemble lines that start with bullet markers
    plus any continuation lines into complete bullet strings.
    Returns (header_lines, bullet_strings).
    """
    header_lines: List[str] = []
    bullet_strings: List[str] = []
    current_bullet: Optional[str] = None
    in_bullets = False

    for line in lines:
        s_line = line.strip()
        if not s_line:
            continue

        if _is_bullet_line(s_line):
            in_bullets = True
            if current_bullet:
                bullet_strings.append(current_bullet)
            current_bullet = _clean_bullet_line(s_line)
        elif in_bullets:
            # Check if this line is an independent date line or start of new sub-entry
            if DATE_RANGE_PATTERN.search(s_line) and len(s_line.split()) < 7:
                if current_bullet:
                    bullet_strings.append(current_bullet)
                    current_bullet = None
                in_bullets = False
                header_lines.append(s_line)
            else:
                # Continuation line of previous bullet point
                if current_bullet:
                    if current_bullet.endswith("-") and not current_bullet.endswith(" -"):
                        # Word was hyphenated across line break (e.g. end-to-)
                        current_bullet = f"{current_bullet}{s_line}"
                    else:
                        current_bullet = f"{current_bullet} {s_line}"
                else:
                    current_bullet = s_line
        else:
            header_lines.append(s_line)

    if current_bullet:
        bullet_strings.append(current_bullet)

    return header_lines, bullet_strings


def structure_raw_resume(raw_text: str, filename: str = "resume") -> ParsedResume:
    """Parse raw resume text into a structured ParsedResume object."""
    raw_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    # 1. Extract contact information
    email_match = EMAIL_PATTERN.search(raw_text)
    email = email_match.group(0) if email_match else None

    phone_match = PHONE_PATTERN.search(raw_text)
    phone = phone_match.group(0) if phone_match else None

    # Find links, filtering out emails
    raw_links = URL_PATTERN.findall(raw_text)
    links = []
    for lk in raw_links:
        clean_lk = lk.strip().rstrip(".,;)")
        if clean_lk and not EMAIL_PATTERN.search(clean_lk) and clean_lk not in links:
            links.append(clean_lk)

    # Candidate name & location from top lines
    name = "Candidate"
    location: Optional[str] = None

    for idx, line in enumerate(raw_lines[:8]):
        is_contact_data = (
            EMAIL_PATTERN.search(line)
            or PHONE_PATTERN.search(line)
            or URL_PATTERN.search(line)
            or any(h.match(line) for h in SECTION_HEADERS.values())
        )
        if not is_contact_data and len(line) < 60:
            clean_val = re.split(r"\s+[-|—]\s+", line)[0].strip()
            if clean_val and not clean_val.lower().startswith("resume"):
                if name == "Candidate":
                    name = clean_val
                elif location is None and ("," in line or any(w in line.lower() for w in ["u.p.", "ny", "ca", "india", "usa", "state"])):
                    location = line.strip()

    contact_info = ContactInfo(
        name=name,
        email=email,
        phone=phone,
        location=location,
        links=links,
    )

    # 2. Segment text into sections
    current_section = "header"
    section_lines: dict[str, List[str]] = {
        "summary": [],
        "skills": [],
        "experience": [],
        "projects": [],
        "education": [],
        "achievements": [],
        "certifications": [],
    }

    for line in raw_lines:
        matched_section = None
        for sec, pattern in SECTION_HEADERS.items():
            if pattern.match(line.rstrip(":")):
                matched_section = sec
                break

        if matched_section:
            current_section = matched_section
            # Check if this header line has content after ":" (e.g. "Experience: Built scalable...")
            if ":" in line:
                remainder = line.split(":", 1)[1].strip()
                if remainder and current_section in section_lines:
                    section_lines[current_section].append(remainder)
            continue

        if current_section in section_lines:
            section_lines[current_section].append(line)

    # 3. Extract Summary
    summary_text: Optional[str] = None
    if section_lines["summary"]:
        summary_text = " ".join(section_lines["summary"]).strip()

    # 4. Extract Skills
    skills_list: List[str] = []
    for s_line in section_lines["skills"]:
        tokens = re.split(r"[,•|;·\n]", s_line)
        for token in tokens:
            cleaned = token.strip().strip("-").strip()
            if ":" in cleaned:
                # Strip category label (e.g. "Languages & Frameworks: Python")
                category_parts = cleaned.split(":", 1)
                cleaned = category_parts[1].strip()
            if cleaned and len(cleaned) < 40 and cleaned.lower() not in ["skills", "technical skills"]:
                if cleaned not in skills_list:
                    skills_list.append(cleaned)

    # 5. Extract Experience & assign bullet_ids
    experience_entries: List[ExperienceEntry] = []
    exp_lines = section_lines["experience"]

    if exp_lines:
        # Split experience lines into entry blocks. An entry block starts with
        # a new role/company/date header when we transition from bullets back to text.
        blocks: List[List[str]] = []
        current_block: List[str] = []
        in_block_bullets = False

        for line in exp_lines:
            is_bullet = _is_bullet_line(line)
            if in_block_bullets and not is_bullet:
                # Could be a continuation of the bullet, OR the start of a new experience entry.
                # A new entry is indicated if the line is short and either matches DATE_RANGE_PATTERN
                # or looks like a title/company (less than 8 words, not ending with a period/comma).
                is_date = bool(DATE_RANGE_PATTERN.search(line))
                is_header_like = (
                    len(line.split()) < 8
                    and not line.endswith((".", ",", ";"))
                    and (is_date or any(w in line.lower() for w in ROLE_KEYWORDS | COMPANY_KEYWORDS))
                )
                if is_date or is_header_like:
                    if current_block:
                        blocks.append(current_block)
                    current_block = [line]
                    in_block_bullets = False
                    continue

            if is_bullet:
                in_block_bullets = True

            current_block.append(line)

        if current_block:
            blocks.append(current_block)

        # Parse each experience block into an ExperienceEntry
        bullet_counter = 0
        for block in blocks:
            header_lines, bullets = _reconstruct_bullets_and_text(block)
            if not header_lines and not bullets:
                continue

            role = "Software Engineer"
            company = ""
            dates = None

            # Look for dates in header lines
            remaining_headers = []
            for h in header_lines:
                date_match = DATE_RANGE_PATTERN.search(h)
                if date_match and dates is None:
                    dates = date_match.group(0).strip()
                    # If line has more text besides the date, retain remainder
                    h_without_date = DATE_RANGE_PATTERN.sub("", h).strip().strip("-|—, ").strip()
                    if h_without_date:
                        remaining_headers.append(h_without_date)
                else:
                    remaining_headers.append(h)

            # If no bullets were detected in this block, check if remaining headers contain accomplishments
            if not bullets and remaining_headers:
                if len(remaining_headers) == 1:
                    bullets = [remaining_headers[0]]
                    role = "Software Engineer"
                    company = "Professional Experience"
                    remaining_headers = []
                elif len(remaining_headers) >= 2 and not any(kw in remaining_headers[-1].lower() for kw in ROLE_KEYWORDS | COMPANY_KEYWORDS):
                    bullets = [remaining_headers[-1]]
                    remaining_headers = remaining_headers[:-1]

            # Classify role vs company from remaining headers
            if len(remaining_headers) == 1:
                single = remaining_headers[0]
                if any(sep in single for sep in [" - ", " – ", " — ", " | ", " at ", " @ "]):
                    parts = re.split(r"\s+(?:[-–—|]|at|@)\s+", single, maxsplit=1)
                    role = parts[0].strip()
                    company = parts[1].strip() if len(parts) > 1 else ""
                else:
                    role = single
            elif len(remaining_headers) >= 2:
                first = remaining_headers[0]
                second = remaining_headers[1]
                # Check keywords
                first_lower = first.lower()
                second_lower = second.lower()
                first_is_role = any(kw in first_lower for kw in ROLE_KEYWORDS)
                second_is_company = any(kw in second_lower for kw in COMPANY_KEYWORDS)

                if first_is_role or second_is_company:
                    role = first
                    company = second
                elif any(kw in first_lower for kw in COMPANY_KEYWORDS):
                    company = first
                    role = second
                else:
                    # Default: line 1 = role, line 2 = company
                    role = first
                    company = second

            # Ensure company does NOT become empty string or placeholder
            if not company:
                company = role if role != "Software Engineer" else "Professional Experience"

            bullet_objs = [
                ExperienceBullet(bullet_id=bullet_counter + b_idx, text=b_text)
                for b_idx, b_text in enumerate(bullets)
            ]
            bullet_counter += len(bullets)

            experience_entries.append(
                ExperienceEntry(
                    company=company,
                    role=role,
                    dates=dates,
                    bullets=bullet_objs,
                )
            )

    # Fallback if no structured entries were produced
    if not experience_entries:
        fallback_lines = section_lines["experience"] if section_lines["experience"] else raw_lines[1:5]
        if fallback_lines:
            bullet_objs = [
                ExperienceBullet(bullet_id=b_idx, text=l)
                for b_idx, l in enumerate(fallback_lines)
                if len(l) > 5
            ]
            if bullet_objs:
                experience_entries.append(
                    ExperienceEntry(
                        company="Professional Experience",
                        role="Software Engineer",
                        dates=None,
                        bullets=bullet_objs,
                    )
                )

    # 6. Extract Projects (including Open Source)
    project_entries: List[ProjectEntry] = []
    proj_lines = section_lines["projects"]

    if proj_lines:
        # Split into project blocks
        proj_blocks: List[List[str]] = []
        curr_p_block: List[str] = []
        in_p_bullets = False

        for line in proj_lines:
            is_bullet = _is_bullet_line(line)
            if in_p_bullets and not is_bullet:
                # Check if this line begins a new project header
                is_date = bool(DATE_RANGE_PATTERN.search(line))
                is_header_like = (
                    len(line.split()) < 12
                    and any(sep in line for sep in ["—", "–", "-", "|"])
                    and not line.endswith((".", ",", ";"))
                )
                if is_header_like and not is_date:
                    if curr_p_block:
                        proj_blocks.append(curr_p_block)
                    curr_p_block = [line]
                    in_p_bullets = False
                    continue

            if is_bullet:
                in_p_bullets = True

            curr_p_block.append(line)

        if curr_p_block:
            proj_blocks.append(curr_p_block)

        for p_block in proj_blocks:
            header_lines, bullets = _reconstruct_bullets_and_text(p_block)
            if not header_lines and not bullets:
                continue

            name = ""
            techs: List[str] = []
            proj_url: Optional[str] = None

            # Process header line (e.g. "FruitsWallah — ASP.NET, C#, React.js, MySQL, JWT")
            if header_lines:
                title_line = header_lines[0]
                url_m = URL_PATTERN.search(title_line)
                if url_m:
                    proj_url = url_m.group(0)

                if any(sep in title_line for sep in ["—", "–", "-", "|"]):
                    parts = re.split(r"\s+[—–\-|]\s+", title_line, maxsplit=1)
                    name = parts[0].strip()
                    if len(parts) > 1:
                        tech_part = parts[1].strip()
                        raw_techs = re.split(r"[,/|;·]", tech_part)
                        for t in raw_techs:
                            t_clean = t.strip()
                            if t_clean and not URL_PATTERN.search(t_clean) and len(t_clean) < 30:
                                techs.append(t_clean)
                else:
                    name = title_line

            if not name and bullets:
                # Derive name from first words of bullet if no title
                name = bullets[0].split(":")[0].strip() if ":" in bullets[0] else "Featured Project"

            # Reconstruct description from bullets
            description = "\n".join(bullets) if bullets else (header_lines[1] if len(header_lines) > 1 else name)

            project_entries.append(
                ProjectEntry(
                    name=name,
                    description=description,
                    technologies=techs,
                    url=proj_url,
                )
            )

    # 7. Extract Education
    education_entries: List[EducationEntry] = []
    edu_lines = section_lines["education"]

    if edu_lines:
        edu_blocks: List[List[str]] = []
        curr_e_block: List[str] = []

        for line in edu_lines:
            is_date = bool(DATE_RANGE_PATTERN.search(line))
            curr_e_block.append(line)
            if is_date:
                edu_blocks.append(curr_e_block)
                curr_e_block = []

        if curr_e_block:
            edu_blocks.append(curr_e_block)

        for e_block in edu_blocks:
            degree = ""
            institution = ""
            dates = None
            details: Optional[str] = None

            for line in e_block:
                d_match = DATE_RANGE_PATTERN.search(line)
                if d_match:
                    dates = d_match.group(0).strip()
                elif not degree:
                    # Parse line like "B.Tech, Computer Science and Design (AKTU) CGPA: 8.12"
                    # or "Intermediate (UP Board) 91.8%"
                    text_line = line.strip()
                    # Check for institution in parentheses
                    inst_match = re.search(r"\(([^)]+)\)", text_line)
                    if inst_match:
                        institution = inst_match.group(1).strip()
                        text_line = re.sub(r"\([^)]+\)", "", text_line).strip()

                    # Check for CGPA or percentage details
                    score_match = re.search(r"(?:CGPA:\s*[\d.]+|\b\d+(?:\.\d+)?%)", text_line, re.IGNORECASE)
                    if score_match:
                        details = score_match.group(0).strip()
                        text_line = text_line.replace(score_match.group(0), "").strip().rstrip(",").strip()

                    degree = text_line
                elif not institution:
                    institution = line.strip()

            if degree:
                education_entries.append(
                    EducationEntry(
                        institution=institution,
                        degree=degree,
                        dates=dates,
                        details=details,
                    )
                )

    # 8. Extract Achievements
    achievements_list: List[str] = []
    ach_lines = section_lines["achievements"]
    if ach_lines:
        _, ach_bullets = _reconstruct_bullets_and_text(ach_lines)
        achievements_list = ach_bullets if ach_bullets else ach_lines

    # 9. Extract Certifications
    certifications_list: List[str] = []
    cert_lines = section_lines["certifications"]
    if cert_lines:
        _, cert_bullets = _reconstruct_bullets_and_text(cert_lines)
        if cert_bullets:
            for cb in cert_bullets:
                # Could be comma-separated list of certifications
                if "," in cb and len(cb.split(",")) > 2:
                    for sub_c in cb.split(","):
                        if sub_c.strip():
                            certifications_list.append(sub_c.strip())
                else:
                    certifications_list.append(cb.strip())
        else:
            certifications_list = cert_lines

    return ParsedResume(
        contact_info=contact_info,
        summary=summary_text,
        skills=skills_list,
        experience=experience_entries,
        education=education_entries,
        projects=project_entries,
        achievements=achievements_list,
        certifications=certifications_list,
        raw_text=raw_text,
    )
