"""
data_handler.py
Handles collection, validation, storage, and masked display of candidate data.
Compliant with GDPR best-practice principles (minimal data, masked logs).
"""

import json
import re
import os
from datetime import datetime
from pathlib import Path


DATA_DIR = Path("candidate_data")


def ensure_data_dir():
    """Create the data directory if it doesn't exist."""
    DATA_DIR.mkdir(exist_ok=True)


def mask_email(email: str) -> str:
    """Mask email for display: john.doe@gmail.com → j***.d**@gmail.com"""
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    parts = local.split(".")
    masked_parts = [p[0] + "*" * (len(p) - 1) if len(p) > 1 else p for p in parts]
    return ".".join(masked_parts) + "@" + domain


def mask_phone(phone: str) -> str:
    """Mask phone: +91-9876543210 → +91-98*****210"""
    digits = re.sub(r"\D", "", phone)
    if len(digits) >= 6:
        return phone[:3] + "*" * (len(digits) - 6) + digits[-3:]
    return "***"


def validate_email(email: str) -> bool:
    """Basic email format validation."""
    pattern = r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def extract_email_from_text(text: str) -> str | None:
    """Try to pull an email out of freeform text."""
    pattern = r"[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}"
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_years_from_text(text: str) -> str:
    """Try to extract a year count from freeform text."""
    match = re.search(r"(\d+\.?\d*)\s*(years?|yrs?)?", text, re.IGNORECASE)
    if match:
        return match.group(1) + " years"
    return text.strip()


def save_candidate(data: dict) -> str:
    """
    Save candidate data to a JSON file.
    Sensitive fields are stored masked in the log file.
    Returns the filename.
    """
    ensure_data_dir()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name_slug = re.sub(r"\W+", "_", data.get("name", "unknown").lower())
    filename = DATA_DIR / f"{name_slug}_{ts}.json"

    # Build a privacy-safe record for storage
    record = {
        "timestamp": datetime.now().isoformat(),
        "name": data.get("name", ""),
        "email_masked": mask_email(data.get("email", "")),
        "phone_masked": mask_phone(data.get("phone", "Not provided")),
        "location": data.get("location", ""),
        "experience": data.get("experience", ""),
        "desired_position": data.get("desired_position", ""),
        "tech_stack": data.get("tech_stack", ""),
        "tech_questions_asked": data.get("questions_asked", []),
        "session_summary": data.get("session_summary", ""),
    }

    with open(filename, "w") as f:
        json.dump(record, f, indent=2)

    return str(filename)


def format_candidate_summary(data: dict) -> str:
    """Return a human-readable summary of collected candidate info."""
    lines = []
    if data.get("name"):
        lines.append(f"**Name:** {data['name']}")
    if data.get("email"):
        lines.append(f"**Email:** {mask_email(data['email'])}")
    if data.get("phone"):
        lines.append(f"**Phone:** {mask_phone(data['phone'])}")
    if data.get("location"):
        lines.append(f"**Location:** {data['location']}")
    if data.get("experience"):
        lines.append(f"**Experience:** {data['experience']}")
    if data.get("desired_position"):
        lines.append(f"**Desired Role:** {data['desired_position']}")
    if data.get("tech_stack"):
        lines.append(f"**Tech Stack:** {data['tech_stack']}")
    return "\n".join(lines)


def get_all_candidates() -> list[dict]:
    """Load all saved candidate records (for admin/sidebar display)."""
    ensure_data_dir()
    records = []
    for f in sorted(DATA_DIR.glob("*.json"), reverse=True):
        try:
            with open(f) as fp:
                records.append(json.load(fp))
        except Exception:
            pass
    return records
