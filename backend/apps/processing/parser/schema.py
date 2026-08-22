"""
Normalized Data Models for Parsed Result Sheets.

Structured intermediate representation produced by the SheetParserService,
containing normalized models ready for dataset persistence, validation,
and downstream analytics.
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple


@dataclasses.dataclass
class ParsedCourse:
    """
    Normalized course column structure.
    """
    course_code: str
    course_code_raw: str = ""
    course_title: str = ""
    course_title_raw: str = ""
    credit_hours: Optional[Decimal] = None
    credit_hours_raw: str = ""
    column_index: int = 0
    gp_col_index: Optional[int] = None
    lg_col_index: Optional[int] = None
    confidence: float = 1.0
    requires_review: bool = False
    review_reasons: List[str] = dataclasses.field(default_factory=list)
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "course_code": self.course_code,
            "course_code_raw": self.course_code_raw,
            "course_title": self.course_title,
            "course_title_raw": self.course_title_raw,
            "credit_hours": float(self.credit_hours) if self.credit_hours is not None else None,
            "credit_hours_raw": self.credit_hours_raw,
            "column_index": self.column_index,
            "confidence": round(self.confidence, 4),
            "requires_review": self.requires_review,
            "review_reasons": self.review_reasons,
        }


@dataclasses.dataclass
class ParsedStudentResult:
    """
    Normalized single course grade for one student.
    """
    course_code: str
    grade_point: Optional[Decimal] = None
    grade_point_raw: str = ""
    letter_grade: str = ""
    letter_grade_raw: str = ""
    is_valid_match: Optional[bool] = None
    confidence: float = 1.0
    requires_review: bool = False
    review_reasons: List[str] = dataclasses.field(default_factory=list)
    cell_coordinates: Optional[Tuple[float, float, float, float]] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "course_code": self.course_code,
            "grade_point": float(self.grade_point) if self.grade_point is not None else None,
            "grade_point_raw": self.grade_point_raw,
            "letter_grade": self.letter_grade,
            "letter_grade_raw": self.letter_grade_raw,
            "is_valid_match": self.is_valid_match,
            "confidence": round(self.confidence, 4),
            "requires_review": self.requires_review,
            "review_reasons": self.review_reasons,
            "cell_coordinates": self.cell_coordinates,
        }


@dataclasses.dataclass
class ParsedCurrentSemesterSummary:
    """
    Normalized current-semester summary figures for one student.
    """
    gpa: Optional[Decimal] = None
    gpa_raw: str = ""
    total_credit: Optional[Decimal] = None
    total_credit_raw: str = ""
    earned_credit: Optional[Decimal] = None
    earned_credit_raw: str = ""
    grade_points: Optional[Decimal] = None
    grade_points_raw: str = ""
    result_status: str = ""
    result_status_raw: str = ""
    remarks: str = ""
    remarks_raw: str = ""
    confidence: float = 1.0
    requires_review: bool = False
    review_reasons: List[str] = dataclasses.field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "gpa": float(self.gpa) if self.gpa is not None else None,
            "gpa_raw": self.gpa_raw,
            "total_credit": float(self.total_credit) if self.total_credit is not None else None,
            "total_credit_raw": self.total_credit_raw,
            "earned_credit": float(self.earned_credit) if self.earned_credit is not None else None,
            "earned_credit_raw": self.earned_credit_raw,
            "grade_points": float(self.grade_points) if self.grade_points is not None else None,
            "grade_points_raw": self.grade_points_raw,
            "result_status": self.result_status,
            "result_status_raw": self.result_status_raw,
            "remarks": self.remarks,
            "remarks_raw": self.remarks_raw,
            "confidence": round(self.confidence, 4),
            "requires_review": self.requires_review,
            "review_reasons": self.review_reasons,
        }


@dataclasses.dataclass
class ParsedCumulativeSummary:
    """
    Normalized cumulative summary figures for one student.
    """
    cgpa: Optional[Decimal] = None
    cgpa_raw: str = ""
    total_credit: Optional[Decimal] = None
    total_credit_raw: str = ""
    earned_credit: Optional[Decimal] = None
    earned_credit_raw: str = ""
    grade_points: Optional[Decimal] = None
    grade_points_raw: str = ""
    result_status: str = ""
    result_status_raw: str = ""
    remarks: str = ""
    remarks_raw: str = ""
    confidence: float = 1.0
    requires_review: bool = False
    review_reasons: List[str] = dataclasses.field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "cgpa": float(self.cgpa) if self.cgpa is not None else None,
            "cgpa_raw": self.cgpa_raw,
            "total_credit": float(self.total_credit) if self.total_credit is not None else None,
            "total_credit_raw": self.total_credit_raw,
            "earned_credit": float(self.earned_credit) if self.earned_credit is not None else None,
            "earned_credit_raw": self.earned_credit_raw,
            "grade_points": float(self.grade_points) if self.grade_points is not None else None,
            "grade_points_raw": self.grade_points_raw,
            "result_status": self.result_status,
            "result_status_raw": self.result_status_raw,
            "remarks": self.remarks,
            "remarks_raw": self.remarks_raw,
            "confidence": round(self.confidence, 4),
            "requires_review": self.requires_review,
            "review_reasons": self.review_reasons,
        }


@dataclasses.dataclass
class ParsedStudent:
    """
    Complete normalized record for a single student row.
    """
    student_id: str
    student_id_raw: str = ""
    student_name: str = ""
    student_name_raw: str = ""
    serial_no: Optional[int] = None
    serial_no_raw: str = ""
    row_index: int = 0
    results: List[ParsedStudentResult] = dataclasses.field(default_factory=list)
    current_semester_summary: Optional[ParsedCurrentSemesterSummary] = None
    cumulative_summary: Optional[ParsedCumulativeSummary] = None
    confidence: float = 1.0
    requires_review: bool = False
    review_reasons: List[str] = dataclasses.field(default_factory=list)

    def get_result(self, course_code: str) -> Optional[ParsedStudentResult]:
        for res in self.results:
            if res.course_code == course_code:
                return res
        return None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "student_id_raw": self.student_id_raw,
            "student_name": self.student_name,
            "student_name_raw": self.student_name_raw,
            "serial_no": self.serial_no,
            "serial_no_raw": self.serial_no_raw,
            "row_index": self.row_index,
            "confidence": round(self.confidence, 4),
            "requires_review": self.requires_review,
            "review_reasons": self.review_reasons,
            "results": [r.as_dict() for r in self.results],
            "current_semester_summary": self.current_semester_summary.as_dict() if self.current_semester_summary else None,
            "cumulative_summary": self.cumulative_summary.as_dict() if self.cumulative_summary else None,
        }


@dataclasses.dataclass
class ParsedSheet:
    """
    Complete structured output representing the entire parsed result sheet dataset.
    """
    institution: str = ""
    program: str = ""
    semester: str = ""
    exam_session: str = ""
    courses: List[ParsedCourse] = dataclasses.field(default_factory=list)
    students: List[ParsedStudent] = dataclasses.field(default_factory=list)
    template_name: str = "Standard Tabulation Sheet"
    overall_confidence: float = 1.0
    warnings: List[str] = dataclasses.field(default_factory=list)
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)

    @property
    def student_count(self) -> int:
        return len(self.students)

    @property
    def course_count(self) -> int:
        return len(self.courses)

    @property
    def requires_review_count(self) -> int:
        return sum(1 for s in self.students if s.requires_review)

    def get_student(self, student_id: str) -> Optional[ParsedStudent]:
        clean_id = student_id.strip().upper()
        for s in self.students:
            if s.student_id.upper() == clean_id:
                return s
        return None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "institution": self.institution,
            "program": self.program,
            "semester": self.semester,
            "exam_session": self.exam_session,
            "student_count": self.student_count,
            "course_count": self.course_count,
            "overall_confidence": round(self.overall_confidence, 4),
            "requires_review_count": self.requires_review_count,
            "template_name": self.template_name,
            "warnings": self.warnings,
            "courses": [c.as_dict() for c in self.courses],
            "students": [s.as_dict() for s in self.students],
            "metadata": self.metadata,
        }
