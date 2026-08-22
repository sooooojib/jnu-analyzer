"""
ValidationService — High-level validation and normalization service.

Verifies:
  - Student IDs, Names, Course Codes, Credits, Grade Points, Letter Grades
  - Conformance to institutional grading scales
  - Deterministic high-confidence OCR corrections (O vs 0, I vs 1, missing dots, extra spaces)
  - Exclusion of critical invalid values from calculation pipelines
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from apps.processing.parser.schema import ParsedCourse, ParsedSheet, ParsedStudent
from apps.processing.parser.template import ResultSheetTemplate, get_default_template
from .base import BaseValidator
from .schema import (
    ValidatedField,
    ValidatedSheet,
    ValidatedStudent,
    ValidationStatus,
)
from .validation_engine import SheetValidationEngine

logger = logging.getLogger(__name__)


class ValidationService(BaseValidator):
    """
    Concrete validation and normalization service.
    """

    def __init__(self, default_template: Optional[ResultSheetTemplate] = None):
        self.default_template = default_template or get_default_template()
        self._engine = SheetValidationEngine(template=self.default_template)

    # -----------------------------------------------------------------------
    # Primary Public Interface
    # -----------------------------------------------------------------------

    def validate_sheet(
        self,
        sheet: ParsedSheet,
        template: Optional[ResultSheetTemplate] = None,
    ) -> ValidatedSheet:
        """
        Validate an entire ParsedSheet dataset against institutional grading rules.
        """
        engine = SheetValidationEngine(template=template or self.default_template) if template else self._engine
        return engine.validate_sheet(sheet=sheet, template=template)

    def validate_student(
        self,
        student: ParsedStudent,
        courses: List[ParsedCourse],
        template: Optional[ResultSheetTemplate] = None,
    ) -> ValidatedStudent:
        """
        Validate an individual student record.
        """
        engine = SheetValidationEngine(template=template or self.default_template) if template else self._engine
        return engine.validate_student(student=student, courses=courses, template=template)

    # -----------------------------------------------------------------------
    # Legacy Compatibility Methods
    # -----------------------------------------------------------------------

    def validate_student_record(self, student_record: Dict[str, Any], courses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Legacy shim for backwards compatibility."""
        return {
            "is_valid": True,
            "calculated_gpa": student_record.get("semester_result", {}).get("gpa", 0.0),
            "discrepancies": [],
            "confidence_score": 1.0,
        }
