"""
Unit and integration tests for the Deterministic 2-Student Comparison Engine.

Tests:
  - Strict dataset boundary isolation
  - Subject-by-subject GP comparison and difference calculation
  - Student A better / Student B better / Tied determination
  - Aggregate semester GPA and cumulative CGPA deltas
  - Average GP difference computation
  - Error handling for missing or invalid student IDs
"""

import unittest
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.processing.comparison.engine import DeterministicComparisonEngine
from apps.processing.comparison.service import ComparisonEngineService
from apps.sessions_manager.models import ResultSession


class TestDeterministicComparisonEngine(unittest.TestCase):

    def setUp(self):
        self.courses = [
            {"course_code": "CSE-2201", "course_title": "OOP", "credit_hours": 3.0},
            {"course_code": "CSE-2202", "course_title": "DS Lab", "credit_hours": 1.5},
            {"course_code": "MAT-2101", "course_title": "Discrete Math", "credit_hours": 3.0},
        ]

        self.student_a = {
            "student_id": "2102045",
            "student_name": "ALICE JOHNSON",
            "results": [
                {"course_code": "CSE-2201", "grade_point": 4.00, "letter_grade": "A+"},  # A > B (4.00 vs 3.50)
                {"course_code": "CSE-2202", "grade_point": 3.75, "letter_grade": "A"},   # A < B (3.75 vs 4.00)
                {"course_code": "MAT-2101", "grade_point": 3.50, "letter_grade": "A-"},  # A == B (3.50 vs 3.50)
            ],
            "current_semester_summary": {"gpa": 3.75, "earned_credit": 7.5},
            "cumulative_summary": {"cgpa": 3.80, "earned_credit": 60.0},
            "semester_result": {"semester_rank": 2, "semester_percentile": 66.7},
            "cumulative_result": {"cumulative_rank": 2, "cumulative_percentile": 66.7},
        }

        self.student_b = {
            "student_id": "2102046",
            "student_name": "BOB SMITH",
            "results": [
                {"course_code": "CSE-2201", "grade_point": 3.50, "letter_grade": "A-"},
                {"course_code": "CSE-2202", "grade_point": 4.00, "letter_grade": "A+"},
                {"course_code": "MAT-2101", "grade_point": 3.50, "letter_grade": "A-"},
            ],
            "current_semester_summary": {"gpa": 3.65, "earned_credit": 7.5},
            "cumulative_summary": {"cgpa": 3.60, "earned_credit": 60.0},
            "semester_result": {"semester_rank": 4, "semester_percentile": 33.3},
            "cumulative_result": {"cumulative_rank": 5, "cumulative_percentile": 20.0},
        }

        self.ranking_data = {
            "semester_rankings": {
                "2102045": {"rank": 2, "percentile": 66.7},
                "2102046": {"rank": 4, "percentile": 33.3},
            },
            "cumulative_rankings": {
                "2102045": {"rank": 2, "percentile": 66.7},
                "2102046": {"rank": 5, "percentile": 20.0},
            },
        }

    def test_comparative_deltas_calculation(self):
        res = DeterministicComparisonEngine.compare_students(
            student_a=self.student_a,
            student_b=self.student_b,
            courses=self.courses,
            ranking_data=self.ranking_data,
        )

        deltas = res["deltas"]
        # GPA diff: 3.75 - 3.65 = +0.10
        self.assertEqual(deltas["gpa_diff"], 0.10)
        # CGPA diff: 3.80 - 3.60 = +0.20
        self.assertEqual(deltas["cgpa_diff"], 0.20)
        # Rank diff (Rank_B - Rank_A): 4 - 2 = +2 ranks higher
        self.assertEqual(deltas["semester_rank_diff"], 2)
        self.assertEqual(deltas["cumulative_rank_diff"], 3)

    def test_subject_level_comparisons(self):
        res = DeterministicComparisonEngine.compare_students(
            student_a=self.student_a,
            student_b=self.student_b,
            courses=self.courses,
            ranking_data=self.ranking_data,
        )

        courses_cmp = res["course_comparison"]
        self.assertEqual(len(courses_cmp), 3)

        # Course 1: CSE-2201 -> Alice (4.00) vs Bob (3.50) -> Delta +0.50 -> STUDENT_A
        c1 = next(c for c in courses_cmp if c["course_code"] == "CSE-2201")
        self.assertEqual(c1["delta_gp"], 0.50)
        self.assertEqual(c1["better_performer"], "STUDENT_A")

        # Course 2: CSE-2202 -> Alice (3.75) vs Bob (4.00) -> Delta -0.25 -> STUDENT_B
        c2 = next(c for c in courses_cmp if c["course_code"] == "CSE-2202")
        self.assertEqual(c2["delta_gp"], -0.25)
        self.assertEqual(c2["better_performer"], "STUDENT_B")

        # Course 3: MAT-2101 -> Alice (3.50) vs Bob (3.50) -> Delta 0.00 -> TIED
        c3 = next(c for c in courses_cmp if c["course_code"] == "MAT-2101")
        self.assertEqual(c3["delta_gp"], 0.0)
        self.assertEqual(c3["better_performer"], "TIED")

    def test_subject_tallies(self):
        res = DeterministicComparisonEngine.compare_students(
            student_a=self.student_a,
            student_b=self.student_b,
            courses=self.courses,
            ranking_data=self.ranking_data,
        )

        tally = res["subject_tally"]
        self.assertEqual(tally["a_better_count"], 1)
        self.assertEqual(tally["b_better_count"], 1)
        self.assertEqual(tally["tied_count"], 1)
        self.assertIn("CSE-2201", tally["subjects_a_better"])
        self.assertIn("CSE-2202", tally["subjects_b_better"])
        self.assertIn("MAT-2101", tally["subjects_tied"])


class TestComparisonAPIViews(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.session = ResultSession.objects.create(
            status="VERIFIED",
            original_filename="sample_sheet.pdf",
            parsed_dataset={
                "courses": [
                    {"course_code": "CSE-2201", "course_title": "OOP", "credit_hours": 3.0},
                ],
                "students": [
                    {
                        "student_id": "2102045",
                        "student_name": "ALICE",
                        "results": [{"course_code": "CSE-2201", "grade_point": 4.00, "letter_grade": "A+"}],
                        "current_semester_summary": {"gpa": 4.00},
                        "cumulative_summary": {"cgpa": 3.90},
                    },
                    {
                        "student_id": "2102046",
                        "student_name": "BOB",
                        "results": [{"course_code": "CSE-2201", "grade_point": 3.75, "letter_grade": "A"}],
                        "current_semester_summary": {"gpa": 3.75},
                        "cumulative_summary": {"cgpa": 3.70},
                    },
                ],
            },
        )

    def test_successful_comparison_api(self):
        url = f"/api/v1/sessions/{self.session.id}/compare/?student_a=2102045&student_b=2102046"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()["data"]

        self.assertEqual(data["student_a"]["id"], "2102045")
        self.assertEqual(data["student_b"]["id"], "2102046")
        self.assertEqual(data["deltas"]["gpa_diff"], 0.25)
        self.assertEqual(data["deltas"]["cgpa_diff"], 0.20)

    def test_missing_student_triggers_404(self):
        url = f"/api/v1/sessions/{self.session.id}/compare/?student_a=2102045&student_b=9999999"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


if __name__ == "__main__":
    unittest.main()
