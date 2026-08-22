"""
Deterministic Ranking Engine for Academic Result Sheets.

Implements:
  1. Current-Semester Ranking (GPA)
  2. Cumulative Ranking (CGPA from sheet)
  3. Subject-Specific Ranking (Course GP)

Tie-Ranking Method Documentation:
  Standard Competition Ranking ("1224" Rule):
  - Items that tie receive the same rank.
  - The subsequent rank increments by the count of tied items.
  - Example: Scores [3.90, 3.90, 3.85, 3.80] -> Ranks [1, 1, 3, 4].

Data Sanitation Rules:
  - Missing or None values are unranked (rank=None).
  - Invalid values (marked INVALID or unusable in calculations) are never ranked.
  - Duplicate student IDs are deduplicated, preserving the highest-confidence valid record.
  - Historical semesters are never reconstructed; cumulative ranks use data in current sheet.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _safe_numeric(val: Any) -> Optional[float]:
    """Safely converts string, Decimal, int, float to float. Returns None if invalid/empty."""
    if val is None or val == "":
        return None
    try:
        f = float(val)
        return round(f, 4)
    except (ValueError, TypeError):
        return None


def deduplicate_students(students: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates student records by student_id, preserving the most complete
    and valid record (or highest confidence).
    """
    seen: Dict[str, Dict[str, Any]] = {}
    for student in students:
        s_id = str(student.get("student_id", "")).strip()
        if not s_id:
            continue

        if s_id not in seen:
            seen[s_id] = student
        else:
            existing = seen[s_id]
            # Replace if existing is INVALID but current is VALID
            if existing.get("status") == "INVALID" and student.get("status") != "INVALID":
                seen[s_id] = student
            # Or if current has higher confidence
            elif float(student.get("confidence", 0.0)) > float(existing.get("confidence", 0.0)):
                seen[s_id] = student

    return list(seen.values())


def compute_standard_competition_ranks(
    items: List[Tuple[str, Optional[float], bool]]
) -> Dict[str, Dict[str, Any]]:
    """
    Computes Standard Competition ("1224") Ranking for a list of (entity_id, score, is_valid).

    Args:
        items: List of (id, score, is_valid_flag)

    Returns:
        Dict mapping entity_id to:
          {
            "rank": Optional[int],
            "score": Optional[float],
            "total_ranked": int,
            "percentile": Optional[float],
            "is_tied": bool,
            "is_ranked": bool,
          }
    """
    # Filter only valid items with non-null scores
    valid_items = [
        (ent_id, score)
        for ent_id, score, is_valid in items
        if is_valid and score is not None
    ]

    total_ranked = len(valid_items)
    results: Dict[str, Dict[str, Any]] = {}

    # Initialize unranked/invalid items
    for ent_id, score, is_valid in items:
        if not is_valid or score is None:
            results[ent_id] = {
                "rank": None,
                "score": score,
                "total_ranked": total_ranked,
                "percentile": None,
                "is_tied": False,
                "is_ranked": False,
                "unranked_reason": "Invalid or missing score",
            }

    if not valid_items:
        return results

    # Sort descending by score
    sorted_items = sorted(valid_items, key=lambda x: x[1], reverse=True)

    # Apply Standard Competition ("1224") Ranking
    current_rank = 1
    i = 0
    while i < total_ranked:
        curr_score = sorted_items[i][1]
        # Count all items with the exact same score (ties)
        tie_count = 0
        while i + tie_count < total_ranked and sorted_items[i + tie_count][1] == curr_score:
            tie_count += 1

        is_tied = tie_count > 1
        percentile = round(((total_ranked - current_rank + 1) / total_ranked) * 100, 1)

        for t in range(tie_count):
            ent_id = sorted_items[i + t][0]
            results[ent_id] = {
                "rank": current_rank,
                "score": curr_score,
                "total_ranked": total_ranked,
                "percentile": percentile,
                "is_tied": is_tied,
                "is_ranked": True,
            }

        # Advance rank by number of tied items ("1224" rule)
        current_rank += tie_count
        i += tie_count

    return results


