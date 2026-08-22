"""
Unit and integration tests for the Deterministic Ranking Engine.

Tests:
  - Standard Competition Ranking ("1224" rule)
  - Semester GPA ranking, Cumulative CGPA ranking, Subject GP ranking
  - Handling of ties (e.g. 3.90 -> 1, 3.90 -> 1, 3.85 -> 3)
  - Missing and None values (unranked)
  - Exclusion of invalid data (never rank using invalid data)
  - Deduplication of duplicate student IDs
  - Percentile and relative position computation
"""

import unittest
from apps.processing.ranking.engine import (
    DeterministicRankingEngine,
    compute_standard_competition_ranks,
    deduplicate_students,
)
from apps.processing.ranking.service import RankingEngineService


class TestStandardCompetitionRanking(unittest.TestCase):

    def test_example_tie_ranking_rule(self):
        # User specification example: 3.90 -> 1, 3.90 -> 1, 3.85 -> 3, 3.80 -> 4
        items = [
            ("s1", 3.90, True),
            ("s2", 3.90, True),
            ("s3", 3.85, True),
            ("s4", 3.80, True),
        ]
        ranks = compute_standard_competition_ranks(items)

        self.assertEqual(ranks["s1"]["rank"], 1)
        self.assertTrue(ranks["s1"]["is_tied"])
        self.assertEqual(ranks["s2"]["rank"], 1)
        self.assertTrue(ranks["s2"]["is_tied"])
        self.assertEqual(ranks["s3"]["rank"], 3)
        self.assertFalse(ranks["s3"]["is_tied"])
        self.assertEqual(ranks["s4"]["rank"], 4)
        self.assertEqual(ranks["s1"]["total_ranked"], 4)

    def test_three_way_tie(self):
        # 3 students tie for Rank 1 -> Ranks 1, 1, 1, next is 4
        items = [
            ("s1", 4.00, True),
            ("s2", 4.00, True),
            ("s3", 4.00, True),
            ("s4", 3.75, True),
        ]
        ranks = compute_standard_competition_ranks(items)

        self.assertEqual(ranks["s1"]["rank"], 1)
        self.assertEqual(ranks["s2"]["rank"], 1)
        self.assertEqual(ranks["s3"]["rank"], 1)
        self.assertEqual(ranks["s4"]["rank"], 4)

    def test_missing_and_invalid_values_are_unranked(self):
        items = [
            ("s1", 3.90, True),
            ("s2", None, True),       # Missing score
            ("s3", 3.80, False),      # Invalid flag (e.g. fatal extraction error)
            ("s4", 3.70, True),
        ]
        ranks = compute_standard_competition_ranks(items)

        # Only s1 and s4 are valid
        self.assertEqual(ranks["s1"]["rank"], 1)
        self.assertEqual(ranks["s1"]["total_ranked"], 2)
        self.assertEqual(ranks["s4"]["rank"], 2)
        self.assertEqual(ranks["s4"]["total_ranked"], 2)

        # s2 and s3 must be unranked
        self.assertIsNone(ranks["s2"]["rank"])
        self.assertFalse(ranks["s2"]["is_ranked"])
        self.assertIsNone(ranks["s3"]["rank"])
        self.assertFalse(ranks["s3"]["is_ranked"])

    def test_percentile_calculation(self):
        items = [
            ("s1", 4.00, True),
            ("s2", 3.50, True),
        ]
        ranks = compute_standard_competition_ranks(items)
        # s1: rank 1 of 2 -> ((2 - 1 + 1)/2)*100 = 100.0%
        # s2: rank 2 of 2 -> ((2 - 2 + 1)/2)*100 = 50.0%
        self.assertEqual(ranks["s1"]["percentile"], 100.0)
        self.assertEqual(ranks["s2"]["percentile"], 50.0)


