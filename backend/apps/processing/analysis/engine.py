"""
Deterministic Analysis Engine for Academic Result Sheets.

Calculates exact statistical distributions for:
  - Individual Student Analysis (GP, GPA, CGPA, highest/lowest/avg subject GP, ranks)
  - Class Semester Analysis (Mean, Median, Mode, Min, Max of Semester GPA)
  - Cumulative Analysis (Mean, Median, Mode, Min, Max of Cumulative CGPA)
  - Subject Analysis (Mean, Median, Mode, Min, Max GP, Toppers, Grade Counts, Ranks)

Strict Nomenclature:
  - GP (Grade Point): numerical score for an individual course (e.g. 4.00)
  - GPA: Grade Point Average for the current semester
  - CGPA: Cumulative Grade Point Average across all semesters to date
"""

from __future__ import annotations

import collections
import statistics
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple


def _safe_float(val: Any) -> Optional[float]:
    """Safely converts string, Decimal, int, float to float. Returns None if invalid/empty."""
    if val is None:
        return None
    try:
        f = float(val)
        return round(f, 4)
    except (ValueError, TypeError):
        return None


def calculate_descriptive_stats(values: List[float]) -> Dict[str, float]:
    """
    Computes mean, median, mode, min, max, and count for a list of floats.
    Never fails on small or empty datasets.
    """
    if not values:
        return {
            "count": 0,
            "mean": 0.0,
            "median": 0.0,
            "mode": 0.0,
            "min": 0.0,
            "max": 0.0,
            "std_dev": 0.0,
        }

    clean_vals = sorted(values)
    count = len(clean_vals)
    mean_val = round(sum(clean_vals) / count, 2)
    median_val = round(statistics.median(clean_vals), 2)

    # Mode calculation (safely returns most frequent or median if uniform)
    freq = collections.Counter(clean_vals)
    max_freq = max(freq.values())
    modes = [val for val, count_val in freq.items() if count_val == max_freq]
    mode_val = round(modes[0], 2)

    min_val = round(clean_vals[0], 2)
    max_val = round(clean_vals[-1], 2)
    std_dev_val = round(statistics.stdev(clean_vals), 2) if count > 1 else 0.0

    return {
        "count": count,
        "mean": mean_val,
        "median": median_val,
        "mode": mode_val,
        "min": min_val,
        "max": max_val,
        "std_dev": std_dev_val,
    }


def compute_distribution_histogram(values: List[float], max_scale: float = 4.0) -> List[Dict[str, Any]]:
    """
    Groups GPA/CGPA/GP values into standard academic brackets.
    """
    if not values:
        return []

    total = len(values)
    brackets = [
        {"label": "A+ (4.00)", "min": 4.00, "max": 4.01, "count": 0},
        {"label": "A (3.75–3.99)", "min": 3.75, "max": 4.00, "count": 0},
        {"label": "A- (3.50–3.74)", "min": 3.50, "max": 3.75, "count": 0},
        {"label": "B+ (3.25–3.49)", "min": 3.25, "max": 3.50, "count": 0},
        {"label": "B (3.00–3.24)", "min": 3.00, "max": 3.25, "count": 0},
        {"label": "B- (2.75–2.99)", "min": 2.75, "max": 3.00, "count": 0},
        {"label": "C+ (2.50–2.74)", "min": 2.50, "max": 2.75, "count": 0},
        {"label": "C (2.25–2.49)", "min": 2.25, "max": 2.50, "count": 0},
        {"label": "D (2.00–2.24)", "min": 2.00, "max": 2.25, "count": 0},
        {"label": "F (< 2.00)", "min": 0.00, "max": 2.00, "count": 0},
    ]

    for val in values:
        for b in brackets:
            if b["min"] <= val < b["max"]:
                b["count"] += 1
                break

    return [
        {
            "bracket": b["label"],
            "count": b["count"],
            "percentage": round((b["count"] / total) * 100, 1) if total > 0 else 0.0,
        }
        for b in brackets
    ]


