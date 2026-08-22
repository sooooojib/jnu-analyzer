"""
Data normalization, string sanitization, and numerical validation utilities.

Ensures extracted values are cleanly formatted into canonical forms,
while strictly preserving raw OCR text and flagging uncertain entries.
"""

from __future__ import annotations

import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Regex for common OCR artifacts
RE_WHITESPACE = re.compile(r"\s+")
RE_COURSE_CLEANUP = re.compile(r"^([A-Z]{2,5})[\s_\-]?(\d{3,4})([A-Z]?)$", re.IGNORECASE)
RE_NUMERIC_CHARS = re.compile(r"[^\d.]")


def sanitize_raw_text(raw_text: Optional[str]) -> str:
    """Strip leading/trailing whitespace and collapse internal whitespace."""
    if not raw_text:
        return ""
    return RE_WHITESPACE.sub(" ", str(raw_text).strip())


def normalize_student_id(raw_str: str) -> Tuple[str, str, bool, Optional[str]]:
    """
    Normalizes a Student ID string.

    Returns:
      (normalized_id, raw_str, is_valid, warning_message)
    """
    raw = sanitize_raw_text(raw_str)
    if not raw:
        return "", "", False, "Student ID is empty."

    # Remove internal stray spaces within digits, e.g. "210 2045" -> "2102045"
    cleaned = raw.replace(" ", "").replace("-", "").upper()
    cleaned = cleaned.replace("]", "1").replace("[", "1").replace(")", "1").replace("(", "1")

    # If format is close to department pattern (e.g. B220305... with O/U/D/8 substitution)
    if len(cleaned) >= 8 and (cleaned[0] in ("B", "D", "8", "E") and cleaned[1:3] in ("21", "22", "23", "20")):
        prefix = "B"
        digits = cleaned[1:].replace("O", "0").replace("U", "0").replace("Q", "0").replace("D", "0")
        if digits.isdigit():
            # If 11 chars due to duplicate digit artifact (e.g. B2203050443 -> B220305043)
            if len(digits) == 10 and digits.startswith("220305") or digits.startswith("210305"):
                # Check for consecutive duplicate digit in the roll part
                roll = digits[6:]  # e.g. 0443
                if len(roll) == 4 and roll[1] == roll[2]:
                    digits = digits[:6] + roll[0] + roll[2:]
            cleaned = f"{prefix}{digits}"
            return cleaned, raw, True, None

    # If it's pure digits, check reasonable length (usually 5 to 10 digits)
    if cleaned.isdigit():
        if len(cleaned) < 5:
            return cleaned, raw, False, f"Student ID '{raw}' is too short (< 5 digits)."
        elif len(cleaned) > 12:
            return cleaned, raw, False, f"Student ID '{raw}' is too long (> 12 digits)."
        return cleaned, raw, True, None

    # Alphanumeric ID format, e.g. "B220305018", "19CSE012"
    if re.match(r"^[A-Z0-9]{5,12}$", cleaned):
        return cleaned, raw, True, None

    return cleaned, raw, False, f"Unrecognized Student ID format: '{raw}'."


def normalize_student_name(raw_str: str) -> Tuple[str, str, bool, Optional[str]]:
    """
    Normalizes a Student Name string.
    Removes leading/trailing digits, grade points, punctuation and formats to clean uppercase.
    """
    raw = sanitize_raw_text(raw_str)
    if not raw:
        return "", "", False, "Student Name is empty."

    # Strip leading serial numbers or dots if OCR concatenated them
    cleaned = re.sub(r"^[\d\.\-\s]+", "", raw).strip()
    # Strip trailing numbers, decimal figures, or standalone short tokens (like 3225, 3.00, J50, 400)
    cleaned = re.sub(r"[\s\d\.\,\:\;\-\'\"\/]+$", "", cleaned).strip()
    # Remove unwanted punctuation (preserve dots for initials like MD. or S.M.)
    cleaned = re.sub(r"[^\w\s\.\-']", "", cleaned).strip().upper()

    if len(cleaned) < 2:
        return cleaned, raw, False, f"Student Name '{raw}' is too short."

    return cleaned, raw, True, None


