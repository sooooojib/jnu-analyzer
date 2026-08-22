"""
Comparison Report Data Builder — Scoped strictly to 2-Student Head-to-Head Comparison.

Consumes verified dataset from ResultSession and existing comparison services
to compile comparative metrics with zero calculation duplication.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from apps.core.exceptions import StudentNotFoundError
from apps.processing.analysis.service import AnalysisEngineService
from apps.processing.comparison.service import ComparisonEngineService
from apps.processing.ranking.service import RankingEngineService
from apps.sessions_manager.models import ResultSession
from .base import find_student_in_dataset, safe_float

logger = logging.getLogger(__name__)


def build_comparison_report_data(
    session: ResultSession,
    student_a_id: str,
    student_b_id: str,
) -> Dict[str, Any]:
    """
    Builds structured export data for a 2-student comparative analysis report.

    Args:
        session: Verified ResultSession instance
        student_a_id: Student A ID
        student_b_id: Student B ID

    Returns:
        Dict containing ONLY the two compared students' comparative report data.

    Raises:
        StudentNotFoundError: If either student is not found in this dataset.
    """
    parsed = session.parsed_dataset or {}
    students = parsed.get("students", [])
    courses = parsed.get("courses", [])

    student_a = find_student_in_dataset(students, student_a_id)
    student_b = find_student_in_dataset(students, student_b_id)

    if not student_a or not student_b:
        missing = []
        if not student_a:
            missing.append(f"Student A '{student_a_id}'")
        if not student_b:
            missing.append(f"Student B '{student_b_id}'")
        raise StudentNotFoundError(f"{' and '.join(missing)} was not found in this result sheet.")

    # 1. Deterministic Rankings & Cohort Analytics
    ranking_service = RankingEngineService()
    ranking_data = ranking_service.get_full_ranking_report(students, courses)

    analysis_service = AnalysisEngineService()
    cohort_data = analysis_service.calculate_cohort_statistics(students=students, courses=courses)

    # 2. Deterministic Comparison Engine
    comparison_service = ComparisonEngineService()
    comp_result = comparison_service.compare_students(
        student_a=student_a,
        student_b=student_b,
        courses=courses,
        cohort_data=cohort_data,
        ranking_data=ranking_data,
    )

    prof_a = comp_result.get("student_a") or {}
    prof_b = comp_result.get("student_b") or {}
    deltas = comp_result.get("deltas") or {}
    tally = comp_result.get("subject_tally") or {}
    courses_comp = comp_result.get("course_comparison") or []

    # 3. Clean Course Comparisons
    clean_courses = []
    for c in courses_comp:
        clean_courses.append({
            "course_code": c.get("course_code"),
            "course_title": c.get("course_title"),
            "credits": safe_float(c.get("credits"), default=3.0),
            "student_a_gp": safe_float(c.get("student_a_gp")),
            "student_a_grade": c.get("student_a_grade", ""),
            "student_b_gp": safe_float(c.get("student_b_gp")),
            "student_b_grade": c.get("student_b_grade", ""),
            "delta_gp": safe_float(c.get("delta_gp")),
            "better_performer": c.get("better_performer", "N/A"),
            "cohort_average_gp": safe_float(c.get("cohort_average_gp")),
        })

    return {
        "report_type": "STUDENT_COMPARISON",
        "student_a": {
            "student_id": prof_a.get("id"),
            "student_name": prof_a.get("name"),
            "semester_gpa": safe_float(prof_a.get("gpa"), default=0.0),
            "cumulative_cgpa": safe_float(prof_a.get("cgpa"), default=0.0),
            "semester_rank": prof_a.get("semester_rank"),
            "semester_percentile": prof_a.get("semester_percentile"),
            "cumulative_rank": prof_a.get("cumulative_rank"),
            "cumulative_percentile": prof_a.get("cumulative_percentile"),
            "credits_earned": safe_float(prof_a.get("credits_earned")),
            "result_status": prof_a.get("result_status", "PASSED"),
        },
        "student_b": {
            "student_id": prof_b.get("id"),
            "student_name": prof_b.get("name"),
            "semester_gpa": safe_float(prof_b.get("gpa"), default=0.0),
            "cumulative_cgpa": safe_float(prof_b.get("cgpa"), default=0.0),
            "semester_rank": prof_b.get("semester_rank"),
            "semester_percentile": prof_b.get("semester_percentile"),
            "cumulative_rank": prof_b.get("cumulative_rank"),
            "cumulative_percentile": prof_b.get("cumulative_percentile"),
            "credits_earned": safe_float(prof_b.get("credits_earned")),
            "result_status": prof_b.get("result_status", "PASSED"),
        },
        "deltas": {
            "gpa_difference": safe_float(deltas.get("gpa_diff")),
            "cgpa_difference": safe_float(deltas.get("cgpa_diff")),
            "average_gp_difference": safe_float(deltas.get("average_gp_diff")),
            "semester_rank_difference": deltas.get("semester_rank_diff"),
            "cumulative_rank_difference": deltas.get("cumulative_rank_diff"),
        },
        "subject_tally": {
            "student_a_wins": tally.get("a_better_count", 0),
            "student_b_wins": tally.get("b_better_count", 0),
            "ties": tally.get("tied_count", 0),
            "student_a_better_courses": tally.get("subjects_a_better", []),
            "student_b_better_courses": tally.get("subjects_b_better", []),
            "tied_courses": tally.get("subjects_tied", []),
            "total_courses_compared": len(clean_courses),
        },
        "course_comparison": clean_courses,
        "metadata": {
            "institution": parsed.get("institution", "Jagannath University"),
            "department": parsed.get("program", "Department of Computer Science & Engineering"),
            "semester": parsed.get("semester", ""),
            "exam_session": parsed.get("exam_session", ""),
            "original_filename": session.original_filename,
        },
    }
