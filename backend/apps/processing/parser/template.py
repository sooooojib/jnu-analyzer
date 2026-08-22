"""
Configurable Result Sheet Template and Grading Scale definitions.

Enables adapting the parser to various university and departmental result sheet
layouts without hardcoding column indexes or student schemas.
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple
import re


# ---------------------------------------------------------------------------
# Default Standard Grading Scale (UGC / North American 4.00 Scale)
# ---------------------------------------------------------------------------

DEFAULT_GRADING_SCALE: Dict[str, Tuple[Decimal, Decimal]] = {
    # Grade: (Grade Point, Min Marks % approx / scale standard)
    "A+": (Decimal("4.00"), Decimal("80.0")),
    "A":  (Decimal("3.75"), Decimal("75.0")),
    "A-": (Decimal("3.50"), Decimal("70.0")),
    "B+": (Decimal("3.25"), Decimal("65.0")),
    "B":  (Decimal("3.00"), Decimal("60.0")),
    "B-": (Decimal("2.75"), Decimal("55.0")),
    "C+": (Decimal("2.50"), Decimal("50.0")),
    "C":  (Decimal("2.25"), Decimal("45.0")),
    "D":  (Decimal("2.00"), Decimal("40.0")),
    "F":  (Decimal("0.00"), Decimal("0.0")),
}

# Non-credit / status grades
NON_NUMERIC_GRADES: Set[str] = {"I", "W", "UW", "NA", "P", "S", "U"}


@dataclasses.dataclass
class ResultSheetTemplate:
    """
    Configuration specification for academic result sheet parsing.
    """
    name: str = "Standard Tabulation Sheet"
    description: str = "Standard departmental result sheet with course columns, GP/LG, and semester summaries."

    # --- Header Keywords for Column Recognition ---
    serial_keywords: Set[str] = dataclasses.field(
        default_factory=lambda: {"sl", "sl.", "sl#", "serial", "no", "no.", "roll#"}
    )
    student_id_keywords: Set[str] = dataclasses.field(
        default_factory=lambda: {"id", "id.", "student id", "student's id", "roll", "reg", "reg.", "registration", "student_id"}
    )
    student_name_keywords: Set[str] = dataclasses.field(
        default_factory=lambda: {"name", "student name", "student's name", "name of student", "name of the student"}
    )
    credit_keywords: Set[str] = dataclasses.field(
        default_factory=lambda: {"cr", "cr.", "credit", "credits", "ch", "c.h.", "c.h", "credit hours"}
    )
    grade_point_keywords: Set[str] = dataclasses.field(
        default_factory=lambda: {"gp", "g.p.", "grade point", "gpa", "point"}
    )
    letter_grade_keywords: Set[str] = dataclasses.field(
        default_factory=lambda: {"lg", "l.g.", "letter grade", "grade"}
    )
    current_summary_keywords: Set[str] = dataclasses.field(
        default_factory=lambda: {"current", "semester", "this semester", "term", "sgpa", "gpa", "current result"}
    )
    cumulative_summary_keywords: Set[str] = dataclasses.field(
        default_factory=lambda: {"cumulative", "cgpa", "total earned", "overall", "cumulative result"}
    )

    # --- Regular Expression Patterns ---
    student_id_pattern: str = r"^\b([A-Z]?\d{6,10}|[A-Z]\d{8,10}|\d{2}[A-Z]{2,4}\d{3,5})\b$"
    course_code_pattern: str = r"^[A-Z]{2,5}[-\s]?\d{3,4}[A-Z]?$"
    credit_pattern: str = r"^(0\.\d{1,2}|[1-9](\.\d{1,2})?)$"
    grade_point_pattern: str = r"^(4(\.00?)?|[0-3]\.\d{1,2}|0(\.00?)?)$"
    letter_grade_pattern: str = r"^(A\+|A|A-|B\+|B|B-|C\+|C|C-|D\+|D|D-|F|I|W|UW|NA)$"

    # --- Grading Scale & Validation Rules ---
    grading_scale: Dict[str, Tuple[Decimal, Decimal]] = dataclasses.field(
        default_factory=lambda: dict(DEFAULT_GRADING_SCALE)
    )
    max_gpa: Decimal = Decimal("4.00")
    min_gpa: Decimal = Decimal("0.00")
    min_credit_hours: Decimal = Decimal("0.50")
    max_credit_hours: Decimal = Decimal("12.00")

    # --- Reference Department Courses for Standard Tabulation Structure ---
    reference_courses: List[Dict[str, Any]] = dataclasses.field(
        default_factory=lambda: [
            {"course_code": "CSE-1201", "course_title": "Object Oriented Programming-I", "credit_hours": Decimal("3.00")},
            {"course_code": "CSEL-1202", "course_title": "Object Oriented Programming-I Lab", "credit_hours": Decimal("1.50")},
            {"course_code": "CSE-1203", "course_title": "Data Structure", "credit_hours": Decimal("3.00")},
            {"course_code": "CSEL-1204", "course_title": "Data Structure Lab", "credit_hours": Decimal("1.50")},
            {"course_code": "CSE-1205", "course_title": "Basic Electronics", "credit_hours": Decimal("3.00")},
            {"course_code": "CSEL-1206", "course_title": "Basic Electronics Lab", "credit_hours": Decimal("1.50")},
            {"course_code": "CSEG-1207", "course_title": "Math-II (Linear Algebra)", "credit_hours": Decimal("3.00")},
            {"course_code": "CSEG-1208", "course_title": "Discrete Mathematics", "credit_hours": Decimal("3.00")},
            {"course_code": "CSEG-1209", "course_title": "History of the Liberation War of Bangladesh", "credit_hours": Decimal("2.00")},
            {"course_code": "CSEV-1210", "course_title": "Viva-Voce", "credit_hours": Decimal("1.00")},
        ]
    )

    # --- Confidence Thresholds ---
    min_acceptable_confidence: float = 0.60
    flag_discrepant_grades: bool = True

    # --- Metadata Regex for Sheet Header ---
    institution_patterns: List[str] = dataclasses.field(
        default_factory=lambda: [
            r"university", r"institute", r"college", r"department\s+of", r"faculty\s+of"
        ]
    )
    semester_patterns: List[str] = dataclasses.field(
        default_factory=lambda: [
            r"(1st|2nd|3rd|4th|5th|6th|7th|8th)\s+semester",
            r"semester\s*[-:]?\s*([1-8]|I|II|III|IV|V|VI|VII|VIII)",
            r"(fall|spring|summer)\s+\d{4}",
        ]
    )
    exam_session_patterns: List[str] = dataclasses.field(
        default_factory=lambda: [
            r"session\s*[-:]?\s*(\d{4}\s*[-–]\s*\d{4})",
            r"examination\s*[-:]?\s*(\d{4})",
            r"held\s+in\s+([A-Za-z]+,?\s+\d{4})",
        ]
    )

    def is_valid_letter_grade(self, grade: str) -> bool:
        clean = grade.strip().upper()
        return clean in self.grading_scale or clean in NON_NUMERIC_GRADES

    def get_expected_grade_point(self, grade: str) -> Optional[Decimal]:
        clean = grade.strip().upper()
        if clean in self.grading_scale:
            return self.grading_scale[clean][0]
        return None


def get_default_template() -> ResultSheetTemplate:
    """Return the default pre-configured result-sheet template."""
    return ResultSheetTemplate()