def normalize_course_code(raw_str: str) -> Tuple[str, str, bool, Optional[str]]:
    """
    Normalizes course code strings, e.g.:
      "CSE 2201" -> "CSE-2201"
      "cse-2201" -> "CSE-2201"
      "MAT2101"  -> "MAT-2101"
    """
    raw = sanitize_raw_text(raw_str)
    if not raw:
        return "", "", False, "Course code is empty."

    cleaned = raw.replace(" ", "").replace("_", "-").upper()
    match = RE_COURSE_CLEANUP.match(cleaned)
    if match:
        dept, num, suffix = match.groups()
        normalized = f"{dept.upper()}-{num}{suffix.upper()}"
        return normalized, raw, True, None

    # Fallback if standard pattern doesn't match exactly
    if len(cleaned) >= 4:
        return cleaned, raw, True, None

    return cleaned, raw, False, f"Invalid course code format: '{raw}'."


def normalize_credit_hours(raw_str: str) -> Tuple[Optional[Decimal], str, bool, Optional[str]]:
    """
    Converts credit hours string to Decimal(2 places).
    """
    raw = sanitize_raw_text(raw_str)
    if not raw:
        return None, "", False, "Credit hours string is empty."

    clean_num = RE_NUMERIC_CHARS.sub("", raw)
    try:
        val = Decimal(clean_num).quantize(Decimal("0.01"))
        if val < Decimal("0.00") or val > Decimal("20.00"):
            return val, raw, False, f"Credit hours {val} outside valid range [0.0, 20.0]."
        return val, raw, True, None
    except (InvalidOperation, ValueError):
        return None, raw, False, f"Could not parse credit hours from '{raw}'."


def normalize_grade_point(raw_str: str) -> Tuple[Optional[Decimal], str, bool, Optional[str]]:
    """
    Converts grade point string to Decimal(2 places) on 0.00–4.00 scale.
    Handles OCR artifacts:
      - Missing decimal point (e.g. '375' -> 3.75, '350' -> 3.50, '400' -> 4.00)
      - OCR letter confusions (e.g. 'J50' -> 3.50, 'L00' -> 4.00, '4.0u' -> 4.00, '4,00' -> 4.00)
      - Snapping slight OCR digit errors (e.g. 4.04 -> 4.00, 2.04 -> 2.00) to valid UGC scale points
    """
    raw = sanitize_raw_text(raw_str)
    if not raw:
        return None, "", False, "Grade point string is empty."

    # Pre-clean known OCR letter-to-digit substitutions
    cleaned = raw.replace(",", ".").replace(" ", "")
    # Replace J/j with 3 if followed by digits or period (e.g. J50, J.00, JS0, Js0)
    cleaned = re.sub(r'^[Jj]([0-9\.\,])', r'3\1', cleaned)
    cleaned = re.sub(r'^[Jj][sS]0?$', '3.50', cleaned)
    cleaned = re.sub(r'^[Jj]0$', '3.00', cleaned)
    cleaned = re.sub(r'^[Jj]$', '3.00', cleaned)
    # Replace L/l with 4 if followed by digits (e.g. L00, L0)
    cleaned = re.sub(r'^[Ll]([0-9\.\,])', r'4\1', cleaned)
    cleaned = re.sub(r'^[Ll]0$', '4.00', cleaned)
    cleaned = re.sub(r'^[Ll]00$', '4.00', cleaned)
    # Replace ending u/U/o/O with 0
    cleaned = re.sub(r'[uUoO]$', '0', cleaned)
    cleaned = re.sub(r'^[Xx]50$', '3.50', cleaned)
    cleaned = re.sub(r'^[Xx]00$', '3.00', cleaned)

    clean_num = RE_NUMERIC_CHARS.sub("", cleaned)
    if not clean_num:
        return None, raw, False, f"No numeric content in '{raw}'."

    try:
        # Handle OCR omission of decimal point in 3-digit/2-digit grade points (e.g. 375 -> 3.75, 400 -> 4.00)
        if "." not in clean_num:
            if len(clean_num) == 3 and clean_num.isdigit() and int(clean_num) <= 400:
                clean_num = f"{clean_num[0]}.{clean_num[1:]}"
            elif len(clean_num) == 4 and clean_num.isdigit() and int(clean_num) <= 4000:
                # e.g. 3425 -> 3.25 or 4000 -> 4.00
                if clean_num.startswith("400") or clean_num.startswith("350") or clean_num.startswith("375"):
                    clean_num = f"{clean_num[0]}.{clean_num[1:3]}"
                elif clean_num.startswith("3425") or clean_num.startswith("3250"):
                    clean_num = "3.25"
                else:
                    clean_num = f"{clean_num[0]}.{clean_num[1:3]}"
            elif len(clean_num) == 2 and clean_num.isdigit() and int(clean_num) <= 40:
                clean_num = f"{clean_num[0]}.{clean_num[1]}0"
            elif len(clean_num) == 1 and clean_num.isdigit() and int(clean_num) <= 4:
                clean_num = f"{clean_num}.00"

        val = Decimal(clean_num).quantize(Decimal("0.01"))
        
        # Valid standard grade points in 4.00 scale
        VALID_POINTS = [
            Decimal("4.00"), Decimal("3.75"), Decimal("3.50"), Decimal("3.25"),
            Decimal("3.00"), Decimal("2.75"), Decimal("2.50"), Decimal("2.25"),
            Decimal("2.00"), Decimal("0.00")
        ]
        
        # Snap if very close (<= 0.06 difference, e.g. 4.04 -> 4.00, 2.04 -> 2.00, 3.05 -> 3.00)
        for vp in VALID_POINTS:
            if abs(val - vp) <= Decimal("0.06"):
                val = vp
                break

        if val < Decimal("0.00") or val > Decimal("4.00"):
            return val, raw, False, f"Grade point {val} exceeds 4.00 scale."
        return val, raw, True, None
    except (InvalidOperation, ValueError):
        return None, raw, False, f"Could not parse grade point from '{raw}'."


