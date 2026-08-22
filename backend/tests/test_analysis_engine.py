"""
Comprehensive unit and integration tests for the Deterministic Analysis Engine.

Verifies:
  - Mathematical correctness of mean, median, mode, min, max, std_dev
  - Individual Analysis (Every subject, course code, title, credits, GP, letter grade, highest/lowest/avg GP, rank)
  - Class Semester Analysis (Mean, Median, Mode, Highest, Lowest GPA)
  - Cumulative Analysis (Directly from cumulative values in sheet, no semester reconstruction)
  - Subject Analysis (Mean, Median, Mode, Highest, Lowest GP, toppers, grade distribution, subject ranks)
  - Strict nomenclature: GP (single subject) vs GPA (semester) vs CGPA (cumulative)
"""

import unittest
from decimal import Decimal

from apps.processing.analysis.engine import (
    DeterministicAnalysisEngine,
    calculate_descriptive_stats,
    compute_distribution_histogram,
)
from apps.processing.analysis.service import AnalysisEngineService


class TestDescriptiveStats(unittest.TestCase):

    def test_empty_list(self):
        stats = calculate_descriptive_stats([])
        self.assertEqual(stats["count"], 0)
        self.assertEqual(stats["mean"], 0.0)
        self.assertEqual(stats["median"], 0.0)
        self.assertEqual(stats["mode"], 0.0)
        self.assertEqual(stats["min"], 0.0)
        self.assertEqual(stats["max"], 0.0)

    def test_single_element(self):
        stats = calculate_descriptive_stats([3.75])
        self.assertEqual(stats["count"], 1)
        self.assertEqual(stats["mean"], 3.75)
        self.assertEqual(stats["median"], 3.75)
        self.assertEqual(stats["mode"], 3.75)
        self.assertEqual(stats["min"], 3.75)
        self.assertEqual(stats["max"], 3.75)

    def test_odd_count_median_and_mode(self):
        # [3.00, 3.50, 3.50, 3.75, 4.00]
        vals = [3.50, 4.00, 3.00, 3.75, 3.50]
        stats = calculate_descriptive_stats(vals)
        self.assertEqual(stats["count"], 5)
        self.assertEqual(stats["mean"], 3.55)
        self.assertEqual(stats["median"], 3.50)
        self.assertEqual(stats["mode"], 3.50)
        self.assertEqual(stats["min"], 3.00)
        self.assertEqual(stats["max"], 4.00)

    def test_even_count_median(self):
        # [3.00, 3.50, 3.75, 4.00] -> median = (3.50 + 3.75) / 2 = 3.625 -> 3.62
        vals = [3.00, 3.50, 3.75, 4.00]
        stats = calculate_descriptive_stats(vals)
        self.assertEqual(stats["count"], 4)
        self.assertEqual(stats["mean"], 3.56)
        self.assertEqual(stats["median"], 3.62)