class DeterministicAnalysisEngine:
    """
    Core statistical computation engine.
    """

    # -----------------------------------------------------------------------
    # 1. Individual Student Analysis
    # -----------------------------------------------------------------------

    @staticmethod
    def analyze_individual_student(
        student: Dict[str, Any],
        courses: List[Dict[str, Any]],
        all_students: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Calculates individual student analysis:
          - Student ID, Name
          - Every subject (course code, name, credit, GP, letter grade, subject rank)
          - Current-semester GPA & Result Status
          - Cumulative CGPA & Result Status (directly from sheet)
          - Highest subject GP
          - Lowest subject GP
          - Average subject GP
        """
        student_id = str(student.get("student_id", "")).strip()
        student_name = student.get("student_name", "UNKNOWN")
        results = student.get("results", [])

        course_map = {c.get("course_code"): c for c in courses}
        all_students = all_students or [student]

        # Analyze every subject for this student
        subject_breakdown = []
        subject_gps: List[float] = []

        for res in results:
            c_code = res.get("course_code", "")
            c_meta = course_map.get(c_code, {})
            c_title = c_meta.get("course_title", c_code)
            c_credit = _safe_float(c_meta.get("credit_hours")) or 3.0
            gp = _safe_float(res.get("grade_point"))
            lg = res.get("letter_grade", "")
            status_val = res.get("status", "VALID")

            if gp is not None:
                subject_gps.append(gp)

            # Compute rank of this student in this specific subject
            subject_rank = 1
            cohort_subject_gps = []
            for other_s in all_students:
                for other_r in other_s.get("results", []):
                    if other_r.get("course_code") == c_code:
                        other_gp = _safe_float(other_r.get("grade_point"))
                        if other_gp is not None:
                            cohort_subject_gps.append(other_gp)
                            if gp is not None and other_gp > gp:
                                subject_rank += 1
                        break

            avg_cohort_gp = round(sum(cohort_subject_gps) / len(cohort_subject_gps), 2) if cohort_subject_gps else gp

            subject_breakdown.append({
                "course_code": c_code,
                "course_title": c_title,
                "credit": c_credit,
                "gp": gp,
                "letter_grade": lg,
                "subject_rank": subject_rank,
                "cohort_average_gp": avg_cohort_gp,
                "status": status_val,
            })

        # Highest, Lowest, Average GP
        highest_gp = max(subject_gps) if subject_gps else None
        lowest_gp = min(subject_gps) if subject_gps else None
        avg_gp = round(sum(subject_gps) / len(subject_gps), 2) if subject_gps else None

        highest_courses = [s["course_code"] for s in subject_breakdown if s["gp"] == highest_gp]
        lowest_courses = [s["course_code"] for s in subject_breakdown if s["gp"] == lowest_gp]

        # Current semester summary
        cur_sem = student.get("current_semester_summary") or {}
        gpa_val = _safe_float(cur_sem.get("gpa")) or 0.0

        # Cumulative summary (directly from sheet)
        cum_sem = student.get("cumulative_summary") or {}
        cgpa_val = _safe_float(cum_sem.get("cgpa")) or 0.0

        return {
            "student_id": student_id,
            "student_name": student_name,
            "serial_no": student.get("serial_no"),
            "status": student.get("status", "VALID"),
            "subjects": subject_breakdown,
            "current_semester": {
                "gpa": gpa_val,
                "total_credit": _safe_float(cur_sem.get("total_credit")),
                "earned_credit": _safe_float(cur_sem.get("earned_credit")),
                "grade_points": _safe_float(cur_sem.get("grade_points")),
                "result_status": cur_sem.get("result_status", "PASSED"),
                "remarks": cur_sem.get("remarks", ""),
            },
            "cumulative": {
                "cgpa": cgpa_val,
                "total_credit": _safe_float(cum_sem.get("total_credit")),
                "earned_credit": _safe_float(cum_sem.get("earned_credit")),
                "grade_points": _safe_float(cum_sem.get("grade_points")),
                "result_status": cum_sem.get("result_status", "PASSED"),
                "remarks": cum_sem.get("remarks", ""),
            },
            "subject_gp_analysis": {
                "highest_subject_gp": highest_gp,
                "highest_subject_courses": highest_courses,
                "lowest_subject_gp": lowest_gp,
                "lowest_subject_courses": lowest_courses,
                "average_subject_gp": avg_gp,
            },
        }

    # -----------------------------------------------------------------------
    # 2. Class Analysis (Current Semester)
    # -----------------------------------------------------------------------

    @staticmethod
    def analyze_class_semester(students: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates class-level statistics for current semester GPA:
          - Total students
          - Average current-semester GPA
          - Median current-semester GPA
          - Mode current-semester GPA
          - Highest GPA
          - Lowest GPA
          - Distribution histogram
        """
        semester_gpas: List[float] = []
        for s in students:
            cur = s.get("current_semester_summary") or {}
            gpa = _safe_float(cur.get("gpa"))
            if gpa is not None:
                semester_gpas.append(gpa)

        stats = calculate_descriptive_stats(semester_gpas)
        histogram = compute_distribution_histogram(semester_gpas)

        return {
            "total_students": len(students),
            "students_with_gpa_count": len(semester_gpas),
            "average_gpa": stats["mean"],
            "median_gpa": stats["median"],
            "mode_gpa": stats["mode"],
            "highest_gpa": stats["max"],
            "lowest_gpa": stats["min"],
            "std_dev_gpa": stats["std_dev"],
            "distribution": histogram,
        }

    # -----------------------------------------------------------------------
    # 3. Cumulative Analysis
    # -----------------------------------------------------------------------

    @staticmethod
    def analyze_cumulative_cohort(students: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates cohort statistics directly from the cumulative values in the sheet:
          - Total students with cumulative data
          - Average cumulative CGPA
          - Median cumulative CGPA
          - Mode cumulative CGPA
          - Highest cumulative CGPA
          - Lowest cumulative CGPA
          - Cumulative distribution histogram
        """
        cumulative_cgpas: List[float] = []
        for s in students:
            cum = s.get("cumulative_summary") or {}
            cgpa = _safe_float(cum.get("cgpa"))
            if cgpa is not None:
                cumulative_cgpas.append(cgpa)

        stats = calculate_descriptive_stats(cumulative_cgpas)
        histogram = compute_distribution_histogram(cumulative_cgpas)

        return {
            "total_students": len(students),
            "students_with_cgpa_count": len(cumulative_cgpas),
            "average_cgpa": stats["mean"],
            "median_cgpa": stats["median"],
            "mode_cgpa": stats["mode"],
            "highest_cgpa": stats["max"],
            "lowest_cgpa": stats["min"],
            "std_dev_cgpa": stats["std_dev"],
            "distribution": histogram,
        }

    # -----------------------------------------------------------------------
    # 4. Subject Analysis
    # -----------------------------------------------------------------------

    @staticmethod
    def analyze_subjects(
        students: List[Dict[str, Any]],
        courses: List[Dict[str, Any]],
        selected_student_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calculates for each course:
          - Average GP
          - Median GP
          - Mode GP
          - Highest GP
          - Lowest GP
          - Number of students
          - Highest-performing student(s)
          - Letter grade distribution
          - Selected student's GP and subject rank
        """
        course_analyses = []

        for course in courses:
            c_code = course.get("course_code", "")
            c_title = course.get("course_title", c_code)
            c_credit = _safe_float(course.get("credit_hours")) or 3.0

            course_gps: List[float] = []
            student_results: List[Tuple[str, str, float, str]] = []  # (student_id, student_name, gp, letter_grade)
            grade_counts: Dict[str, int] = collections.defaultdict(int)

            for s in students:
                s_id = str(s.get("student_id", "")).strip()
                s_name = s.get("student_name", "UNKNOWN")
                res = next((r for r in s.get("results", []) if r.get("course_code") == c_code), None)
                if res:
                    gp = _safe_float(res.get("grade_point"))
                    lg = res.get("letter_grade", "")
                    if lg:
                        grade_counts[lg] += 1
                    if gp is not None:
                        course_gps.append(gp)
                        student_results.append((s_id, s_name, gp, lg))

            stats = calculate_descriptive_stats(course_gps)

            # Find top performers in this subject
            highest_gp = stats["max"]
            toppers = [
                {"student_id": s_id, "student_name": s_name, "gp": gp, "letter_grade": lg}
                for s_id, s_name, gp, lg in student_results
                if gp == highest_gp
            ]

            # Selected student specific rank, GP, letter grade, and diff from average in this course
            selected_gp = None
            selected_lg = None
            selected_rank = None
            selected_diff = None
            selected_percentile = None

            if selected_student_id:
                sel_clean = str(selected_student_id).strip()
                # Compute standard competition ranks for this subject
                from apps.processing.ranking.engine import compute_standard_competition_ranks
                subj_ranking_items = [(s_id, gp, True) for s_id, _, gp, _ in student_results]
                subj_ranks_map = compute_standard_competition_ranks(subj_ranking_items)

                for s_id, _, s_gp, s_lg in student_results:
                    if s_id == sel_clean:
                        selected_gp = s_gp
                        selected_lg = s_lg
                        r_info = subj_ranks_map.get(s_id, {})
                        selected_rank = r_info.get("rank")
                        selected_percentile = r_info.get("percentile")
                        if selected_gp is not None and stats["mean"] is not None:
                            selected_diff = round(selected_gp - stats["mean"], 2)
                        break

            GRADE_ORDER = {"A+": 1, "A": 2, "A-": 3, "B+": 4, "B": 5, "B-": 6, "C+": 7, "C": 8, "C-": 9, "D+": 10, "D": 11, "D-": 12, "F": 13, "I": 14, "W": 15}
            sorted_grade_counts = dict(sorted(grade_counts.items(), key=lambda item: (GRADE_ORDER.get(item[0].strip().upper(), 99), item[0])))

            course_analyses.append({
                "course_code": c_code,
                "course_title": c_title,
                "credit_hours": c_credit,
                "number_of_students": len(student_results),
                "average_gp": stats["mean"],
                "median_gp": stats["median"],
                "mode_gp": stats["mode"],
                "highest_gp": stats["max"],
                "lowest_gp": stats["min"],
                "std_dev_gp": stats["std_dev"],
                "highest_performing_students": toppers,
                "grade_counts": sorted_grade_counts,
                "selected_student_gp": selected_gp,
                "selected_student_letter_grade": selected_lg,
                "selected_student_subject_rank": selected_rank,
                "selected_student_diff_from_average": selected_diff,
                "selected_student_percentile": selected_percentile,
            })

        return course_analyses
