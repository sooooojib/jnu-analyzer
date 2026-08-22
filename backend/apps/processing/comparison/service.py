"""
ComparisonEngineService — High-level service for 2-student comparative analysis.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import BaseComparisonEngine
from .engine import DeterministicComparisonEngine

logger = logging.getLogger(__name__)


class ComparisonEngineService(BaseComparisonEngine):
    """
    Service for calculating head-to-head metrics and difference matrices between two students.
    """

    def __init__(self):
        self.engine = DeterministicComparisonEngine()

    def compare_students(
        self,
        student_a: Dict[str, Any],
        student_b: Dict[str, Any],
        cohort_data: Optional[Dict[str, Any]] = None,
        courses: Optional[List[Dict[str, Any]]] = None,
        ranking_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculates head-to-head comparison metrics between two students.
        """
        logger.info(
            f"Comparing student {student_a.get('student_id')} with {student_b.get('student_id')}"
        )
        courses = courses or []
        return self.engine.compare_students(
            student_a=student_a,
            student_b=student_b,
            courses=courses,
            cohort_analytics=cohort_data,
            ranking_data=ranking_data,
        )