class DeterministicRankingEngine:
    """
    Calculates exact rankings for Current Semester (GPA), Cumulative (CGPA),
    and Individual Subjects (GP).
    """

    @classmethod
    def rank_current_semester(
        cls, students: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Ranks students by current-semester GPA.
        """
        items = []
        for s in students:
            s_id = str(s.get("student_id", "")).strip()
            cur = s.get("current_semester_summary") or {}
            gpa = _safe_numeric(cur.get("gpa"))
            # Check if student or gpa is invalid
            is_valid = (
                s.get("status") != "INVALID" and
                cur.get("status") != "INVALID" and
                (gpa is not None and 0.0 <= gpa <= 4.0)
            )
            items.append((s_id, gpa, is_valid))

        return compute_standard_competition_ranks(items)

    @classmethod
    def rank_cumulative(
        cls, students: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Ranks students by cumulative CGPA (using values directly from current sheet).
        """
        items = []
        for s in students:
            s_id = str(s.get("student_id", "")).strip()
            cum = s.get("cumulative_summary") or {}
            cgpa = _safe_numeric(cum.get("cgpa"))
            is_valid = (
                s.get("status") != "INVALID" and
                cum.get("status") != "INVALID" and
                (cgpa is not None and 0.0 <= cgpa <= 4.0)
            )
            items.append((s_id, cgpa, is_valid))

        return compute_standard_competition_ranks(items)

    @classmethod
    def rank_subjects(
        cls,
        students: List[Dict[str, Any]],
        courses: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Ranks students within each course column by course GP.
        Returns: { course_code: { student_id: ranking_dict } }
        """
        course_rankings: Dict[str, Dict[str, Dict[str, Any]]] = {}

        for course in courses:
            c_code = course.get("course_code", "")
            items = []
            for s in students:
                s_id = str(s.get("student_id", "")).strip()
                res = next((r for r in s.get("results", []) if r.get("course_code") == c_code), None)
                if res:
                    gp = _safe_numeric(res.get("grade_point"))
                    is_valid = (
                        res.get("status") != "INVALID" and
                        (gp is not None and 0.0 <= gp <= 4.0)
                    )
                    items.append((s_id, gp, is_valid))
                else:
                    items.append((s_id, None, False))

            course_rankings[c_code] = compute_standard_competition_ranks(items)

        return course_rankings

    @classmethod
    def rank_all(
        cls,
        students: List[Dict[str, Any]],
        courses: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Deduplicates students and computes full semester, cumulative, and subject rankings.
        """
        clean_students = deduplicate_students(students)

        sem_ranks = cls.rank_current_semester(clean_students)
        cum_ranks = cls.rank_cumulative(clean_students)
        subj_ranks = cls.rank_subjects(clean_students, courses)

        # Augment students with computed rankings
        augmented_students = []
        for s in clean_students:
            s_copy = dict(s)
            s_id = str(s_copy.get("student_id", "")).strip()

            sem_info = sem_ranks.get(s_id, {})
            cum_info = cum_ranks.get(s_id, {})

            if "semester_result" not in s_copy:
                s_copy["semester_result"] = {}
            s_copy["semester_result"]["semester_rank"] = sem_info.get("rank")
            s_copy["semester_result"]["semester_percentile"] = sem_info.get("percentile")

            if "cumulative_result" not in s_copy:
                s_copy["cumulative_result"] = {}
            s_copy["cumulative_result"]["cumulative_rank"] = cum_info.get("rank")
            s_copy["cumulative_result"]["cumulative_percentile"] = cum_info.get("percentile")

            # Augment results with subject-specific rank
            augmented_results = []
            for r in s_copy.get("results", []):
                r_copy = dict(r)
                c_code = r_copy.get("course_code", "")
                c_rank_info = subj_ranks.get(c_code, {}).get(s_id, {})
                r_copy["subject_rank"] = c_rank_info.get("rank")
                r_copy["subject_percentile"] = c_rank_info.get("percentile")
                r_copy["is_topper"] = c_rank_info.get("rank") == 1
                augmented_results.append(r_copy)

            s_copy["results"] = augmented_results
            augmented_students.append(s_copy)

        return {
            "students": augmented_students,
            "semester_rankings": sem_ranks,
            "cumulative_rankings": cum_ranks,
            "subject_rankings": subj_ranks,
            "total_students": len(clean_students),
        }
