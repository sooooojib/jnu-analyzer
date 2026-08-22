"""
Base utilities and helpers for the Academic Result Sheet Export Data Layer.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def normalize_student_id(raw_id: Any) -> str:
    """Strips all leading, trailing, and internal whitespace and casts to uppercase string."""
    if raw_id is None:
        return ""
    return re.sub(r"\s+", "", str(raw_id)).upper()


def safe_float(val: Any, default: Optional[float] = None) -> Optional[float]:
    """Safely converts numeric values to float, returning default if None or invalid."""
    if val is None or val == "":
        return default
    try:
        return round(float(val), 4)
    except (ValueError, TypeError):
        return default


def find_student_in_dataset(students: List[Dict[str, Any]], query_id: str) -> Optional[Dict[str, Any]]:
    """
    Finds a student record in the given student list using exact or normalized ID match.
    Strictly stays within the provided dataset list.
    """
    clean_query = str(query_id).strip()
    norm_query = normalize_student_id(query_id)
    if not norm_query:
        return None

    for s in students:
        s_id = str(s.get("student_id", "")).strip()
        if s_id == clean_query or normalize_student_id(s_id) == norm_query:
            return s
    return None


def get_letter_grade_from_gpa(gpa: Optional[float]) -> str:
    """Returns UGC letter grade corresponding to a GPA."""
    if gpa is None:
        return "N/A"
    val = float(gpa)
    if val >= 4.0:
        return "A+"
    elif val >= 3.75:
        return "A"
    elif val >= 3.50:
        return "A-"
    elif val >= 3.25:
        return "B+"
    elif val >= 3.00:
        return "B"
    elif val >= 2.75:
        return "B-"
    elif val >= 2.50:
        return "C+"
    elif val >= 2.25:
        return "C"
    elif val >= 2.00:
        return "D"
    else:
        return "F"