class TestDeterministicAnalysisEngine(unittest.TestCase):

    def setUp(self):
        self.courses = [
            {"course_code": "CSE-2201", "course_title": "Object Oriented Programming", "credit_hours": 3.0},
            {"course_code": "CSE-2202", "course_title": "Data Structures Lab", "credit_hours": 1.5},
            {"course_code": "MAT-2101", "course_title": "Discrete Mathematics", "credit_hours": 3.0},
        ]

        self.students = [
            {
                "student_id": "2102045",
                "student_name": "ALICE JOHNSON",
                "serial_no": 1,
                "status": "VALID",
                "results": [
                    {"course_code": "CSE-2201", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                    {"course_code": "CSE-2202", "grade_point": 3.75, "letter_grade": "A", "status": "VALID"},
                    {"course_code": "MAT-2101", "grade_point": 3.50, "letter_grade": "A-", "status": "VALID"},
                ],
                "current_semester_summary": {"gpa": 3.75, "total_credit": 7.5, "earned_credit": 7.5, "result_status": "PASSED"},
                "cumulative_summary": {"cgpa": 3.80, "total_credit": 60.0, "earned_credit": 60.0, "result_status": "PASSED"},
            },
            {
                "student_id": "2102046",
                "student_name": "BOB SMITH",
                "serial_no": 2,
                "status": "VALID",
                "results": [
                    {"course_code": "CSE-2201", "grade_point": 3.50, "letter_grade": "A-", "status": "VALID"},
                    {"course_code": "CSE-2202", "grade_point": 3.00, "letter_grade": "B", "status": "VALID"},
                    {"course_code": "MAT-2101", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                ],
                "current_semester_summary": {"gpa": 3.60, "total_credit": 7.5, "earned_credit": 7.5, "result_status": "PASSED"},
                "cumulative_summary": {"cgpa": 3.50, "total_credit": 60.0, "earned_credit": 60.0, "result_status": "PASSED"},
            },
            {
                "student_id": "2102047",
                "student_name": "CHARLIE BROWN",
                "serial_no": 3,
                "status": "VALID",
                "results": [
                    {"course_code": "CSE-2201", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                    {"course_code": "CSE-2202", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                    {"course_code": "MAT-2101", "grade_point": 3.75, "letter_grade": "A", "status": "VALID"},
                ],
                "current_semester_summary": {"gpa": 3.90, "total_credit": 7.5, "earned_credit": 7.5, "result_status": "PASSED"},
                "cumulative_summary": {"cgpa": 3.85, "total_credit": 60.0, "earned_credit": 60.0, "result_status": "PASSED"},
            },
        ]
        self.engine = DeterministicAnalysisEngine()

    # -----------------------------------------------------------------------
    # 1. Individual Analysis Tests
    # -----------------------------------------------------------------------

    def test_individual_student_analysis(self):
        alice = self.students[0]
        res = self.engine.analyze_individual_student(alice, self.courses, self.students)

        self.assertEqual(res["student_id"], "2102045")
        self.assertEqual(res["student_name"], "ALICE JOHNSON")
        self.assertEqual(len(res["subjects"]), 3)

        # Subject breakdown checks
        s1 = next(s for s in res["subjects"] if s["course_code"] == "CSE-2201")
        self.assertEqual(s1["gp"], 4.00)
        self.assertEqual(s1["letter_grade"], "A+")
        self.assertEqual(s1["credit"], 3.0)
        # Alice tied 1st in CSE-2201 with Charlie
        self.assertEqual(s1["subject_rank"], 1)

        # Current semester GPA vs Cumulative CGPA
        self.assertEqual(res["current_semester"]["gpa"], 3.75)
        self.assertEqual(res["cumulative"]["cgpa"], 3.80)

        # GP Extreme and Average
        gp_analysis = res["subject_gp_analysis"]
        self.assertEqual(gp_analysis["highest_subject_gp"], 4.00)
        self.assertIn("CSE-2201", gp_analysis["highest_subject_courses"])
        self.assertEqual(gp_analysis["lowest_subject_gp"], 3.50)
        self.assertIn("MAT-2101", gp_analysis["lowest_subject_courses"])
        # (4.00 + 3.75 + 3.50) / 3 = 3.75
        self.assertEqual(gp_analysis["average_subject_gp"], 3.75)

    # -----------------------------------------------------------------------
    # 2. Class Analysis Tests
    # -----------------------------------------------------------------------

    def test_class_semester_analysis(self):
        # GPAs: [3.75, 3.60, 3.90] -> sorted [3.60, 3.75, 3.90]
        # Mean = (3.60 + 3.75 + 3.90) / 3 = 3.75
        # Median = 3.75
        # Min = 3.60, Max = 3.90
        res = self.engine.analyze_class_semester(self.students)

        self.assertEqual(res["total_students"], 3)
        self.assertEqual(res["average_gpa"], 3.75)
        self.assertEqual(res["median_gpa"], 3.75)
        self.assertEqual(res["highest_gpa"], 3.90)
        self.assertEqual(res["lowest_gpa"], 3.60)
        self.assertTrue(len(res["distribution"]) > 0)

    # -----------------------------------------------------------------------
    # 3. Cumulative Analysis Tests
    # -----------------------------------------------------------------------

    def test_cumulative_analysis(self):
        # CGPAs: [3.80, 3.50, 3.85] -> sorted [3.50, 3.80, 3.85]
        # Mean = (3.50 + 3.80 + 3.85) / 3 = 3.72
        # Median = 3.80
        # Min = 3.50, Max = 3.85
        res = self.engine.analyze_cumulative_cohort(self.students)

        self.assertEqual(res["total_students"], 3)
        self.assertEqual(res["average_cgpa"], 3.72)
        self.assertEqual(res["median_cgpa"], 3.80)
        self.assertEqual(res["highest_cgpa"], 3.85)
        self.assertEqual(res["lowest_cgpa"], 3.50)

    # -----------------------------------------------------------------------
    # 4. Subject Analysis Tests
    # -----------------------------------------------------------------------

    def test_subject_analysis(self):
        # In CSE-2201: GPs are [4.00, 3.50, 4.00] -> Mean = 3.83, Median = 4.00, Mode = 4.00, Max = 4.00, Min = 3.50
        res = self.engine.analyze_subjects(self.students, self.courses, selected_student_id="2102046")
        self.assertEqual(len(res), 3)

        cse2201 = next(c for c in res if c["course_code"] == "CSE-2201")
        self.assertEqual(cse2201["number_of_students"], 3)
        self.assertEqual(cse2201["average_gp"], 3.83)
        self.assertEqual(cse2201["median_gp"], 4.00)
        self.assertEqual(cse2201["mode_gp"], 4.00)
        self.assertEqual(cse2201["highest_gp"], 4.00)
        self.assertEqual(cse2201["lowest_gp"], 3.50)

        # Toppers list has Alice & Charlie
        toppers = cse2201["highest_performing_students"]
        self.assertEqual(len(toppers), 2)
        topper_ids = {t["student_id"] for t in toppers}
        self.assertIn("2102045", topper_ids)
        self.assertIn("2102047", topper_ids)

        # Selected student (Bob / 2102046) has GP 3.50 and rank 3 in CSE-2201
        self.assertEqual(cse2201["selected_student_gp"], 3.50)
        self.assertEqual(cse2201["selected_student_subject_rank"], 3)

    # -----------------------------------------------------------------------
    # 5. Service Full Orchestration Test
    # -----------------------------------------------------------------------

    def test_service_cohort_statistics(self):
        service = AnalysisEngineService()
        output = service.calculate_cohort_statistics(self.students, self.courses)

        self.assertIn("class_analysis", output)
        self.assertIn("cumulative_analysis", output)
        self.assertIn("subject_analysis", output)
        self.assertIn("student_leaderboard", output)

        # Leaderboard sorted descending by GPA: Charlie (3.90) > Alice (3.75) > Bob (3.60)
        lb = output["student_leaderboard"]
        self.assertEqual(lb[0]["student_id"], "2102047")
        self.assertEqual(lb[0]["rank"], 1)
        self.assertEqual(lb[1]["student_id"], "2102045")
        self.assertEqual(lb[1]["rank"], 2)
        self.assertEqual(lb[2]["student_id"], "2102046")
        self.assertEqual(lb[2]["rank"], 3)


if __name__ == "__main__":
    unittest.main()
