"""
Tests for Claude AI Markdown Result Sheet Parser.
"""
from decimal import Decimal
from django.test import TestCase
from apps.processing.parser.markdown_parser import MarkdownSheetParser


class MarkdownParserTests(TestCase):
    def setUp(self):
        self.parser = MarkdownSheetParser()

    def test_parse_valid_claude_markdown_table(self):
        markdown_content = """
# Academic Result Sheet
- **Institution**: Jagannath University
- **Department**: Department of Computer Science & Engineering
- **Semester**: B.Sc. 1st Year 2nd Semester Examination 2023
- **Session**: 2022-2023
- **TCP**: 21.5

| S/N | Student ID | Student Name | CSE-1201 GP | CSE-1201 LG | CSEL-1202 GP | CSEL-1202 LG | CSE-1203 GP | CSE-1203 LG | CSEL-1204 GP | CSEL-1204 LG | CSE-1205 GP | CSE-1205 LG | CSEL-1206 GP | CSEL-1206 LG | CSEG-1207 GP | CSEG-1207 LG | CSEG-1208 GP | CSEG-1208 LG | CSEG-1209 GP | CSEG-1209 LG | CSEV-1210 GP | CSEV-1210 LG | Total GP | GPA | Cumulative Credits | CGPA | Result Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 26 | B220305026 | MUFAZZER HOSSAIN ANAS | 4.00 | A+ | 4.00 | A+ | 3.50 | A- | 4.00 | A+ | 4.00 | A+ | 4.00 | A+ | 3.50 | A- | 3.75 | A | 4.00 | A+ | 3.75 | A | 82.25 | 3.83 | 42.00 | 3.64 | P |
| 27 | B220305027 | ISRAT BENTE RASHID | 3.50 | A- | 4.00 | A+ | 3.75 | A | 4.00 | A+ | 3.50 | A- | 3.75 | A | 3.50 | A- | 4.00 | A+ | 4.00 | A+ | 3.75 | A | 79.75 | 3.71 | 42.00 | 3.57 | P |
| 28 | B220305028 | SUMIA AKTER SRITY | 4.00 | A+ | 3.50 | A- | 3.75 | A | 3.75 | A | 4.00 | A+ | 4.00 | A+ | 3.75 | A | 0.00 | F | 3.75 | A | 4.00 | A+ | 71.63 | 3.33 | 42.00 | 3.42 | P |
"""
        sheet = self.parser.parse_markdown_content(markdown_content)
        self.assertEqual(len(sheet.students), 3)
        self.assertEqual(len(sheet.courses), 10)
        
        s1 = sheet.students[0]
        self.assertEqual(s1.student_id, "B220305026")
        self.assertEqual(s1.student_name, "MUFAZZER HOSSAIN ANAS")
        self.assertEqual(len(s1.results), 10)
        self.assertEqual(s1.results[0].grade_point, Decimal("4.00"))
        self.assertEqual(s1.results[0].letter_grade, "A+")
        self.assertIsNotNone(s1.current_semester_summary)
        self.assertIsNotNone(s1.cumulative_summary)
        self.assertEqual(s1.cumulative_summary.cgpa, Decimal("3.64"))

    def test_parse_embedded_json_in_markdown(self):
        json_markdown = """
```json
[
  {
    "student_id": "B220305029",
    "student_name": "MD. MEHEDI HASAN",
    "serial_no": 29,
    "gpa": 3.19,
    "cgpa": 3.29,
    "results": [
      {"course_code": "CSE-1201", "grade_point": 3.25, "letter_grade": "B+"}
    ]
  }
]
```
"""
        sheet = self.parser.parse_markdown_content(json_markdown)
        self.assertEqual(len(sheet.students), 1)
        self.assertEqual(sheet.students[0].student_id, "B220305029")
        self.assertEqual(sheet.students[0].student_name, "MD. MEHEDI HASAN")