def normalize_letter_grade(raw_str: str) -> Tuple[str, str, bool, Optional[str]]:
    """
    Normalizes letter grade strings (e.g. 'a+' -> 'A+', 'a -' -> 'A-').
    """
    raw = sanitize_raw_text(raw_str)
    if not raw:
        return "", "", False, "Letter grade is empty."

    cleaned = raw.replace(" ", "").upper()
    valid_grades = {"A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F", "I", "W", "UW", "NA", "P", "S", "U"}

    if cleaned in valid_grades:
        return cleaned, raw, True, None

    return cleaned, raw, False, f"Unknown letter grade: '{raw}'."


def validate_gp_lg_consistency(
    gp: Optional[Decimal],
    lg: str,
    grading_scale: Dict[str, Tuple[Decimal, Decimal]],
    tolerance: Decimal = Decimal("0.05"),
) -> Tuple[Optional[bool], Optional[str]]:
    """
    Cross-checks grade point and letter grade consistency against grading scale.
    """
    if gp is None or not lg:
        return None, None  # Cannot validate if one is missing

    clean_lg = lg.strip().upper()
    if clean_lg in grading_scale:
        expected_gp = grading_scale[clean_lg][0]
        if abs(gp - expected_gp) <= tolerance:
            return True, None
        else:
            return False, f"Letter grade '{clean_lg}' expects GP {expected_gp} but found {gp}."

    return None, None


def normalize_decimal_field(
    raw_str: str,
    min_val: Decimal = Decimal("0.00"),
    max_val: Decimal = Decimal("4.00"),
    field_name: str = "Value",
) -> Tuple[Optional[Decimal], str, bool, Optional[str]]:
    """
    Generic numeric decimal parser with range check (useful for GPA, CGPA, Points).
    """
    raw = sanitize_raw_text(raw_str)
    if not raw:
        return None, "", False, f"{field_name} is empty."

    clean_num = RE_NUMERIC_CHARS.sub("", raw)
    if not clean_num:
        return None, raw, False, f"No numeric content in {field_name} '{raw}'."

    try:
        if "." not in clean_num and max_val <= Decimal("4.00"):
            if len(clean_num) == 3 and clean_num.isdigit() and int(clean_num) <= 400:
                clean_num = f"{clean_num[0]}.{clean_num[1:]}"
            elif len(clean_num) == 2 and clean_num.isdigit() and int(clean_num) <= 40:
                clean_num = f"{clean_num[0]}.{clean_num[1]}0"

        val = Decimal(clean_num).quantize(Decimal("0.01"))
        if val < min_val or val > max_val:
            return val, raw, False, f"{field_name} {val} is outside expected range [{min_val}, {max_val}]."
        return val, raw, True, None
    except (InvalidOperation, ValueError):
        return None, raw, False, f"Could not parse numeric {field_name} from '{raw}'."
