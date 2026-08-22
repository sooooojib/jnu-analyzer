"""
AnalysisEngineService — Orchestrates deterministic statistical analysis across verified result datasets.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import BaseAnalysisEngine
from .engine import DeterministicAnalysisEngine

logger = logging.getLogger(__name__)


class AnalysisEngineService(BaseAnalysisEngine):
    """
    Service implementing deterministic statistical analysis for:
      - Individual Student Analysis (GP, GPA, CGPA, Subject Ranks)
      - Class Semester Analysis (Mean, Median, Mode, Min, Max GPA)
      - Cumulative Analysis (Mean, Median, Mode, Min, Max CGPA)
      - Subject Analysis (Mean, Median, Mode, Min, Max GP, Toppers)
    """

    def __init__(self):
        self.engine = DeterministicAnalysisEngine()

    def calculate_cohort_statistics(
        self,
        students: List[Dict[str, Any]],
        courses: List[Dict[str, Any]],
        selected_student_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Computes complete cohort statistical analytics.
        """
        logger.info(f"Computing deterministic cohort statistical metrics for {len(students)} students.")

        class_stats = self.engine.analyze_class_semester(students)
        cumulative_stats = self.engine.analyze_cumulative_cohort(students)
        subject_stats = self.engine.analyze_subjects(students, courses, selected_student_id)

        # Compute deterministic ranking maps for both semester and cumulative
        from apps.processing.ranking.engine import DeterministicRankingEngine
        sem_ranks = DeterministicRankingEngine.rank_current_semester(students)
        cum_ranks = DeterministicRankingEngine.rank_cumulative(students)

        # Build student leaderboard with both semester and cumulative ranks
        leaderboard = []
        for s in students:
            s_id = str(s.get("student_id", "")).strip()
            cur = s.get("current_semester_summary") or {}
            cum = s.get("cumulative_summary") or {}
            gpa = cur.get("gpa")
            cgpa = cum.get("cgpa")
            sem_info = sem_ranks.get(s_id, {})
            cum_info = cum_ranks.get(s_id, {})
            leaderboard.append({
                "student_id": s_id,
                "student_name": s.get("student_name", ""),
                "gpa": float(gpa) if gpa is not None else 0.0,
                "cgpa": float(cgpa) if cgpa is not None else 0.0,
                "semester_rank": sem_info.get("rank"),
                "semester_percentile": sem_info.get("percentile"),
                "cumulative_rank": cum_info.get("rank"),
                "cumulative_percentile": cum_info.get("percentile"),
                "status": s.get("status", "VALID"),
            })

        # By default, sort by semester GPA descending
        leaderboard.sort(key=lambda x: (x["gpa"], x["cgpa"]), reverse=True)
        for item in leaderboard:
            # Use the deterministic competition rank; positional index is NOT a valid rank substitute
            item["rank"] = item.get("semester_rank")

        return {
            "class_analysis": class_stats,
            "cumulative_analysis": cumulative_stats,
            "subject_analysis": subject_stats,
            "student_leaderboard": leaderboard,
            # Backward-compatible mappings
            "summary_metrics": {
                "count": class_stats["total_students"],
                "mean": class_stats["average_gpa"],
                "median": class_stats["median_gpa"],
                "mode": class_stats["mode_gpa"],
                "std_dev": class_stats["std_dev_gpa"],
                "min": class_stats["lowest_gpa"],
                "max": class_stats["highest_gpa"],
            },
            "gpa_distribution_histogram": class_stats["distribution"],
            "subject_wise_breakdown": subject_stats,
            "leaderboard": leaderboard,
        }

    def calculate_individual_student(
        self,
        student: Dict[str, Any],
        courses: List[Dict[str, Any]],
        all_students: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Computes detailed individual analysis for a specific student.
        """
        return self.engine.analyze_individual_student(
            student=student,
            courses=courses,
            all_students=all_students,
        )
