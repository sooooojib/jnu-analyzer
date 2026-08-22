"""
Abstract interface for result sheet and student data validators.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from apps.processing.parser.schema import ParsedCourse, ParsedSheet, ParsedStudent
from apps.processing.parser.template import ResultSheetTemplate
from .schema import ValidatedSheet, ValidatedStudent


class BaseValidator(ABC):
    """
    Abstract interface for academic result validation and confidence scoring.
    """

    @abstractmethod
    def validate_sheet(
        self,
        sheet: ParsedSheet,
        template: Optional[ResultSheetTemplate] = None,
    ) -> ValidatedSheet:
        """
        Validate complete parsed result sheet dataset.
        """
        pass

    @abstractmethod
    def validate_student(
        self,
        student: ParsedStudent,
        courses: List[ParsedCourse],
        template: Optional[ResultSheetTemplate] = None,
    ) -> ValidatedStudent:
        """
        Validate an individual student record.
        """
        pass

    # ------------------------------------------------------------------
    # Legacy compatibility methods
    # ------------------------------------------------------------------

    @abstractmethod
    def validate_student_record(self, student_record: Dict[str, Any], courses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify credit summation, recalculate GPA, check GP-Letter match."""
        pass
