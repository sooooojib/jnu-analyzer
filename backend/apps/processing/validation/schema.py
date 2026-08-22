"""
Validation schemas and data structures.

Defines:
  - ValidationStatus enum (VALID, WARNING, NEEDS_REVIEW, INVALID)
  - ValidatedField[T] tracking raw value, normalized value, confidence, status, and warnings
  - ValidatedStudentResult, ValidatedCurrentSemesterSummary, ValidatedCumulativeSummary,
    ValidatedStudent, and ValidatedSheet.
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

T = TypeVar("T")


class ValidationStatus(str, Enum):
    """
    Validation status for fields and entities.
    """
    VALID = "VALID"                # Fully valid, conforms to schema & grading scale
    WARNING = "WARNING"            # Minor issue or deterministic high-confidence correction applied
    NEEDS_REVIEW = "NEEDS_REVIEW"  # Ambiguous, discrepant, or low-confidence value requiring manual review
    INVALID = "INVALID"            # Critical fatal error / impossible value; MUST NOT be used in calculations


@dataclasses.dataclass
class ValidatedField(Generic[T]):
    """
    A single validated field retaining raw value, normalized value, confidence, and audit trail.
    """
    field_name: str
    raw_value: Any
    normalized_value: Optional[T]
    confidence: float = 1.0
    status: ValidationStatus = ValidationStatus.VALID
    warnings: List[str] = dataclasses.field(default_factory=list)
    error: Optional[str] = None
    applied_corrections: List[str] = dataclasses.field(default_factory=list)
    is_usable_in_calculations: bool = True

    @property
    def is_valid(self) -> bool:
        return self.status == ValidationStatus.VALID

    @property
    def is_warning(self) -> bool:
        return self.status == ValidationStatus.WARNING

    @property
    def needs_review(self) -> bool:
        return self.status == ValidationStatus.NEEDS_REVIEW

    @property
    def is_invalid(self) -> bool:
        return self.status == ValidationStatus.INVALID

    def as_dict(self) -> Dict[str, Any]:
        norm_val = self.normalized_value
        if hasattr(norm_val, "as_dict"):
            norm_val = norm_val.as_dict()
        elif isinstance(norm_val, Decimal):
            norm_val = float(norm_val)
        return {
            "field_name": self.field_name,
            "raw_value": str(self.raw_value) if self.raw_value is not None else "",
            "normalized_value": norm_val,
            "confidence": round(self.confidence, 4),
            "status": self.status.value,
            "warnings": self.warnings,
            "error": self.error,
            "applied_corrections": self.applied_corrections,
            "is_usable_in_calculations": self.is_usable_in_calculations,
        }


@dataclasses.dataclass
class ValidatedStudentResult:
    """
    Validated result for a single course taken by a student.
    """
    course_code: ValidatedField[str]
    grade_point: ValidatedField[Decimal]
    letter_grade: ValidatedField[str]
    is_consistent_gp_lg: bool = True
    status: ValidationStatus = ValidationStatus.VALID
    cell_coordinates: Optional[Tuple[float, float, float, float]] = None

    @property
    def is_usable_in_calculations(self) -> bool:
        return self.grade_point.is_usable_in_calculations and self.status != ValidationStatus.INVALID

    def as_dict(self) -> Dict[str, Any]:
        return {
            "course_code": self.course_code.as_dict(),
            "grade_point": self.grade_point.as_dict(),
            "letter_grade": self.letter_grade.as_dict(),
            "is_consistent_gp_lg": self.is_consistent_gp_lg,
            "status": self.status.value,
            "is_usable_in_calculations": self.is_usable_in_calculations,
            "cell_coordinates": self.cell_coordinates,
        }


@dataclasses.dataclass
class ValidatedCurrentSemesterSummary:
    """
    Validated current-semester summary figures.
    """
    gpa: ValidatedField[Decimal]
    total_credit: ValidatedField[Decimal]
    earned_credit: ValidatedField[Decimal]
    grade_points: ValidatedField[Decimal]
    result_status: ValidatedField[str]
    remarks: ValidatedField[str]
    status: ValidationStatus = ValidationStatus.VALID

    def as_dict(self) -> Dict[str, Any]:
        return {
            "gpa": self.gpa.as_dict(),
            "total_credit": self.total_credit.as_dict(),
            "earned_credit": self.earned_credit.as_dict(),
            "grade_points": self.grade_points.as_dict(),
            "result_status": self.result_status.as_dict(),
            "remarks": self.remarks.as_dict(),
            "status": self.status.value,
        }


@dataclasses.dataclass
class ValidatedCumulativeSummary:
    """
    Validated cumulative summary figures.
    """
    cgpa: ValidatedField[Decimal]
    total_credit: ValidatedField[Decimal]
    earned_credit: ValidatedField[Decimal]
    grade_points: ValidatedField[Decimal]
    result_status: ValidatedField[str]
    remarks: ValidatedField[str]
    status: ValidationStatus = ValidationStatus.VALID

    def as_dict(self) -> Dict[str, Any]:
        return {
            "cgpa": self.cgpa.as_dict(),
            "total_credit": self.total_credit.as_dict(),
            "earned_credit": self.earned_credit.as_dict(),
            "grade_points": self.grade_points.as_dict(),
            "result_status": self.result_status.as_dict(),
            "remarks": self.remarks.as_dict(),
            "status": self.status.value,
        }


@dataclasses.dataclass
class ValidatedStudent:
    """
    Complete validated student record.
    """
    student_id: ValidatedField[str]
    student_name: ValidatedField[str]
    serial_no: ValidatedField[int]
    row_index: int
    results: List[ValidatedStudentResult] = dataclasses.field(default_factory=list)
    current_semester_summary: Optional[ValidatedCurrentSemesterSummary] = None
    cumulative_summary: Optional[ValidatedCumulativeSummary] = None
    status: ValidationStatus = ValidationStatus.VALID
    overall_confidence: float = 1.0
    has_critical_errors: bool = False
    validation_messages: List[str] = dataclasses.field(default_factory=list)

    def get_result(self, course_code: str) -> Optional[ValidatedStudentResult]:
        for res in self.results:
            if res.course_code.normalized_value == course_code:
                return res
        return None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id.as_dict(),
            "student_name": self.student_name.as_dict(),
            "serial_no": self.serial_no.as_dict(),
            "row_index": self.row_index,
            "status": self.status.value,
            "overall_confidence": round(self.overall_confidence, 4),
            "has_critical_errors": self.has_critical_errors,
            "validation_messages": self.validation_messages,
            "results": [r.as_dict() for r in self.results],
            "current_semester_summary": self.current_semester_summary.as_dict() if self.current_semester_summary else None,
            "cumulative_summary": self.cumulative_summary.as_dict() if self.cumulative_summary else None,
        }


@dataclasses.dataclass
class ValidatedSheet:
    """
    Complete validated academic result sheet.
    """
    institution: ValidatedField[str]
    program: ValidatedField[str]
    semester: ValidatedField[str]
    exam_session: ValidatedField[str]
    courses: List[ValidatedField[Any]] = dataclasses.field(default_factory=list)
    students: List[ValidatedStudent] = dataclasses.field(default_factory=list)
    overall_confidence: float = 1.0
    status: ValidationStatus = ValidationStatus.VALID
    warnings: List[str] = dataclasses.field(default_factory=list)
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)

    @property
    def total_students(self) -> int:
        return len(self.students)

    @property
    def valid_students_count(self) -> int:
        return sum(1 for s in self.students if s.status == ValidationStatus.VALID)

    @property
    def warning_students_count(self) -> int:
        return sum(1 for s in self.students if s.status == ValidationStatus.WARNING)

    @property
    def needs_review_students_count(self) -> int:
        return sum(1 for s in self.students if s.status == ValidationStatus.NEEDS_REVIEW)

    @property
    def invalid_students_count(self) -> int:
        return sum(1 for s in self.students if s.status == ValidationStatus.INVALID)

    def get_student(self, student_id: str) -> Optional[ValidatedStudent]:
        clean_id = student_id.strip().upper()
        for s in self.students:
            if s.student_id.normalized_value and s.student_id.normalized_value.upper() == clean_id:
                return s
        return None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "institution": self.institution.as_dict(),
            "program": self.program.as_dict(),
            "semester": self.semester.as_dict(),
            "exam_session": self.exam_session.as_dict(),
            "total_students": self.total_students,
            "valid_students_count": self.valid_students_count,
            "warning_students_count": self.warning_students_count,
            "needs_review_students_count": self.needs_review_students_count,
            "invalid_students_count": self.invalid_students_count,
            "overall_confidence": round(self.overall_confidence, 4),
            "status": self.status.value,
            "warnings": self.warnings,
            "courses": [c.as_dict() for c in self.courses],
            "students": [s.as_dict() for s in self.students],
            "metadata": self.metadata,
        }
