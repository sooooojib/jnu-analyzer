"""
Class Report Data Builder — Scoped strictly to the Class-wide Cohort Analysis.

Consumes verified dataset from ResultSession and existing analysis services
to compile cohort metrics with zero calculation duplication.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from apps.processing.analysis.service import AnalysisEngineService
from apps.sessions_manager.models import ResultSession
from .base import safe_float

logger = logging.getLogger(__name__)


def build_class_report_data(session: ResultSession) -> Dict[str, Any]:
    """
    Builds structured export data for class-wide cohort analytics report.

    Args:
        session: Verified ResultSession instance

    Returns:
        Dict containing ONLY class-level cohort analysis data.
    """
    parsed = session.parsed_dataset or {}
    students = parsed.get("students", [])
    courses = parsed.get("courses", [])

    # 1. Deterministic Cohort Statistics & Rankings
    analysis_service = AnalysisEngineService()
    cohort_stats = analysis_service.calculate_cohort_statistics(students=students, courses=courses)

    class_analysis = cohort_stats.get("class_analysis") or {}
    cumulative_analysis = cohort_stats.get("cumulative_analysis") or {}
    subject_analyses = cohort_stats.get("subject_analysis") or []
    leaderboard = cohort_stats.get("student_leaderboard") or []

    # 2. Format Subject-wise Analysis cleanly for export
    subject_data: List[Dict[str, Any]] = []
    for s in subject_analyses:
        toppers = [
            {
                "student_id": t.get("student_id"),
                "student_name": t.get("student_name"),
                "grade_point": safe_float(t.get("gp")),
                "letter_grade": t.get("letter_grade", ""),
            }
            for t in s.get("highest_performing_students", [])
        ]

        subject_data.append({
            "course_code": s.get("course_code"),
            "course_title": s.get("course_title"),
            "credit_hours": safe_float(s.get("credit_hours"), default=3.0),
            "number_of_students": s.get("number_of_students", 0),
            "average_gp": safe_float(s.get("average_gp")),
            "median_gp": safe_float(s.get("median_gp")),
            "mode_gp": safe_float(s.get("mode_gp")),
            "highest_gp": safe_float(s.get("highest_gp")),
            "lowest_gp": safe_float(s.get("lowest_gp")),
            "std_dev_gp": safe_float(s.get("std_dev_gp")),
            "toppers": toppers,
            "grade_distribution": s.get("grade_counts", {}),
        })

    # 3. Format Student Rankings / Leaderboard
    rankings_data: List[Dict[str, Any]] = []
    for item in leaderboard:
        rankings_data.append({
            "rank": item.get("rank"),
            "student_id": item.get("student_id"),
            "student_name": item.get("student_name"),
            "gpa": safe_float(item.get("gpa"), default=0.0),
            "cgpa": safe_float(item.get("cgpa"), default=0.0),
            "semester_rank": item.get("semester_rank"),
            "cumulative_rank": item.get("cumulative_rank"),
            "status": item.get("status", "VALID"),
        })

    # 4. Format Distribution Histograms
    def _format_dist_item(item: Dict[str, Any]) -> Dict[str, Any]:
        bracket = str(item.get("bracket", "")).strip()
        grade_tier = item.get("grade_tier") or item.get("grade") or ""
        gpa_range = item.get("gpa_range") or item.get("range") or ""

        if not grade_tier or not gpa_range:
            if "(" in bracket and ")" in bracket:
                parts = bracket.split("(", 1)
                grade_tier = parts[0].strip()
                gpa_range = parts[1].rstrip(")").strip()
            elif bracket:
                grade_tier = bracket
                gpa_range = "—"

        return {
            "bracket": bracket or f"{grade_tier} ({gpa_range})",
            "grade_tier": grade_tier,
            "gpa_range": gpa_range,
            "count": item.get("count", 0),
            "percentage": safe_float(item.get("percentage"), default=0.0) or 0.0,
        }

    formatted_gpa_dist = [_format_dist_item(d) for d in class_analysis.get("distribution", [])]
    formatted_cgpa_dist = [_format_dist_item(d) for d in cumulative_analysis.get("distribution", [])]

    return {
        "report_type": "CLASS_ANALYSIS",
        "class_overview": {
            "total_students": class_analysis.get("total_students", len(students)),
            "students_with_gpa_count": class_analysis.get("students_with_gpa_count", 0),
            "total_subjects": len(courses),
            "average_gpa": safe_float(class_analysis.get("average_gpa")),
            "median_gpa": safe_float(class_analysis.get("median_gpa")),
            "mode_gpa": safe_float(class_analysis.get("mode_gpa")),
            "highest_gpa": safe_float(class_analysis.get("highest_gpa")),
            "lowest_gpa": safe_float(class_analysis.get("lowest_gpa")),
            "std_dev_gpa": safe_float(class_analysis.get("std_dev_gpa")),
            "gpa_distribution": formatted_gpa_dist,
        },
        "cumulative_overview": {
            "total_students": cumulative_analysis.get("total_students", len(students)),
            "students_with_cgpa_count": cumulative_analysis.get("students_with_cgpa_count", 0),
            "average_cgpa": safe_float(cumulative_analysis.get("average_cgpa")),
            "median_cgpa": safe_float(cumulative_analysis.get("median_cgpa")),
            "mode_cgpa": safe_float(cumulative_analysis.get("mode_cgpa")),
            "highest_cgpa": safe_float(cumulative_analysis.get("highest_cgpa")),
            "lowest_cgpa": safe_float(cumulative_analysis.get("lowest_cgpa")),
            "std_dev_cgpa": safe_float(cumulative_analysis.get("std_dev_cgpa")),
            "cgpa_distribution": formatted_cgpa_dist,
        },
        "student_rankings": rankings_data,
        "subject_analysis": subject_data,
        "metadata": {
            "institution": parsed.get("institution", "Jagannath University"),
            "department": parsed.get("program", "Department of Computer Science & Engineering"),
            "semester": parsed.get("semester", ""),
            "exam_session": parsed.get("exam_session", ""),
            "original_filename": session.original_filename,
        },
    }