class TestDeterministicRankingEngine(unittest.TestCase):

    def setUp(self):
        self.courses = [
            {"course_code": "CSE-2201", "course_title": "OOP", "credit_hours": 3.0},
            {"course_code": "CSE-2202", "course_title": "DS Lab", "credit_hours": 1.5},
        ]
        self.students = [
            {
                "student_id": "2102045",
                "student_name": "ALICE",
                "status": "VALID",
                "confidence": 0.99,
                "results": [
                    {"course_code": "CSE-2201", "grade_point": 4.00, "status": "VALID"},
                    {"course_code": "CSE-2202", "grade_point": 3.75, "status": "VALID"},
                ],
                "current_semester_summary": {"gpa": 3.90, "status": "VALID"},
                "cumulative_summary": {"cgpa": 3.85, "status": "VALID"},
            },
            {
                "student_id": "2102046",
                "student_name": "BOB",
                "status": "VALID",
                "confidence": 0.95,
                "results": [
                    {"course_code": "CSE-2201", "grade_point": 4.00, "status": "VALID"},
                    {"course_code": "CSE-2202", "grade_point": 3.00, "status": "VALID"},
                ],
                "current_semester_summary": {"gpa": 3.90, "status": "VALID"},  # Tied with Alice
                "cumulative_summary": {"cgpa": 3.70, "status": "VALID"},
            },
            {
                "student_id": "2102047",
                "student_name": "CHARLIE",
                "status": "VALID",
                "confidence": 0.92,
                "results": [
                    {"course_code": "CSE-2201", "grade_point": 3.50, "status": "VALID"},
                    {"course_code": "CSE-2202", "grade_point": 4.00, "status": "VALID"},
                ],
                "current_semester_summary": {"gpa": 3.65, "status": "VALID"},
                "cumulative_summary": {"cgpa": 3.95, "status": "VALID"},
            },
        ]

    def test_semester_ranking_with_tie(self):
        ranks = DeterministicRankingEngine.rank_current_semester(self.students)
        # Alice & Bob tie at 3.90 -> Rank 1
        self.assertEqual(ranks["2102045"]["rank"], 1)
        self.assertEqual(ranks["2102046"]["rank"], 1)
        # Charlie is 3.65 -> Rank 3 (due to 1224 rule)
        self.assertEqual(ranks["2102047"]["rank"], 3)

    def test_cumulative_ranking_from_sheet(self):
        ranks = DeterministicRankingEngine.rank_cumulative(self.students)
        # Charlie (3.95) -> 1, Alice (3.85) -> 2, Bob (3.70) -> 3
        self.assertEqual(ranks["2102047"]["rank"], 1)
        self.assertEqual(ranks["2102045"]["rank"], 2)
        self.assertEqual(ranks["2102046"]["rank"], 3)

    def test_subject_specific_ranking(self):
        ranks = DeterministicRankingEngine.rank_subjects(self.students, self.courses)

        # In CSE-2201: Alice & Bob have 4.00 (Rank 1), Charlie has 3.50 (Rank 3)
        cse2201_ranks = ranks["CSE-2201"]
        self.assertEqual(cse2201_ranks["2102045"]["rank"], 1)
        self.assertEqual(cse2201_ranks["2102046"]["rank"], 1)
        self.assertEqual(cse2201_ranks["2102047"]["rank"], 3)

        # In CSE-2202: Charlie has 4.00 (Rank 1), Alice has 3.75 (Rank 2), Bob has 3.00 (Rank 3)
        cse2202_ranks = ranks["CSE-2202"]
        self.assertEqual(cse2202_ranks["2102047"]["rank"], 1)
        self.assertEqual(cse2202_ranks["2102045"]["rank"], 2)
        self.assertEqual(cse2202_ranks["2102046"]["rank"], 3)

    def test_deduplication_keeps_highest_confidence_valid_entry(self):
        dupes = [
            {"student_id": "2102045", "student_name": "ALICE OLD", "confidence": 0.80, "status": "WARNING"},
            {"student_id": "2102045", "student_name": "ALICE NEW", "confidence": 0.98, "status": "VALID"},
        ]
        clean = deduplicate_students(dupes)
        self.assertEqual(len(clean), 1)
        self.assertEqual(clean[0]["student_name"], "ALICE NEW")

    def test_invalid_student_is_excluded_from_ranking(self):
        students_with_invalid = list(self.students)
        students_with_invalid.append({
            "student_id": "2102099",
            "student_name": "CORRUPT RECORD",
            "status": "INVALID",
            "current_semester_summary": {"gpa": 5.50, "status": "INVALID"},
        })

        ranks = DeterministicRankingEngine.rank_current_semester(students_with_invalid)
        # Corrupt record must be unranked
        self.assertIsNone(ranks["2102099"]["rank"])
        self.assertFalse(ranks["2102099"]["is_ranked"])
        # Total ranked valid population remains 3
        self.assertEqual(ranks["2102045"]["total_ranked"], 3)

    def test_service_rank_all_orchestration(self):
        service = RankingEngineService()
        augmented = service.calculate_ranks(self.students, self.courses)

        self.assertEqual(len(augmented), 3)
        alice = next(s for s in augmented if s["student_id"] == "2102045")
        self.assertEqual(alice["semester_result"]["semester_rank"], 1)
        self.assertEqual(alice["cumulative_result"]["cumulative_rank"], 2)

        # Check Alice's subject topper status in CSE-2201
        res_cse2201 = next(r for r in alice["results"] if r["course_code"] == "CSE-2201")
        self.assertEqual(res_cse2201["subject_rank"], 1)
        self.assertTrue(res_cse2201["is_topper"])


if __name__ == "__main__":
    unittest.main()
