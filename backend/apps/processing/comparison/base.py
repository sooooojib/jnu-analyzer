from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseComparisonEngine(ABC):
    """
    Abstract interface for 2-student comparative analysis.
    """
    @abstractmethod
    def compare_students(self, student_a: Dict[str, Any], student_b: Dict[str, Any], cohort_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute delta matrix, GPA difference, and course-by-course vector."""
        pass
