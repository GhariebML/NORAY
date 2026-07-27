"""
NORAY — Certificate Parser

Parse certificates, diplomas, and transcripts from PDF/images.
Uses OCR for image-based certificates when pytesseract is available.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from noray.shared.models import CareerProfile, Certification, Education

# ─── Public API ───────────────────────────────────────────────

def parse_certificate(file_path: Path) -> dict[str, Any]:
    """
    Parse a certificate file and extract structured data.
    
    Supports: PDF (.pdf), Images (.png, .jpg, .jpeg, .webp)
    
    Returns:
        Dict with raw_text, structured fields, source, and file path.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Certificate file not found: {file_path}")

    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        raw_text = _extract_from_pdf(file_path)
    elif suffix in (".png", ".jpg", ".jpeg", ".webp"):
        raw_text = _extract_from_image(file_path)
    else:
        raise ValueError(f"Unsupported certificate format: {suffix}")

    structured = _extract_certificate_fields(raw_text)

    return {
        "raw_text": raw_text,
        "structured": structured,
        "source": f"certificate_{suffix.lstrip('.')}",
        "file": str(file_path),
    }


def import_certificates_to_profile(directory: Path, profile: CareerProfile) -> CareerProfile:
    """
    Scan a directory for certificate files and add them to the profile.
    
    Processes all PDF and image files in the directory.
    Skips .gitkeep and other non-document files.
    """
    if not directory.exists():
        return profile

    existing_certs = {(c.name.lower(), c.issuer.lower()) for c in profile.certifications}
    existing_edu = {(e.institution.lower(), e.degree.lower()) for e in profile.education}
    processed = 0

    for file_path in sorted(directory.iterdir()):
        if file_path.name.startswith(".") or file_path.name == ".gitkeep":
            continue
        if file_path.suffix.lower() not in (".pdf", ".png", ".jpg", ".jpeg", ".webp"):
            continue

        try:
            parsed = parse_certificate(file_path)
            structured = parsed["structured"]

            # If it looks like a diploma/degree certificate → add to education
            if structured.get("is_degree") and structured.get("institution"):
                key = (structured["institution"].lower(), structured.get("degree", "").lower())
                if key not in existing_edu:
                    profile.education.append(Education(
                        degree=structured.get("degree", ""),
                        field=structured.get("field", ""),
                        institution=structured["institution"],
                        end_year=structured.get("year", 0),
                    ))
                    existing_edu.add(key)

            # Otherwise → add to certifications
            elif structured.get("name"):
                cert_key = (structured["name"].lower(), structured.get("issuer", "").lower())
                if cert_key not in existing_certs:
                    profile.certifications.append(Certification(
                        name=structured["name"],
                        issuer=structured.get("issuer", ""),
                        date=structured.get("date", ""),
                        hours=structured.get("hours", 0),
                        credential_url=structured.get("credential_url", ""),
                    ))
                    existing_certs.add(cert_key)

            processed += 1

        except Exception:
            # Skip files that can't be parsed
            continue

    if processed > 0 and "certificate_import" not in profile.meta.sources:
        profile.meta.sources.append("certificate_import")

    return profile


# ─── Text Extraction ──────────────────────────────────────────

