"""
Student Report Data Builder — Scoped strictly to the selected student.

Consumes verified dataset from ResultSession and existing analysis/ranking services
to compile all student-specific metrics with zero calculation duplication.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from apps.core.exceptions import StudentNotFoundError
from apps.processing.analysis.service import AnalysisEngineService
from apps.processing.ranking.service import RankingEngineService
from apps.sessions_manager.models import ResultSession
from .base import find_student_in_dataset, normalize_student_id, safe_float

logger = logging.getLogger(__name__)


def build_student_report_data(session: ResultSession, student_id: str) -> Dict[str, Any]:
    """
    Builds structured export data for a single student's analysis report.

    Args:
        session: Verified ResultSession instance
        student_id: Raw or formatted Student ID

    Returns:
        Dict containing ONLY the selected student's report data.

    Raises:
        StudentNotFoundError: If student is not present in this session dataset.
    """
    parsed = session.parsed_dataset or {}
    students = parsed.get("students", [])
    courses = parsed.get("courses", [])

    target_student = find_student_in_dataset(students, student_id)
    if not target_student:
        raise StudentNotFoundError(f"Student ID '{student_id}' was not found in this result sheet.")

    target_id_clean = str(target_student.get("student_id", "")).strip()
    target_id_norm = normalize_student_id(target_id_clean)

    # 1. Deterministic Rankings
    ranking_service = RankingEngineService()
    ranking_report = ranking_service.get_full_ranking_report(students, courses)
    sem_ranks = ranking_report.get("semester_rankings", {})
    cum_ranks = ranking_report.get("cumulative_rankings", {})
    subj_ranks_map = ranking_report.get("subject_rankings", {})

    sem_info = sem_ranks.get(target_id_clean) or sem_ranks.get(target_id_norm) or {}
    cum_info = cum_ranks.get(target_id_clean) or cum_ranks.get(target_id_norm) or {}

    # 2. Deterministic Individual Analysis
    analysis_service = AnalysisEngineService()
    ind_analysis = analysis_service.calculate_individual_student(
        student=target_student,
        courses=courses,
        all_students=students,
    )

    # 3. Cohort Course Averages & Highest (for class comparison columns)
    cohort_stats = analysis_service.calculate_cohort_statistics(students=students, courses=courses)
    course_avg_map = {
        item.get("course_code"): item.get("average_gp")
        for item in cohort_stats.get("subject_analysis", [])
    }
    course_highest_map = {
        item.get("course_code"): item.get("highest_gp")
        for item in cohort_stats.get("subject_analysis", [])
    }

    # 4. Detailed Subject Breakdown
    course_map = {c.get("course_code"): c for c in courses}
    course_results = []
    subject_gps: List[float] = []

    for r in target_student.get("results", []):
        c_code = r.get("course_code", "")
        c_meta = course_map.get(c_code, {})
        c_title = c_meta.get("course_title", c_code)
        credits_val = safe_float(c_meta.get("credit_hours"), default=3.0) or 3.0
        gp_val = safe_float(r.get("grade_point"))
        lg_val = r.get("letter_grade", "")

        if gp_val is not None:
            subject_gps.append(gp_val)

        # Subject rank from ranking report
        subj_rank_info = subj_ranks_map.get(c_code, {}).get(target_id_clean) or subj_ranks_map.get(c_code, {}).get(target_id_norm) or {}
        subj_rank = subj_rank_info.get("rank")
        cohort_avg = course_avg_map.get(c_code)
        cohort_highest = course_highest_map.get(c_code)

        course_results.append({
            "course_code": c_code,
            "course_title": c_title,
            "credit": credits_val,
            "grade_point": gp_val,
            "letter_grade": lg_val,
            "subject_rank": subj_rank,
            "class_highest_gp": cohort_highest,
            "class_average_gp": cohort_avg,
            "status": r.get("status", "VALID"),
        })

    # 5. Summaries
    cur_sem = target_student.get("current_semester_summary") or {}
    cum_sem = target_student.get("cumulative_summary") or {}

    gpa_val = safe_float(cur_sem.get("gpa"), default=0.0) or 0.0
    cgpa_val = safe_float(cum_sem.get("cgpa"), default=0.0) if cum_sem else 0.0

    credits_attempted = safe_float(cur_sem.get("total_credit"), default=sum(c["credit"] for c in course_results)) or 0.0
    credits_earned = safe_float(cur_sem.get("earned_credit"), default=credits_attempted) or credits_attempted
    total_cum_credits = safe_float(cum_sem.get("earned_credit", cum_sem.get("total_credit")), default=credits_earned) or credits_earned

    # 6. Student-Specific Performance Stats
    highest_gp = max(subject_gps) if subject_gps else None
    lowest_gp = min(subject_gps) if subject_gps else None
    avg_gp = round(sum(subject_gps) / len(subject_gps), 2) if subject_gps else None

    highest_courses = [c["course_code"] for c in course_results if c["grade_point"] == highest_gp and highest_gp is not None]
    lowest_courses = [c["course_code"] for c in course_results if c["grade_point"] == lowest_gp and lowest_gp is not None]

    return {
        "report_type": "STUDENT_ANALYSIS",
        "student_info": {
            "student_id": target_student.get("student_id"),
            "student_name": target_student.get("student_name", "UNKNOWN"),
            "serial_no": target_student.get("serial_no"),
            "status": target_student.get("status", "VALID"),
        },
        "academic_summary": {
            "semester_gpa": gpa_val,
            "credits_attempted": credits_attempted,
            "credits_earned": credits_earned,
            "semester_rank": sem_info.get("rank"),
            "semester_percentile": sem_info.get("percentile"),
            "semester_result_status": cur_sem.get("result_status", "PASSED"),
            "semester_remarks": cur_sem.get("remarks", ""),
            "cumulative_cgpa": cgpa_val,
            "total_credits_earned": total_cum_credits,
            "cumulative_rank": cum_info.get("rank"),
            "cumulative_percentile": cum_info.get("percentile"),
            "cumulative_result_status": cum_sem.get("result_status", "PASSED") if cum_sem else "PASSED",
            "cumulative_remarks": cum_sem.get("remarks", "") if cum_sem else "",
            "total_subjects": len(course_results),
        },
        "subject_results": course_results,
        "performance_statistics": {
            "highest_subject_gp": highest_gp,
            "highest_subject_courses": highest_courses,
            "lowest_subject_gp": lowest_gp,
            "lowest_subject_courses": lowest_courses,
            "average_subject_gp": avg_gp,
        },
        "metadata": {
            "institution": parsed.get("institution", "Jagannath University"),
            "department": parsed.get("program", "Department of Computer Science & Engineering"),
            "semester": parsed.get("semester", ""),
            "exam_session": parsed.get("exam_session", ""),
            "original_filename": session.original_filename,
        },
    }
