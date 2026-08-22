"""
Deterministic 2-Student Comparison Engine for Academic Result Sheets.

Calculates exact head-to-head metrics between two students in the same verified dataset:
  - Identity, Semester GPA, Cumulative CGPA, and Cohort Ranks
  - Subject-by-Subject GP, Letter Grades, and Deltas
  - Subjects where Student A performed better, Student B performed better, or equal
  - Average GP difference, Semester GPA difference, and Cumulative CGPA difference
  - Factual, strictly defined mathematical metrics with no unsupported subjective claims
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _safe_float(val: Any) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        return round(float(val), 4)
    except (ValueError, TypeError):
        return None


class DeterministicComparisonEngine:
    """
    Computes deterministic comparative analysis between two students in the same dataset.
    """

    @classmethod
    def compare_students(
        cls,
        student_a: Dict[str, Any],
        student_b: Dict[str, Any],
        courses: List[Dict[str, Any]],
        cohort_analytics: Optional[Dict[str, Any]] = None,
        ranking_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Runs comprehensive comparative analysis between student_a and student_b.
        """
        id_a = str(student_a.get("student_id", "")).strip()
        name_a = student_a.get("student_name", "UNKNOWN")
        id_b = str(student_b.get("student_id", "")).strip()
        name_b = student_b.get("student_name", "UNKNOWN")

        # 1. Summaries & GPAs
        cur_a = student_a.get("current_semester_summary") or {}
        cum_a = student_a.get("cumulative_summary") or {}
        gpa_a = _safe_float(cur_a.get("gpa")) or 0.0
        cgpa_a = _safe_float(cum_a.get("cgpa")) or 0.0

        cur_b = student_b.get("current_semester_summary") or {}
        cum_b = student_b.get("cumulative_summary") or {}
        gpa_b = _safe_float(cur_b.get("gpa")) or 0.0
        cgpa_b = _safe_float(cum_b.get("cgpa")) or 0.0

        # 2. Ranks & Percentiles
        sem_ranks = (ranking_data or {}).get("semester_rankings", {})
        cum_ranks = (ranking_data or {}).get("cumulative_rankings", {})

        rank_info_a = sem_ranks.get(id_a, {})
        rank_info_b = sem_ranks.get(id_b, {})
        sem_rank_a = rank_info_a.get("rank")  # None if unranked or missing
        sem_rank_b = rank_info_b.get("rank")
        sem_pct_a = rank_info_a.get("percentile")
        sem_pct_b = rank_info_b.get("percentile")

        cum_info_a = cum_ranks.get(id_a, {})
        cum_info_b = cum_ranks.get(id_b, {})
        cum_rank_a = cum_info_a.get("rank")
        cum_rank_b = cum_info_b.get("rank")
        cum_pct_a = cum_info_a.get("percentile")
        cum_pct_b = cum_info_b.get("percentile")

        # 3. Subject-by-Subject Comparison
        results_a = {r.get("course_code"): r for r in student_a.get("results", [])}
        results_b = {r.get("course_code"): r for r in student_b.get("results", [])}

        course_comparisons = []
        subjects_a_better = []
        subjects_b_better = []
        subjects_tied = []
        gp_diffs = []

        # Cohort subject averages map
        subj_avg_map = {}
        if cohort_analytics and "subject_analysis" in cohort_analytics:
            for s_item in cohort_analytics["subject_analysis"]:
                subj_avg_map[s_item.get("course_code")] = s_item.get("average_gp", 0.0)

        for course in courses:
            c_code = course.get("course_code", "")
            c_title = course.get("course_title", c_code)
            c_credits = _safe_float(course.get("credit_hours")) or 3.0

            res_a = results_a.get(c_code, {})
            res_b = results_b.get(c_code, {})

            gp_a = _safe_float(res_a.get("grade_point"))
            lg_a = res_a.get("letter_grade", "")
            gp_b = _safe_float(res_b.get("grade_point"))
            lg_b = res_b.get("letter_grade", "")

            delta_gp = None
            outcome = "N/A"

            if gp_a is not None and gp_b is not None:
                delta_gp = round(gp_a - gp_b, 2)
                gp_diffs.append(delta_gp)
                if delta_gp > 0:
                    outcome = "STUDENT_A"
                    subjects_a_better.append(c_code)
                elif delta_gp < 0:
                    outcome = "STUDENT_B"
                    subjects_b_better.append(c_code)
                else:
                    outcome = "TIED"
                    subjects_tied.append(c_code)
            elif gp_a is not None:
                outcome = "STUDENT_A"
                subjects_a_better.append(c_code)
            elif gp_b is not None:
                outcome = "STUDENT_B"
                subjects_b_better.append(c_code)

            course_comparisons.append({
                "course_code": c_code,
                "course_title": c_title,
                "credits": c_credits,
                "student_a_gp": gp_a,
                "student_a_grade": lg_a,
                "student_b_gp": gp_b,
                "student_b_grade": lg_b,
                "delta_gp": delta_gp,
                "better_performer": outcome,
                "cohort_average_gp": subj_avg_map.get(c_code),
            })

        # 4. Compute Aggregate Differences
        gpa_diff = round(gpa_a - gpa_b, 2)
        cgpa_diff = round(cgpa_a - cgpa_b, 2)
        avg_gp_diff = round(sum(gp_diffs) / len(gp_diffs), 2) if gp_diffs else 0.0
        
        # Rank difference (positive means Student A has higher standing / smaller rank number)
        sem_rank_diff = (sem_rank_b - sem_rank_a) if (sem_rank_a is not None and sem_rank_b is not None) else None
        cum_rank_diff = (cum_rank_b - cum_rank_a) if (cum_rank_a is not None and cum_rank_b is not None) else None

        return {
            "student_a": {
                "id": id_a,
                "name": name_a,
                "gpa": gpa_a,
                "cgpa": cgpa_a,
                "semester_rank": sem_rank_a,
                "semester_percentile": sem_pct_a,
                "cumulative_rank": cum_rank_a,
                "cumulative_percentile": cum_pct_a,
                "credits_earned": _safe_float(cur_a.get("earned_credit", cur_a.get("total_credit"))),
                "result_status": cur_a.get("result_status", "PASSED"),
            },
            "student_b": {
                "id": id_b,
                "name": name_b,
                "gpa": gpa_b,
                "cgpa": cgpa_b,
                "semester_rank": sem_rank_b,
                "semester_percentile": sem_pct_b,
                "cumulative_rank": cum_rank_b,
                "cumulative_percentile": cum_pct_b,
                "credits_earned": _safe_float(cur_b.get("earned_credit", cur_b.get("total_credit"))),
                "result_status": cur_b.get("result_status", "PASSED"),
            },
            "deltas": {
                "gpa_diff": gpa_diff,
                "cgpa_diff": cgpa_diff,
                "average_gp_diff": avg_gp_diff,
                "semester_rank_diff": sem_rank_diff,
                "cumulative_rank_diff": cum_rank_diff,
            },
            "subject_tally": {
                "a_better_count": len(subjects_a_better),
                "b_better_count": len(subjects_b_better),
                "tied_count": len(subjects_tied),
                "subjects_a_better": subjects_a_better,
                "subjects_b_better": subjects_b_better,
                "subjects_tied": subjects_tied,
            },
            "course_comparison": course_comparisons,
        }
