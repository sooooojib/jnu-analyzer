from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseAnalysisEngine(ABC):
    """
    Abstract interface for cohort statistical analysis (Mean, Median, Mode, StdDev, IQR).
    """
    @abstractmethod
    def calculate_cohort_statistics(self, students: List[Dict[str, Any]], courses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute aggregate GPA distributions, subject breakdowns, and summary metrics."""
        pass