def _extract_from_pdf(file_path: Path) -> str:
    """Extract text from a PDF certificate."""
    try:
        import pdfplumber
        with pdfplumber.open(str(file_path)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
            return "\n\n".join(pages)
    except ImportError:
        pass

    try:
        import fitz
        doc = fitz.open(str(file_path))
        text = "\n\n".join(page.get_text() for page in doc)
        doc.close()
        return text
    except ImportError:
        pass

    raise ImportError(
        "No PDF library available. Install:\n"
        "  pip install pdfplumber  OR  pip install pymupdf"
    )


def _extract_from_image(file_path: Path) -> str:
    """Extract text from an image certificate using OCR."""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(str(file_path))
        text = pytesseract.image_to_string(img)
        if text.strip():
            return text
    except ImportError:
        pass

    # If OCR fails or isn't available, return filename as hint
    return f"[Image certificate: {file_path.name}]"


# ─── Field Extraction ─────────────────────────────────────────

def _extract_certificate_fields(text: str) -> dict[str, Any]:
    """
    Extract structured fields from certificate text.
    
    Handles common certificate formats:
    - University diplomas
    - Online course certificates (Coursera, edX, Udemy, etc.)
    - Professional certifications (AWS, Google, Microsoft, etc.)
    """
    result = {
        "name": "",
        "issuer": "",
        "date": "",
        "year": 0,
        "hours": 0,
        "credential_url": "",
        "credential_id": "",
        "is_degree": False,
        "degree": "",
        "field": "",
        "institution": "",
    }

    text_lower = text.lower()

    # ── Detect if it's a degree certificate ──
    degree_keywords = [
        "bachelor", "master", "doctor", "phd", "bsc", "msc", "ba", "ma",
        "diploma", "degree", "graduated", "conferred", "awarded the degree",
    ]
    result["is_degree"] = any(kw in text_lower for kw in degree_keywords)

    if result["is_degree"]:
        result.update(_extract_degree_fields(text))
        return result

    # ── Extract certificate name ──
    # Look for "Certificate of Completion", "Certificate of Achievement", etc.
    cert_name_patterns = [
        r"certificate\s+of\s+(?:completion|achievement|attendance|excellence|participation)",
        r"(?:this\s+is\s+to\s+certify|certified\s+that)",
        r"(?:course|program|training)\s*(?:name|title)[:\s]+(.+)",
    ]
    for pattern in cert_name_patterns:
        match = re.search(pattern, text_lower)
        if match:
            if match.groups():
                result["name"] = match.group(1).strip().title()
            else:
                result["name"] = match.group(0).strip().title()
            break

    # If no name found, use first substantial line
    if not result["name"]:
        lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 5]
        for line in lines[:5]:
            if not re.match(r"^(certificate|this|to|for|the)\b", line.lower()):
                result["name"] = line[:100]
                break

    # ── Extract issuer ──
    issuer_patterns = [
        r"(?:issued|presented|awarded)\s+by[:\s]+(.+)",
        r"(?:from|by)\s+(.+?)(?:\s+on\s+|\s+in\s+|\s*$)",
        r"(?:coursera|edx|udemy|google|microsoft|aws|amazon|meta|ibm|oracle|cisco|hubspot|salesforce)",
        r"(?:university|institute|college|academy|school)\s+of\s+(.+?)(?:\s*\n|\s*$)",
    ]
    for pattern in issuer_patterns:
        match = re.search(pattern, text_lower)
        if match:
            if match.groups():
                result["issuer"] = match.group(1).strip().title()
            else:
                result["issuer"] = match.group(0).strip().title()
            break

    # Known issuers
    known_issuers = {
        "coursera": "Coursera",
        "edx": "edX",
        "udemy": "Udemy",
        "google": "Google",
        "microsoft": "Microsoft",
        "aws": "Amazon Web Services",
        "amazon": "Amazon Web Services",
        "meta": "Meta",
        "ibm": "IBM",
        "oracle": "Oracle",
        "cisco": "Cisco",
        "hubspot": "HubSpot",
        "salesforce": "Salesforce",
        "linkedin": "LinkedIn Learning",
    }
    for key, name in known_issuers.items():
        if key in text_lower:
            result["issuer"] = name
            break

    # ── Extract date ──
    date_patterns = [
        r"(?:issued|completed|dated|on)[:\s]+((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})",
        r"(?:issued|completed|dated|on)[:\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        r"(?:issued|completed|dated|on)[:\s]+(\w+\s+\d{4})",
        r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})",
        r"(\d{4})",  # Just a year
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["date"] = match.group(1).strip()
            year_match = re.search(r"(\d{4})", result["date"])
            if year_match:
                result["year"] = int(year_match.group(1))
            break

    # ── Extract hours ──
    hours_match = re.search(r"(\d+)\s*(?:hours?|hrs?|contact\s+hours?|credit\s+hours?)", text_lower)
    if hours_match:
        result["hours"] = int(hours_match.group(1))

    # ── Extract credential URL ──
    url_match = re.search(r"(https?://[^\s]+)", text)
    if url_match:
        result["credential_url"] = url_match.group(1)

    # ── Extract credential ID ──
    id_patterns = [
        r"(?:credential|certificate|verification)\s*(?:id|number|#)[:\s]+([A-Za-z0-9\-]+)",
        r"(?:id)[:\s]+([A-Za-z0-9]{8,})",
    ]
    for pattern in id_patterns:
        match = re.search(pattern, text_lower)
        if match:
            result["credential_id"] = match.group(1).strip()
            break

    return result


def _extract_degree_fields(text: str) -> dict[str, Any]:
    """Extract degree-specific fields from a diploma/transcript."""
    result = {
        "name": "",
        "issuer": "",
        "date": "",
        "year": 0,
        "degree": "",
        "field": "",
        "institution": "",
    }

    text_lower = text.lower()

    # ── Degree level ──
    degree_map = {
        "bachelor": "BSc",
        "master": "MSc",
        "doctor": "PhD",
        "phd": "PhD",
        "bsc": "BSc",
        "msc": "MSc",
        "ba": "BA",
        "ma": "MA",
        "mba": "MBA",
        "diploma": "Diploma",
    }
    for key, val in degree_map.items():
        if key in text_lower:
            result["degree"] = val
            break

    # ── Field of study ──
    field_match = re.search(
        r"(?:in|of)\s+(.+?)(?:\s*(?:from|at|,|\n))",
        text,
        re.IGNORECASE,
    )
    if field_match:
        field = field_match.group(1).strip()
        if len(field) < 100 and not re.match(r"^(the|this|a)\b", field.lower()):
            result["field"] = field

    # ── Institution ──
    inst_patterns = [
        r"(?:university|institute|college|academy|school|polytechnic)\s+(?:of\s+)?(.+?)(?:\s*\n|\s*,|\s*$)",
        r"(.+?\s+(?:university|institute|college|academy|school|polytechnic))",
    ]
    for pattern in inst_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["institution"] = match.group(1).strip().title()
            break

    # ── Date ──
    date_match = re.search(
        r"(?:graduated|conferred|awarded|completed)\s+(?:on\s+)?(.+?)(?:\s*\n|\s*$)",
        text,
        re.IGNORECASE,
    )
    if date_match:
        result["date"] = date_match.group(1).strip()
        year_match = re.search(r"(\d{4})", result["date"])
        if year_match:
            result["year"] = int(year_match.group(1))

    result["name"] = f"{result['degree']} in {result['field']}" if result["degree"] and result["field"] else result["degree"]

    return result
