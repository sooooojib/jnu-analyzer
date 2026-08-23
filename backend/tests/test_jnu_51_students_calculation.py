"""
Test suite validating calculation and analysis accuracy for the 51-student
Jagannath University BSc 1st Year 1st Semester CSE Examination dataset.
"""

from decimal import Decimal
from django.test import TestCase
from apps.processing.parser.markdown_parser import MarkdownSheetParser
from apps.processing.validation.validation_engine import SheetValidationEngine
from apps.processing.analysis.engine import DeterministicAnalysisEngine
from apps.processing.ranking.engine import DeterministicRankingEngine
from apps.processing.comparison.engine import DeterministicComparisonEngine
from apps.sessions_manager.models import ResultSession
from apps.export.data_builders.student_builder import build_student_report_data
from apps.export.data_builders.class_builder import build_class_report_data
from apps.export.data_builders.comparison_builder import build_comparison_report_data
from apps.export.services.student_pdf_exporter import build_student_pdf
from apps.export.services.class_pdf_exporter import build_class_pdf
from apps.export.services.comparison_pdf_exporter import build_comparison_pdf
from apps.export.services.student_excel_exporter import build_student_excel

JNU_DATASET = """# Academic Result Sheet
- **Institution**: Jagannath University
- **Department**: Department of Computer Science & Engineering
- **Semester**: BSc 1st Year 1st Semester Examination 2023
- **Session / Batch**: Session: 2022-23
- **Total Semester Credit**: 20.50

### Course List:
- [CSE-1101]: Introduction to Computer Science and IT (Credit: 3.00)
- [CSE-1102]: Structured Programming Language (Credit: 3.00)
- [CSEL-1103]: Structured Programming Language Lab (Credit: 1.50)
- [CSER-1104]: Math-I (Calculus) (Credit: 3.00)
- [CSER-1105]: Physics (Credit: 3.00)
- [CSE-1106]: Electrical Circuit Analysis (Credit: 3.00)
- [CSEL-1107]: Electrical Circuit Analysis Lab (Credit: 1.00)
- [CSER-1108]: English (Credit: 3.00)

| S/N | Student ID | Student Name | CSE-1101 GP | CSE-1101 LG | CSE-1102 GP | CSE-1102 LG | CSEL-1103 GP | CSEL-1103 LG | CSER-1104 GP | CSER-1104 LG | CSER-1105 GP | CSER-1105 LG | CSE-1106 GP | CSE-1106 LG | CSEL-1107 GP | CSEL-1107 LG | CSER-1108 GP | CSER-1108 LG | Total GP | GPA | Cumulative Credits | CGPA | Result Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | B210305018 | FEERDAUS HASAN PRINCE | 2.50 | C+ | 0.00 | F | 0.00 | F | 0.00 | F | 2.25 | C | 2.50 | C+ | 2.25 | C | 3.00 | B | 33.00 | 1.61 | 20.50 | 1.61 | CP |
| 2 | B210305042 | SHAMIMA AKTHER BORNA | 4.00 | A+ | 0.00 | F | 4.00 | A+ | 4.00 | A+ | 4.00 | A+ | 0.00 | F | 4.00 | A+ | 3.75 | A | 57.25 | 2.79 | 20.50 | 2.79 | CP |
| 3 | B210305048 | MARUF KHAN | 3.75 | A | 0.00 | F | 2.25 | C | 3.25 | B+ | 4.00 | A+ | 3.75 | A | 4.00 | A+ | 3.75 | A | 62.88 | 3.07 | 20.50 | 3.07 | CP |
| 4 | B210305049 | FARHANA YESMIN RIYA | 3.25 | B+ | 2.75 | B- | 3.50 | A- | 2.25 | C | 2.25 | C | 3.50 | A- | 4.00 | A+ | 3.75 | A | 62.50 | 3.05 | 20.50 | 3.05 | P |
| 5 | B220305002 | SANJIDA PARVIN | 4.00 | A+ | 2.50 | C+ | 3.00 | B | 3.25 | B+ | 3.00 | B | 3.50 | A- | 4.00 | A+ | 3.75 | A | 68.50 | 3.34 | 20.50 | 3.34 | P |
| 6 | B220305004 | IFRAT JAHAN JUTHY | 3.75 | A | 3.25 | B+ | 3.50 | A- | 3.50 | A- | 3.75 | A | 4.00 | A+ | 4.00 | A+ | 2.75 | B- | 72.25 | 3.52 | 20.50 | 3.52 | P |
| 7 | B220305005 | JANNATUN NAHAR JUI | 4.00 | A+ | 3.75 | A | 3.50 | A- | 4.00 | A+ | 4.00 | A+ | 3.50 | A- | 4.00 | A+ | 3.50 | A- | 77.50 | 3.78 | 20.50 | 3.78 | P |
| 8 | B220305006 | MD. RAMJAN MIAH | 4.00 | A+ | 3.50 | A- | 3.75 | A | 2.25 | C | 2.50 | C+ | 3.00 | B | 4.00 | A+ | 3.75 | A | 66.63 | 3.25 | 20.50 | 3.25 | P |
| 9 | B220305007 | FARIHA YASMEEN | 3.75 | A | 2.50 | C+ | 2.75 | B- | 3.50 | A- | 3.75 | A | 3.50 | A- | 3.50 | A- | 3.50 | A- | 69.13 | 3.37 | 20.50 | 3.37 | P |
| 10 | B220305008 | NAZMUL HASAN | 4.00 | A+ | 3.25 | B+ | 3.75 | A | 4.00 | A+ | 4.00 | A+ | 4.00 | A+ | 4.00 | A+ | 3.75 | A | 78.63 | 3.84 | 20.50 | 3.84 | P |
| 11 | B220305009 | S.M SAJIB AL HASAN | 3.25 | B+ | 3.25 | B+ | 3.75 | A | 3.75 | A | 3.50 | A- | 3.50 | A- | 4.00 | A+ | 3.25 | B+ | 71.13 | 3.47 | 20.50 | 3.47 | P |
| 12 | B220305010 | NAIMA MARJAN JERIN | 4.00 | A+ | 2.75 | B- | 3.25 | B+ | 3.75 | A | 4.00 | A+ | 3.50 | A- | 3.75 | A | 3.25 | B+ | 72.38 | 3.53 | 20.50 | 3.53 | P |
| 13 | B220305011 | MAUFIYA KHATUN | 3.25 | B+ | 3.25 | B+ | 3.00 | B | 4.00 | A+ | 3.75 | A | 3.75 | A | 4.00 | A+ | 3.25 | B+ | 72.25 | 3.52 | 20.50 | 3.52 | P |
| 14 | B220305012 | MD. ANISUR RAHMAN ZIHAD | 3.25 | B+ | 0.00 | F | 3.25 | B+ | 0.00 | F | 2.25 | C | 3.00 | B | 4.00 | A+ | 3.50 | A- | 44.88 | 2.19 | 20.50 | 2.19 | CP |
| 15 | B220305013 | BORNITA DEY | 4.00 | A+ | 3.25 | B+ | 3.75 | A | 4.00 | A+ | 3.75 | A | 4.00 | A+ | 4.00 | A+ | 3.50 | A- | 77.13 | 3.76 | 20.50 | 3.76 | P |
| 16 | B220305014 | NAFISA RAHMAN | 4.00 | A+ | 3.25 | B+ | 3.00 | B | 3.50 | A- | 3.50 | A- | 4.00 | A+ | 4.00 | A+ | 3.50 | A- | 73.75 | 3.60 | 20.50 | 3.60 | P |
| 17 | B220305016 | TAHMINA AKTER | 4.00 | A+ | 3.50 | A- | 3.50 | A- | 4.00 | A+ | 4.00 | A+ | 4.00 | A+ | 4.00 | A+ | 3.75 | A | 79.00 | 3.85 | 20.50 | 3.85 | P |
| 18 | B220305017 | TASFIA TASNIM | 4.00 | A+ | 3.00 | B | 3.50 | A- | 4.00 | A+ | 4.00 | A+ | 3.75 | A | 4.00 | A+ | 3.75 | A | 76.75 | 3.74 | 20.50 | 3.74 | P |
| 19 | B220305018 | MD. ARMAN HOSSAIN | 3.75 | A | 3.25 | B+ | 3.75 | A | 2.75 | B- | 2.50 | C+ | 3.25 | B+ | 4.00 | A+ | 3.50 | A- | 66.63 | 3.25 | 20.50 | 3.25 | P |
| 20 | B220305019 | SHOAIB MAHAMUD SOWVIK | 4.00 | A+ | 3.50 | A- | 3.75 | A | 2.25 | C | 3.50 | A- | 3.50 | A- | 4.00 | A+ | 3.75 | A | 71.13 | 3.47 | 20.50 | 3.47 | P |
| 21 | B220305020 | MD. ARIFUR RAHMAN | 3.75 | A | 3.00 | B | 3.50 | A- | 3.00 | B | 2.75 | B- | 3.75 | A | 4.00 | A+ | 3.75 | A | 69.25 | 3.38 | 20.50 | 3.38 | P |
| 22 | B220305021 | MD. MAHMUDUL HASAN | 2.00 | D | 2.00 | D | 0.00 | F | 0.00 | F | 0.00 | F | 0.00 | F | 2.00 | D | 3.50 | A- | 24.50 | 1.20 | 20.50 | 1.20 | CP |
| 23 | B220305022 | MD. TOUFIKUL ISLAM | 2.75 | B- | 2.75 | B- | 3.50 | A- | 3.25 | B+ | 3.25 | B+ | 3.25 | B+ | 4.00 | A+ | 3.75 | A | 66.25 | 3.23 | 20.50 | 3.23 | P |
| 24 | B220305023 | JIBON CHANDRO ROY | 3.00 | B | 2.75 | B- | 3.00 | B | 2.50 | C+ | 2.00 | D | 2.00 | D | 3.50 | A- | 3.75 | A | 56.00 | 2.73 | 20.50 | 2.73 | P |
| 25 | B220305024 | MD. NAYEM ISLAM | 3.50 | A- | 0.00 | F | 2.00 | D | 2.25 | C | 3.00 | B | 2.00 | D | 2.50 | C+ | 3.50 | A- | 48.25 | 2.35 | 20.50 | 2.35 | CP |
| 26 | B220305025 | MD. KHALEDUR RAHMAN ZIHAD | 3.25 | B+ | 2.25 | C | 3.00 | B | 3.25 | B+ | 3.00 | B | 2.50 | C+ | 4.00 | A+ | 3.75 | A | 62.50 | 3.05 | 20.50 | 3.05 | P |
| 27 | B220305026 | MUFAZZER HOSSAIN ANAS | 4.00 | A+ | 3.75 | A | 4.00 | A+ | 3.00 | B | 3.00 | B | 3.50 | A- | 4.00 | A+ | 3.50 | A- | 72.25 | 3.52 | 20.50 | 3.52 | P |
| 28 | B220305027 | ISRAT BINTE RASHID | 3.75 | A | 2.75 | B- | 3.50 | A- | 3.50 | A- | 3.75 | A | 3.75 | A | 4.00 | A+ | 3.75 | A | 73.00 | 3.56 | 20.50 | 3.56 | P |
| 29 | B220305028 | SUMIA AKTER SRITY | 4.00 | A+ | 3.75 | A | 3.00 | B | 4.00 | A+ | 4.00 | A+ | 4.00 | A+ | 4.00 | A+ | 3.75 | A | 79.00 | 3.85 | 20.50 | 3.85 | P |
| 30 | B220305029 | MD. MEHEDI HASAN | 4.00 | A+ | 3.00 | B | 3.50 | A- | 3.50 | A- | 2.50 | C+ | 3.50 | A- | 4.00 | A+ | 3.75 | A | 70.00 | 3.41 | 20.50 | 3.41 | P |
| 31 | B220305030 | JOYANONDA GHOSH | 3.75 | A | 3.00 | B | 3.00 | B | 3.25 | B+ | 3.25 | B+ | 3.00 | B | 4.00 | A+ | 3.75 | A | 68.50 | 3.34 | 20.50 | 3.34 | P |
| 32 | B220305031 | SARKAR SADMAN RAGIB MUGDHO | 3.00 | B | 2.75 | B- | 3.25 | B+ | 3.00 | B | 2.75 | B- | 3.25 | B+ | 4.00 | A+ | 3.50 | A- | 63.63 | 3.10 | 20.50 | 3.10 | P |
| 33 | B220305033 | TASNIA RYSA | 4.00 | A+ | 3.50 | A- | 4.00 | A+ | 3.75 | A | 3.25 | B+ | 3.25 | B+ | 4.00 | A+ | 3.50 | A- | 73.75 | 3.60 | 20.50 | 3.60 | P |
| 34 | B220305034 | SUSMITA AKTER | 3.75 | A | 3.00 | B | 4.00 | A+ | 3.50 | A- | 4.00 | A+ | 3.50 | A- | 4.00 | A+ | 3.75 | A | 74.50 | 3.63 | 20.50 | 3.63 | P |
| 35 | B220305035 | MD.TAIJUL ISLAM TANIM | 3.75 | A | 2.00 | D | 2.25 | C | 3.25 | B+ | 3.75 | A | 3.25 | B+ | 4.00 | A+ | 3.75 | A | 66.63 | 3.25 | 20.50 | 3.25 | P |
| 36 | B220305037 | UMMA HAFSA KASHFI | 3.50 | A- | 3.25 | B+ | 3.75 | A | 4.00 | A+ | 3.25 | B+ | 2.75 | B- | 3.00 | B | 3.75 | A | 70.13 | 3.42 | 20.50 | 3.42 | P |
| 37 | B220305038 | SUSMITA GHOSH | 4.00 | A+ | 2.25 | C | 2.25 | C | 4.00 | A+ | 3.75 | A | 3.75 | A | 4.00 | A+ | 3.50 | A- | 71.13 | 3.47 | 20.50 | 3.47 | P |
| 38 | B220305039 | ANUPOM KUMAR SARDAR | 4.00 | A+ | 0.00 | F | 2.25 | C | 0.00 | F | 2.25 | C | 3.25 | B+ | 3.25 | B+ | 4.00 | A+ | 47.13 | 2.30 | 20.50 | 2.30 | CP |
| 39 | B220305040 | MD ABDUL HAMIM CHOWDHURY | 2.25 | C | 2.00 | D | 2.75 | B- | 2.75 | B- | 2.50 | C+ | 3.75 | A | 3.50 | A- | 3.00 | B | 56.38 | 2.75 | 20.50 | 2.75 | P |
| 40 | B220305042 | MD. MOBARAK HOSEN SADIK | 0.00 | F | 2.50 | C+ | 0.00 | F | 0.00 | F | 0.00 | F | 2.25 | C | 0.00 | F | 2.50 | C+ | 21.75 | 1.06 | 20.50 | 1.06 | CP |
| 41 | B220305043 | ATIK JAWAD | 4.00 | A+ | 3.50 | A- | 3.75 | A | 3.50 | A- | 4.00 | A+ | 3.50 | A- | 4.00 | A+ | 3.75 | A | 76.38 | 3.73 | 20.50 | 3.73 | P |
| 42 | B220305044 | TAHMIDA AZIZA | 4.00 | A+ | 4.00 | A+ | 3.25 | B+ | 3.75 | A | 4.00 | A+ | 4.00 | A+ | 4.00 | A+ | 4.00 | A+ | 80.13 | 3.91 | 20.50 | 3.91 | P |
| 43 | B220305045 | MD. ASHRAFUL ISLAM ANTO | 3.00 | B | 0.00 | F | 2.00 | D | 0.00 | F | 2.00 | D | 0.00 | F | 2.00 | D | 3.75 | A | 31.25 | 1.52 | 20.50 | 1.52 | CP |
| 44 | B220305046 | MD. JAHID HASAN | 3.25 | B+ | 2.00 | D | 3.00 | B | 0.00 | F | 2.25 | C | 2.75 | B- | 3.00 | B | 3.75 | A | 49.50 | 2.41 | 20.50 | 2.41 | CP |
| 45 | B220305047 | ANIK KHONDOKAR | 3.75 | A | 3.25 | B+ | 3.50 | A- | 3.25 | B+ | 3.75 | A | 3.50 | A- | 4.00 | A+ | 3.75 | A | 73.00 | 3.56 | 20.50 | 3.56 | P |
| 46 | B220305049 | MD. SOHAG | 3.75 | A | 2.50 | C+ | 3.25 | B+ | 3.00 | B | 4.00 | A+ | 3.25 | B+ | 4.00 | A+ | 3.50 | A- | 68.88 | 3.36 | 20.50 | 3.36 | P |
| 47 | B220305050 | LUTFUN NAHAR | 3.25 | B+ | 3.00 | B | 3.00 | B | 3.25 | B+ | 3.25 | B+ | 3.25 | B+ | 2.75 | B- | 3.50 | A- | 65.75 | 3.21 | 20.50 | 3.21 | P |
| 48 | B220305053 | SHEAK NOOR MOHAMMAD NABIL | 3.75 | A | 3.25 | B+ | 3.25 | B+ | 3.50 | A- | 4.00 | A+ | 3.50 | A- | 4.00 | A+ | 3.75 | A | 74.13 | 3.62 | 20.50 | 3.62 | P |
| 49 | B220305054 | TAHSHIN JANNAT APSHORA | 3.75 | A | 0.00 | F | 0.00 | F | 3.25 | B+ | 2.50 | C+ | 3.75 | A | 4.00 | A+ | 3.50 | A- | 54.25 | 2.65 | 20.50 | 2.65 | CP |
| 50 | B220305055 | SHAFAYET JAMIL | 3.50 | A- | 3.00 | B | 3.75 | A | 2.50 | C+ | 3.00 | B | 3.25 | B+ | 3.75 | A | 3.25 | B+ | 64.88 | 3.16 | 20.50 | 3.16 | P |
| 51 | B220305056 | ATASI SHARMA | 3.75 | A | 2.75 | B- | 3.25 | B+ | 3.00 | B | 3.25 | B+ | 3.00 | B | 4.00 | A+ | 3.75 | A | 67.38 | 3.29 | 20.50 | 3.29 | P |
"""


