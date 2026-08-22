"""
RankingEngineService — High-level service for calculating standard competition rankings.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import BaseRankingEngine
from .engine import DeterministicRankingEngine

logger = logging.getLogger(__name__)


class RankingEngineService(BaseRankingEngine):
    """
    Deterministic ranking service calculating standard competition ranks ("1224" rule)
    across semester GPA, cumulative CGPA, and individual course GPs.
    """

    def __init__(self):
        self.engine = DeterministicRankingEngine()

    def calculate_ranks(
        self,
        students: List[Dict[str, Any]],
        courses: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Computes semester, cumulative, and subject rankings for all students.
        """
        courses = courses or []
        logger.info(f"Computing standard competition ranks for {len(students)} students across {len(courses)} courses.")
        result = self.engine.rank_all(students=students, courses=courses)
        return result["students"]

    def get_full_ranking_report(
        self,
        students: List[Dict[str, Any]],
        courses: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Returns complete ranking mappings for semester, cumulative, and subjects.
        """
        courses = courses or []
        return self.engine.rank_all(students=students, courses=courses)
