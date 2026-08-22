"""
Unit and integration tests for detailed subject-wise analysis and topper tie-handling.
"""

import unittest
from apps.processing.analysis.engine import DeterministicAnalysisEngine


class TestSubjectAnalysisDetails(unittest.TestCase):

    def setUp(self):
        self.courses = [
            {"course_code": "CSE-2201", "course_title": "Object Oriented Programming", "credit_hours": 3.0},
            {"course_code": "CSE-2202", "course_title": "Data Structures Lab", "credit_hours": 1.5},
        ]

        # 4 Students
        # In CSE-2201: Alice(4.00, A+), Bob(4.00, A+), Charlie(3.50, A-), David(3.00, B)
        # Average = (4.00 + 4.00 + 3.50 + 3.00) / 4 = 3.625 -> 3.62
        self.students = [
            {
                "student_id": "2102045",
                "student_name": "ALICE JOHNSON",
                "results": [
                    {"course_code": "CSE-2201", "grade_point": 4.00, "letter_grade": "A+"},
                    {"course_code": "CSE-2202", "grade_point": 3.75, "letter_grade": "A"},
                ],
            },
            {
                "student_id": "2102046",
                "student_name": "BOB SMITH",
                "results": [
                    {"course_code": "CSE-2201", "grade_point": 4.00, "letter_grade": "A+"},
                    {"course_code": "CSE-2202", "grade_point": 4.00, "letter_grade": "A+"},
                ],
            },
            {
                "student_id": "2102047",
                "student_name": "CHARLIE BROWN",
                "results": [
                    {"course_code": "CSE-2201", "grade_point": 3.50, "letter_grade": "A-"},
                    {"course_code": "CSE-2202", "grade_point": 3.00, "letter_grade": "B"},
                ],
            },
            {
                "student_id": "2102048",
                "student_name": "DAVID MILLER",
                "results": [
                    {"course_code": "CSE-2201", "grade_point": 3.00, "letter_grade": "B"},
                    {"course_code": "CSE-2202", "grade_point": 3.50, "letter_grade": "A-"},
                ],
            },
        ]
        self.engine = DeterministicAnalysisEngine()

    def test_subject_statistical_metrics(self):
        analyses = self.engine.analyze_subjects(self.students, self.courses)
        self.assertEqual(len(analyses), 2)

        cse2201 = next(c for c in analyses if c["course_code"] == "CSE-2201")
        self.assertEqual(cse2201["number_of_students"], 4)
        self.assertEqual(cse2201["credit_hours"], 3.0)
        self.assertEqual(cse2201["average_gp"], 3.62)
        self.assertEqual(cse2201["median_gp"], 3.75)
        self.assertEqual(cse2201["highest_gp"], 4.00)
        self.assertEqual(cse2201["lowest_gp"], 3.00)

    def test_highest_performing_students_tie_handling(self):
        # Alice and Bob both have 4.00 in CSE-2201 -> Both must be returned as joint toppers
        analyses = self.engine.analyze_subjects(self.students, self.courses)
        cse2201 = next(c for c in analyses if c["course_code"] == "CSE-2201")

        toppers = cse2201["highest_performing_students"]
        self.assertEqual(len(toppers), 2)
        topper_ids = {t["student_id"] for t in toppers}
        self.assertIn("2102045", topper_ids)
        self.assertIn("2102046", topper_ids)
        for t in toppers:
            self.assertEqual(t["gp"], 4.00)
            self.assertEqual(t["letter_grade"], "A+")

    def test_selected_student_difference_and_percentile(self):
        # Select Charlie (2102047): GP = 3.50 in CSE-2201
        # Avg = 3.62 -> Diff = 3.50 - 3.62 = -0.12 GP
        # Rank: Alice(1), Bob(1), Charlie(3), David(4) -> Charlie is Rank 3
        # Percentile: ((4 - 3 + 1)/4)*100 = 50.0%
        analyses = self.engine.analyze_subjects(self.students, self.courses, selected_student_id="2102047")
        cse2201 = next(c for c in analyses if c["course_code"] == "CSE-2201")

        self.assertEqual(cse2201["selected_student_gp"], 3.50)
        self.assertEqual(cse2201["selected_student_letter_grade"], "A-")
        self.assertEqual(cse2201["selected_student_subject_rank"], 3)
        self.assertEqual(cse2201["selected_student_diff_from_average"], -0.12)
        self.assertEqual(cse2201["selected_student_percentile"], 50.0)

    def test_selected_student_tied_topper_metrics(self):
        # Select Alice (2102045): GP = 4.00 in CSE-2201
        # Avg = 3.62 -> Diff = 4.00 - 3.62 = +0.38 GP
        # Rank: 1
        # Percentile: ((4 - 1 + 1)/4)*100 = 100.0%
        analyses = self.engine.analyze_subjects(self.students, self.courses, selected_student_id="2102045")
        cse2201 = next(c for c in analyses if c["course_code"] == "CSE-2201")

        self.assertEqual(cse2201["selected_student_gp"], 4.00)
        self.assertEqual(cse2201["selected_student_letter_grade"], "A+")
        self.assertEqual(cse2201["selected_student_subject_rank"], 1)
        self.assertEqual(cse2201["selected_student_diff_from_average"], 0.38)
        self.assertEqual(cse2201["selected_student_percentile"], 100.0)


if __name__ == "__main__":
    unittest.main()
