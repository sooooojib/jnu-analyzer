"""
Unit and Integration tests for the Export Data Layer.

Verifies:
  1. build_student_report_data: Valid student, missing optional fields, invalid student, boundary isolation.
  2. build_class_report_data: Valid dataset, empty dataset, rankings, subject analysis, boundary isolation.
  3. build_comparison_report_data: Valid 2 students, deltas, tallies, invalid student, boundary isolation.
  4. Strict zero-cross-contamination between Student, Class, and Comparison data payloads.
"""

import unittest
import uuid
from apps.core.exceptions import StudentNotFoundError
from apps.export.data_builders import (
    build_student_report_data,
    build_class_report_data,
    build_comparison_report_data,
)
from apps.sessions_manager.models import ResultSession


class TestExportDataLayer(unittest.TestCase):

    def setUp(self):
        self.session_id = uuid.uuid4()
        self.courses = [
            {"course_code": "CSE-1101", "course_title": "Intro to CS", "credit_hours": 3.0},
            {"course_code": "CSE-1102", "course_title": "Structured Programming", "credit_hours": 3.0},
            {"course_code": "CSE-1103", "course_title": "Programming Lab", "credit_hours": 1.5},
        ]
        self.students = [
            {
                "student_id": "2102001",
                "student_name": "ALICE WALKER",
                "serial_no": 1,
                "status": "VALID",
                "results": [
                    {"course_code": "CSE-1101", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                    {"course_code": "CSE-1102", "grade_point": 3.75, "letter_grade": "A", "status": "VALID"},
                    {"course_code": "CSE-1103", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                ],
                "current_semester_summary": {
                    "gpa": 3.90,
                    "total_credit": 7.5,
                    "earned_credit": 7.5,
                    "grade_points": 29.25,
                    "result_status": "PASSED",
                    "remarks": "Excellent",
                },
                "cumulative_summary": {
                    "cgpa": 3.90,
                    "total_credit": 7.5,
                    "earned_credit": 7.5,
                    "grade_points": 29.25,
                    "result_status": "PASSED",
                },
            },
            {
                "student_id": "2102002",
                "student_name": "BOB MARLEY",
                "serial_no": 2,
                "status": "VALID",
                "results": [
                    {"course_code": "CSE-1101", "grade_point": 3.50, "letter_grade": "A-", "status": "VALID"},
                    {"course_code": "CSE-1102", "grade_point": 3.50, "letter_grade": "A-", "status": "VALID"},
                    {"course_code": "CSE-1103", "grade_point": 3.75, "letter_grade": "A", "status": "VALID"},
                ],
                "current_semester_summary": {
                    "gpa": 3.55,
                    "total_credit": 7.5,
                    "earned_credit": 7.5,
                    "grade_points": 26.62,
                    "result_status": "PASSED",
                },
                "cumulative_summary": {
                    "cgpa": 3.55,
                    "total_credit": 7.5,
                    "earned_credit": 7.5,
                    "result_status": "PASSED",
                },
            },
            {
                "student_id": "2102003",
                "student_name": "CHARLIE BROWN",
                "serial_no": 3,
                "status": "VALID",
                "results": [
                    {"course_code": "CSE-1101", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                    {"course_code": "CSE-1102", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                    {"course_code": "CSE-1103", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                ],
                "current_semester_summary": {
                    "gpa": 4.00,
                    "total_credit": 7.5,
                    "earned_credit": 7.5,
                    "grade_points": 30.00,
                    "result_status": "PASSED",
                },
                "cumulative_summary": {
                    "cgpa": 4.00,
                    "total_credit": 7.5,
                    "earned_credit": 7.5,
                    "result_status": "PASSED",
                },
            },
        ]

        self.session = ResultSession(
            id=self.session_id,
            original_filename="BSc_CSE_1st_Sem.md",
            file_type="md",
            status="VERIFIED",
            parsed_dataset={
                "institution": "Jagannath University",
                "program": "Department of Computer Science & Engineering",
                "semester": "BSc 1st Year 1st Semester Examination 2023",
                "exam_session": "2022-23",
                "courses": self.courses,
                "students": self.students,
            },
        )

    # -------------------------------------------------------------------------
    # 1. Student Report Data Builder Tests
    # -------------------------------------------------------------------------

    def test_student_report_data_valid(self):
        data = build_student_report_data(self.session, "2102001")
        self.assertEqual(data["report_type"], "STUDENT_ANALYSIS")
        
        # Student Info
        self.assertEqual(data["student_info"]["student_id"], "2102001")
        self.assertEqual(data["student_info"]["student_name"], "ALICE WALKER")
        
        # Academic Summary
        self.assertEqual(data["academic_summary"]["semester_gpa"], 3.90)
        self.assertEqual(data["academic_summary"]["cumulative_cgpa"], 3.90)
        self.assertEqual(data["academic_summary"]["semester_rank"], 2)  # Charlie is rank 1 (4.00)
        self.assertEqual(data["academic_summary"]["total_subjects"], 3)
        
        # Subject Results
        self.assertEqual(len(data["subject_results"]), 3)
        cse1101 = next(c for c in data["subject_results"] if c["course_code"] == "CSE-1101")
        self.assertEqual(cse1101["grade_point"], 4.00)
        self.assertEqual(cse1101["letter_grade"], "A+")
        self.assertEqual(cse1101["subject_rank"], 1)  # Tied rank 1 with Charlie
        self.assertIsNotNone(cse1101["class_average_gp"])

        # Performance Statistics
        self.assertEqual(data["performance_statistics"]["highest_subject_gp"], 4.00)
        self.assertEqual(data["performance_statistics"]["lowest_subject_gp"], 3.75)
        self.assertIn("CSE-1101", data["performance_statistics"]["highest_subject_courses"])

        # Boundary Isolation: Ensure NO class leaderboard or comparison tallies exist
        self.assertNotIn("student_rankings", data)
        self.assertNotIn("student_leaderboard", data)
        self.assertNotIn("deltas", data)
        self.assertNotIn("course_comparison", data)

    def test_student_report_data_invalid_student_raises_404(self):
        with self.assertRaises(StudentNotFoundError):
            build_student_report_data(self.session, "NON_EXISTENT_ID")

    def test_student_report_data_whitespace_normalization(self):
        # Should cleanly match ' 2102001 ' or '210 2001'
        data = build_student_report_data(self.session, " 2102001 ")
        self.assertEqual(data["student_info"]["student_id"], "2102001")

    def test_student_report_data_missing_cumulative(self):
        # Student with missing cumulative summary
        session_no_cum = ResultSession(
            id=uuid.uuid4(),
            original_filename="sheet.md",
            parsed_dataset={
                "courses": self.courses,
                "students": [
                    {
                        "student_id": "9999",
                        "student_name": "TEST",
                        "results": [{"course_code": "CSE-1101", "grade_point": 3.75, "letter_grade": "A"}],
                        "current_semester_summary": {"gpa": 3.75, "total_credit": 3.0},
                    }
                ],
            },
        )
        data = build_student_report_data(session_no_cum, "9999")
        self.assertEqual(data["academic_summary"]["semester_gpa"], 3.75)
        self.assertEqual(data["academic_summary"]["cumulative_cgpa"], 0.0)

    # -------------------------------------------------------------------------
    # 2. Class Report Data Builder Tests
    # -------------------------------------------------------------------------

    def test_class_report_data_valid(self):
        data = build_class_report_data(self.session)
        self.assertEqual(data["report_type"], "CLASS_ANALYSIS")

        # Class Overview
        self.assertEqual(data["class_overview"]["total_students"], 3)
        self.assertEqual(data["class_overview"]["total_subjects"], 3)
        self.assertEqual(data["class_overview"]["highest_gpa"], 4.00)
        self.assertEqual(data["class_overview"]["lowest_gpa"], 3.55)
        self.assertIsNotNone(data["class_overview"]["average_gpa"])
        self.assertIsInstance(data["class_overview"]["gpa_distribution"], list)

        # Cumulative Overview
        self.assertEqual(data["cumulative_overview"]["total_students"], 3)
        self.assertEqual(data["cumulative_overview"]["highest_cgpa"], 4.00)

        # Student Rankings Leaderboard
        self.assertEqual(len(data["student_rankings"]), 3)
        self.assertEqual(data["student_rankings"][0]["student_id"], "2102003")  # Charlie is rank 1
        self.assertEqual(data["student_rankings"][0]["rank"], 1)

        # Subject Analysis
        self.assertEqual(len(data["subject_analysis"]), 3)
        cse1101 = next(s for s in data["subject_analysis"] if s["course_code"] == "CSE-1101")
        self.assertEqual(cse1101["highest_gp"], 4.00)
        self.assertEqual(cse1101["number_of_students"], 3)
        # Toppers
        self.assertEqual(len(cse1101["toppers"]), 2)  # Alice and Charlie both have 4.00

        # Boundary Isolation: Ensure NO individual detailed scorecard or comparison data
        self.assertNotIn("course_grades", data)
        self.assertNotIn("student_a", data)
        self.assertNotIn("deltas", data)

    def test_class_report_data_empty_dataset(self):
        empty_session = ResultSession(
            id=uuid.uuid4(),
            original_filename="empty.md",
            parsed_dataset={"courses": [], "students": []},
        )
        data = build_class_report_data(empty_session)
        self.assertEqual(data["class_overview"]["total_students"], 0)
        self.assertEqual(data["student_rankings"], [])
        self.assertEqual(data["subject_analysis"], [])

    # -------------------------------------------------------------------------
    # 3. Comparison Report Data Builder Tests
    # -------------------------------------------------------------------------

    def test_comparison_report_data_valid(self):
        data = build_comparison_report_data(self.session, "2102001", "2102002")
        self.assertEqual(data["report_type"], "STUDENT_COMPARISON")

        # Student A & B profiles
        self.assertEqual(data["student_a"]["student_id"], "2102001")
        self.assertEqual(data["student_a"]["semester_gpa"], 3.90)
        self.assertEqual(data["student_b"]["student_id"], "2102002")
        self.assertEqual(data["student_b"]["semester_gpa"], 3.55)

        # Deltas
        self.assertEqual(data["deltas"]["gpa_difference"], 0.35)  # 3.90 - 3.55 = +0.35

        # Subject Tallies
        self.assertEqual(data["subject_tally"]["total_courses_compared"], 3)
        self.assertGreaterEqual(data["subject_tally"]["student_a_wins"], 1)

        # Course comparison matrix
        self.assertEqual(len(data["course_comparison"]), 3)
        cse1101 = next(c for c in data["course_comparison"] if c["course_code"] == "CSE-1101")
        self.assertEqual(cse1101["student_a_gp"], 4.00)
        self.assertEqual(cse1101["student_b_gp"], 3.50)
        self.assertEqual(cse1101["delta_gp"], 0.50)
        self.assertEqual(cse1101["better_performer"], "STUDENT_A")

        # Boundary Isolation: Ensure NO full class leaderboard or unrelated students
        self.assertNotIn("student_rankings", data)
        self.assertNotIn("student_leaderboard", data)
        self.assertNotIn("2102003", str(data["student_a"]))
        self.assertNotIn("2102003", str(data["student_b"]))

    def test_comparison_report_data_invalid_student_raises_404(self):
        with self.assertRaises(StudentNotFoundError):
            build_comparison_report_data(self.session, "2102001", "INVALID_STUDENT")

        with self.assertRaises(StudentNotFoundError):
            build_comparison_report_data(self.session, "INVALID_STUDENT", "2102002")