class JagannathUniversityBatchCalculationTestCase(TestCase):
    """
    Validates end-to-end mathematical precision and statistical integrity on the 51-student cohort.
    """

    def setUp(self):
        self.parser = MarkdownSheetParser()
        self.parsed_sheet = self.parser.parse_markdown_content(JNU_DATASET)
        self.dict_sheet = self.parsed_sheet.as_dict()

    def test_parser_detected_metadata_and_structure(self):
        self.assertEqual(self.parsed_sheet.institution, "Jagannath University")
        self.assertEqual(self.parsed_sheet.program, "Department of Computer Science & Engineering")
        self.assertEqual(len(self.parsed_sheet.courses), 8)
        self.assertEqual(len(self.parsed_sheet.students), 51)

        total_credits = sum(c.credit_hours for c in self.parsed_sheet.courses)
        self.assertEqual(total_credits, Decimal("20.50"))

    def test_all_51_students_grade_point_arithmetic(self):
        course_credits = {c.course_code: c.credit_hours for c in self.parsed_sheet.courses}
        total_cr = Decimal("20.50")

        scale_map = {
            Decimal("4.00"): "A+",
            Decimal("3.75"): "A",
            Decimal("3.50"): "A-",
            Decimal("3.25"): "B+",
            Decimal("3.00"): "B",
            Decimal("2.75"): "B-",
            Decimal("2.50"): "C+",
            Decimal("2.25"): "C",
            Decimal("2.00"): "D",
            Decimal("0.00"): "F",
        }

        for student in self.parsed_sheet.students:
            calculated_tgp = Decimal("0.00")
            for res in student.results:
                gp = res.grade_point
                lg = res.letter_grade
                cr = course_credits[res.course_code]

                # Check LG to GP mapping
                self.assertEqual(
                    lg, scale_map[gp],
                    f"Grade scale mismatch for {student.student_id} in {res.course_code}: {gp} -> {lg}"
                )

                if gp > Decimal("0.00"):
                    calculated_tgp += (gp * cr)

            extracted_tgp = student.current_semester_summary.grade_points
            extracted_gpa = student.current_semester_summary.gpa
            calculated_gpa = (calculated_tgp / total_cr).quantize(Decimal("0.01"))

            self.assertAlmostEqual(
                float(calculated_tgp), float(extracted_tgp), delta=0.05,
                msg=f"Total GP mismatch for {student.student_id}: calc {calculated_tgp} != ext {extracted_tgp}"
            )
            self.assertAlmostEqual(
                float(calculated_gpa), float(extracted_gpa), delta=0.02,
                msg=f"GPA mismatch for {student.student_id}: calc {calculated_gpa} != ext {extracted_gpa}"
            )

    def test_validation_engine_all_valid(self):
        val_engine = SheetValidationEngine()
        validated = val_engine.validate_sheet(self.parsed_sheet)
        self.assertEqual(validated.valid_students_count, 51)
        self.assertEqual(validated.invalid_students_count, 0)
        self.assertEqual(validated.needs_review_students_count, 0)

    def test_statistical_distribution_engine(self):
        students_data = self.dict_sheet["students"]
        courses_data = self.dict_sheet["courses"]

        class_stats = DeterministicAnalysisEngine.analyze_class_semester(students_data)
        self.assertEqual(class_stats["total_students"], 51)
        self.assertEqual(class_stats["highest_gpa"], 3.91)
        self.assertEqual(class_stats["lowest_gpa"], 1.06)
        self.assertEqual(class_stats["average_gpa"], 3.15)
        self.assertEqual(class_stats["median_gpa"], 3.36)

        subject_stats = DeterministicAnalysisEngine.analyze_subjects(students_data, courses_data)
        self.assertEqual(len(subject_stats), 8)

    def test_ranking_engine_ranks_and_ties(self):
        students_data = self.dict_sheet["students"]
        courses_data = self.dict_sheet["courses"]

        rankings = DeterministicRankingEngine.rank_all(students_data, courses_data)
        sem_ranks = rankings.get("semester_rankings", {})

        # Top student: Tahmida Aziza (3.91) -> Rank 1
        self.assertEqual(sem_ranks["B220305044"]["rank"], 1)
        self.assertEqual(sem_ranks["B220305044"]["score"], 3.91)
        self.assertFalse(sem_ranks["B220305044"]["is_tied"])

        # Tied 2nd: Tahmina Akter (3.85) and Sumia Akter Srity (3.85) -> Rank 2 (Tie)
        self.assertEqual(sem_ranks["B220305016"]["rank"], 2)
        self.assertTrue(sem_ranks["B220305016"]["is_tied"])
        self.assertEqual(sem_ranks["B220305028"]["rank"], 2)
        self.assertTrue(sem_ranks["B220305028"]["is_tied"])

        # 4th rank following the tie: Nazmul Hasan (3.84) -> Rank 4
        self.assertEqual(sem_ranks["B220305008"]["rank"], 4)

    def test_export_report_builders_and_file_generation(self):
        session = ResultSession.objects.create(
            original_filename="jnu_batch_test.md",
            file_size_bytes=len(JNU_DATASET.encode("utf-8")),
            status="VERIFIED",
            parsed_dataset=self.dict_sheet,
        )

        try:
            # Student Report & Exporters
            student_data = build_student_report_data(session, "B220305044")
            self.assertEqual(student_data["student_info"]["student_name"], "TAHMIDA AZIZA")
            self.assertEqual(student_data["academic_summary"]["semester_gpa"], 3.91)

            pdf_bytes = build_student_pdf(student_data)
            self.assertGreater(len(pdf_bytes), 2000)

            excel_bytes = build_student_excel(student_data)
            self.assertGreater(len(excel_bytes), 2000)

            # Class Report & Exporter
            class_data = build_class_report_data(session)
            self.assertEqual(class_data["class_overview"]["total_students"], 51)
            class_pdf_bytes = build_class_pdf(class_data)
            self.assertGreater(len(class_pdf_bytes), 2000)

            # Comparison Report & Exporter
            comp_data = build_comparison_report_data(session, "B220305044", "B220305016")
            self.assertEqual(comp_data["deltas"]["gpa_difference"], 0.06)
            comp_pdf_bytes = build_comparison_pdf(comp_data)
            self.assertGreater(len(comp_pdf_bytes), 2000)

        finally:
            session.delete()
