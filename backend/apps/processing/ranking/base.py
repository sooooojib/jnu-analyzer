from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseRankingEngine(ABC):
    """
    Abstract interface for computing semester and cumulative ranks and percentiles.
    """
    @abstractmethod
    def calculate_ranks(self, students: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Assign semester_rank, cumulative_rank, and percentile ranks to all students."""
        pass
