"""
Universal Markdown Result Sheet Parser.

Supports:
  - ANY University / College / Department / Degree (e.g. CSE, EEE, BBA, Pharmacy, English, Law, etc.)
  - ANY Semester (1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 4.1, 4.2, Masters, etc.)
  - ANY Batch / Session (2018-2019, 2022-2023, 2024, etc.)
  - ANY number of dynamic courses (1 to 30+ courses)
  - Multi-page merged tables sorted by S/N & Student ID
  - Automatic detection of Course Codes, Course Titles, Credit Hours from Markdown headers & Course Lists
  - GPA, CGPA, TGP, and credit calculation and verification
"""

from __future__ import annotations

import json
import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from .normalizer import (
    normalize_course_code,
    normalize_grade_point,
    normalize_letter_grade,
    normalize_student_id,
    normalize_student_name,
)
from .schema import (
    ParsedCourse,
    ParsedCumulativeSummary,
    ParsedCurrentSemesterSummary,
    ParsedSheet,
    ParsedStudent,
    ParsedStudentResult,
)
from .template import ResultSheetTemplate, get_default_template

logger = logging.getLogger(__name__)

RE_COURSE_HEADER = re.compile(r"([A-Z]{2,6}[\s_\-]?[0-9]{3,4}[A-Z]?)", re.IGNORECASE)
RE_CREDIT_EXTRACT = re.compile(r"(?:credit|cr|ch|credits)?[\s:=]*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)


class MarkdownSheetParser:
    """
    Universal Parser for Markdown result tables and text extracted from any vision AI
    (Claude, Google AI Studio Gemini Pro, ChatGPT, etc.).
    """

    def __init__(self, template: Optional[ResultSheetTemplate] = None):
        self.template = template or get_default_template()

    def parse_markdown_content(self, md_content: str, filename: str = "ai_extracted.md") -> ParsedSheet:
        """
        Dynamically parse markdown content for any institution, department, semester, and course list.
        """
        lines = md_content.strip().splitlines()
        warnings: List[str] = []

        # 1. Dynamically extract metadata and declared course list from document headers/body
        meta = self._extract_metadata(lines)
        declared_courses = self._extract_declared_course_list(lines)

        # 2. Check for embedded JSON block first
        json_match = re.search(r"```(?:json)?\s*(\[\s*\{.*?\}\s*\]|\{\s*\"students\".*?\})\s*```", md_content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                return self._parse_from_json_data(data, meta, filename, declared_courses)
            except Exception as e:
                logger.warning(f"Failed parsing embedded JSON block: {e}")

        # 3. Locate Markdown Table Lines
        table_lines = [line.strip() for line in lines if line.strip().startswith("|") and line.strip().endswith("|")]
        if not table_lines or len(table_lines) < 2:
            table_lines = [line.strip() for line in lines if "|" in line]

        if not table_lines:
            warnings.append("No Markdown table (| ... |) detected in the provided file.")
            return ParsedSheet(
                institution=meta.get("institution", "University"),
                program=meta.get("program", "Department"),
                semester=meta.get("semester", "Academic Semester"),
                exam_session=meta.get("exam_session", ""),
                courses=[],
                students=[],
                template_name="Universal AI Parser",
                overall_confidence=0.0,
                warnings=warnings,
                metadata={"source_type": "markdown", "filename": filename},
            )

        # Separate header row from data rows
        header_line = table_lines[0]
        data_lines = []
        for line in table_lines[1:]:
            # Skip separator line (e.g. |---|---|---|)
            if re.match(r"^\|[\s\-:|]+\|$", line):
                continue
            data_lines.append(line)

        raw_headers = [c.strip() for c in header_line.strip("|").split("|")]

        # 4. Dynamically detect and map all course columns from the table headers
        courses, col_mapping = self._map_columns_dynamically(raw_headers, declared_courses)

        # 5. Parse every student row
        students: List[ParsedStudent] = []
        for row_idx, row_line in enumerate(data_lines):
            raw_cells = [c.strip() for c in row_line.strip("|").split("|")]
            if len(raw_cells) < 3:
                continue

            student = self._parse_table_row(
                row_idx=row_idx,
                cells=raw_cells,
                headers=raw_headers,
                courses=courses,
                col_mapping=col_mapping,
            )
            if student:
                students.append(student)

        # Sort students cleanly by Serial Number (S/N) or Student ID
        students.sort(key=lambda s: (s.serial_no if s.serial_no is not None else 9999, s.student_id))

        if not students:
            warnings.append("Could not extract valid student records from Markdown table.")

        overall_conf = 0.99 if students else 0.0

        return ParsedSheet(
            institution=meta.get("institution", "University"),
            program=meta.get("program", "Department"),
            semester=meta.get("semester", "Academic Semester"),
            exam_session=meta.get("exam_session", ""),
            courses=courses,
            students=students,
            template_name="Universal AI Parser",
            overall_confidence=overall_conf,
            warnings=warnings,
            metadata={
                "source_type": "ai_markdown_universal",
                "filename": filename,
                "total_rows_parsed": len(students),
                "total_courses_detected": len(courses),
                "institution": meta.get("institution"),
                "department": meta.get("program"),
                "semester": meta.get("semester"),
                "session": meta.get("exam_session"),
            },
        )

    # -----------------------------------------------------------------------
    # Metadata & Declared Course List Extraction
    # -----------------------------------------------------------------------

    def _extract_metadata(self, lines: List[str]) -> Dict[str, str]:
        """Dynamically extracts institution, department, semester, session, and credit from headers."""
        meta = {
            "institution": "Jagannath University",
            "program": "Department",
            "semester": "Examination Results",
            "exam_session": "",
            "tcp": "",
        }
        for line in lines[:30]:
            l = line.strip()
            # 1. Total Semester Credit / TCP
            if re.search(r"\b(tcp|total credit|semester credit|credit)\b", l, re.I) and not l.startswith("|"):
                val = re.sub(r"^[^:]+:\s*", "", l).strip("*# -`")
                if val:
                    meta["tcp"] = val
            # 2. Institution
            elif re.search(r"\b(institution|university|college|inst)\b", l, re.I) and not l.startswith("|"):
                val = re.sub(r"^[^:]+:\s*", "", l).strip("*# -`")
                if val and len(val) > 2:
                    meta["institution"] = val
            # 3. Department / Faculty / Program
            elif re.search(r"\b(department|dept|program|faculty|discipline)\b", l, re.I) and not l.startswith("|"):
                val = re.sub(r"^[^:]+:\s*", "", l).strip("*# -`")
                if val and len(val) > 2:
                    meta["program"] = val
            # 4. Session / Batch
            elif re.search(r"\b(session|batch|academic session)\b", l, re.I) and not l.startswith("|"):
                val = re.sub(r"^[^:]+:\s*", "", l).strip("*# -`")
                if val and len(val) > 2:
                    meta["exam_session"] = val
            # 5. Semester / Examination
            elif re.search(r"\b(semester|exam|examination|year|term)\b", l, re.I) and not l.startswith("|"):
                val = re.sub(r"^[^:]+:\s*", "", l).strip("*# -`")
                if val and len(val) > 2:
                    meta["semester"] = val

        return meta

    def _extract_declared_course_list(self, lines: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Extracts Course List defined in bullet points or numbered lists
        (e.g. `- [CSE-1201]: OOP-I (Credit: 3.00)` or `- **CSE-1201**: Title` or `1. CSE-1201: Title (Credit: 3)`).
        """
        declared: Dict[str, Dict[str, Any]] = {}
        for line in lines:
            l = line.strip()
            if not l or (l.startswith("|") and ("student" in l.lower() or "gpa" in l.lower() or "s/n" in l.lower())):
                continue

            # Match bullet points / numbered lists:
            # Matches: - [CSE-1201]: Title, - **CSE-1201**: Title, - `CSE-1201`: Title, 1. CSE-1201 - Title, etc.
            m = re.match(r"^[ \t*#\-0-9.]*\[?\*?`?([A-Za-z]{2,6}[\s_\-]?[0-9]{3,4}[A-Za-z]?)`?\*?\]?\s*[:\-–]\s*(.*?)$", l)
            if not m:
                m = re.match(r"^[ \t*#\-0-9.]*\[([A-Za-z]{2,6}[\s_\-]?[0-9]{3,4}[A-Za-z]?)\]\s*[:\-–]?\s*(.*?)$", l)

            if m:
                code_raw = m.group(1).upper().replace(" ", "").replace("_", "-")
                rest = m.group(2).strip()
                title = rest
                credits = None

                # Extract credit in parentheses e.g. (Credit: 3.00), (Credit 3), (3.0 Credits), (3.0 Cr)
                c_match = re.search(r"\((?:credit|cr|credits)?[\s:=]*([0-9]+(?:\.[0-9]+)?)[^)]*(?:credit|cr|credits)?\)", rest, re.I)
                if not c_match:
                    c_match = re.search(r"\[(?:credit|cr|credits)?[\s:=]*([0-9]+(?:\.[0-9]+)?)[^\]]*\]", rest, re.I)

                if c_match:
                    try:
                        credits = Decimal(c_match.group(1))
                    except InvalidOperation:
                        pass
                    # Remove only the credit portion from the title
                    title = rest[:c_match.start()] + rest[c_match.end():]

                clean_title = title.strip(" -:,\t[]*`")
                if clean_title:
                    declared[code_raw] = {
                        "course_code": code_raw,
                        "course_title": clean_title,
                        "credit_hours": credits or self._infer_default_credit(code_raw, clean_title),
                    }

        return declared

    def _infer_default_credit(self, course_code: str, course_title: str = "") -> Decimal:
        """Heuristic for determining default credit hours if not specified."""
        code_upper = course_code.upper()
        title_upper = course_title.upper()
        
        # Lab, Sessional, Practical, Project Lab, Viva
        if (
            "LAB" in code_upper or 
            "LAB" in title_upper or 
            "SESSIONAL" in title_upper or 
            "PRACTICAL" in title_upper or 
            code_upper.endswith("L") or 
            "VIVA" in code_upper or 
            "VIVA" in title_upper or
            "PROJECT" in title_upper
        ):
            return Decimal("1.50")
        
        return Decimal("3.00")

    # -----------------------------------------------------------------------
    # Dynamic Course & Column Mapping
    # -----------------------------------------------------------------------

    def _map_columns_dynamically(
        self, 
        headers: List[str], 
        declared_courses: Dict[str, Dict[str, Any]]
    ) -> Tuple[List[ParsedCourse], Dict[str, Any]]:
        """
        Dynamically inspects table headers to locate S/N, Student ID, Student Name,
        all Course GP & LG columns, and Summary metrics.
        """
        col_mapping = {
            "sn_idx": None,
            "id_idx": None,
            "name_idx": None,
            "course_gp_idx": {},   # course_code -> col_idx
            "course_lg_idx": {},   # course_code -> col_idx
            "tgp_idx": None,
            "gpa_idx": None,
            "cum_credits_idx": None,
            "cgpa_idx": None,
            "status_idx": None,
        }

        # 1. Identify standard fixed columns
        for idx, h in enumerate(headers):
            hl = h.lower().replace(" ", "").replace("_", "").replace("-", "")
            
            if hl in ("sn", "sl", "s/n", "slno", "serial", "serialno", "no"):
                col_mapping["sn_idx"] = idx
            elif "studentid" in hl or hl in ("id", "roll", "rollno", "stdid", "reg", "regno"):
                col_mapping["id_idx"] = idx
            elif "studentname" in hl or hl in ("name", "student", "candidatesname", "student'sname"):
                col_mapping["name_idx"] = idx
            elif hl in ("totalgp", "tgp", "totalgradepoints", "totalgradepoint", "gp_total"):
                col_mapping["tgp_idx"] = idx
            elif hl in ("gpa", "semestergpa", "sgpa", "currentgpa", "sem_gpa"):
                col_mapping["gpa_idx"] = idx
            elif "cgpa" in hl or hl in ("cumulativegpa", "cumulativecgpa", "cum_gpa"):
                col_mapping["cgpa_idx"] = idx
            elif "credit" in hl and ("total" in hl or "cum" in hl or "earned" in hl):
                col_mapping["cum_credits_idx"] = idx
            elif hl in ("status", "result", "resultstatus", "remarks", "passed"):
                col_mapping["status_idx"] = idx

        # Fallbacks for ID and Name if headers were unconventional
        if col_mapping["id_idx"] is None:
            col_mapping["id_idx"] = 1 if len(headers) > 1 else 0
        if col_mapping["name_idx"] is None:
            col_mapping["name_idx"] = 2 if len(headers) > 2 else 1

        # 2. Discover all Course Columns dynamically
        detected_course_codes: List[str] = []
        course_column_pairs: Dict[str, Dict[str, Optional[int]]] = {}

        for idx, h in enumerate(headers):
            # Skip known non-course summary columns
            if idx in (
                col_mapping["sn_idx"], 
                col_mapping["id_idx"], 
                col_mapping["name_idx"],
                col_mapping["tgp_idx"],
                col_mapping["gpa_idx"],
                col_mapping["cum_credits_idx"],
                col_mapping["cgpa_idx"],
                col_mapping["status_idx"],
            ):
                continue

            # Look for a Course Code pattern in the header
            code_match = RE_COURSE_HEADER.search(h)
            if code_match:
                code_raw = code_match.group(1).upper().replace(" ", "").replace("_", "-")
                if code_raw not in detected_course_codes:
                    detected_course_codes.append(code_raw)
                    course_column_pairs[code_raw] = {"gp": None, "lg": None}

                if "LG" in h.upper() or "GRADE" in h.upper() or "LETTER" in h.upper():
                    course_column_pairs[code_raw]["lg"] = idx
                elif "GP" in h.upper() or "POINT" in h.upper() or course_column_pairs[code_raw]["gp"] is None:
                    course_column_pairs[code_raw]["gp"] = idx
            else:
                # If no code in header, but it's an unassigned middle column
                h_clean = h.strip()
                if h_clean and idx > (col_mapping["name_idx"] or 1):
                    # Check if it's before summary columns
                    is_summary = any(kw in h_clean.lower() for kw in ("gpa", "cgpa", "total", "credit", "result", "status", "remarks"))
                    if not is_summary:
                        synthetic_code = f"COURSE-{len(detected_course_codes) + 1}"
                        if synthetic_code not in detected_course_codes:
                            detected_course_codes.append(synthetic_code)
                            course_column_pairs[synthetic_code] = {"gp": idx, "lg": None}

        # Also incorporate declared courses if headers had no direct codes
        if not detected_course_codes and declared_courses:
            for code in declared_courses.keys():
                detected_course_codes.append(code)
                course_column_pairs[code] = {"gp": None, "lg": None}

        # Build ParsedCourse objects
        courses: List[ParsedCourse] = []
        for i, code in enumerate(detected_course_codes):
            pair = course_column_pairs.get(code, {})
            gp_idx = pair.get("gp")
            lg_idx = pair.get("lg")

            # If GP index was not found by pattern, map sequentially
            if gp_idx is None:
                start_col = max((col_mapping["name_idx"] or 2) + 1, 3)
                gp_idx = start_col + (i * 2)
                lg_idx = gp_idx + 1 if (gp_idx + 1) < len(headers) else None

            col_mapping["course_gp_idx"][code] = gp_idx
            if lg_idx is not None:
                col_mapping["course_lg_idx"][code] = lg_idx

            decl = declared_courses.get(code)
            if not decl:
                norm_code = re.sub(r'[^A-Za-z0-9]', '', code).upper()
                for d_k, d_v in declared_courses.items():
                    if re.sub(r'[^A-Za-z0-9]', '', d_k).upper() == norm_code:
                        decl = d_v
                        break
            if not decl:
                decl = {}

            title = decl.get("course_title", "")
            cred = decl.get("credit_hours", self._infer_default_credit(code, title))

            courses.append(ParsedCourse(
                course_code=code,
                course_code_raw=code,
                course_title=title,
                credit_hours=cred,
                column_index=i,
                gp_col_index=gp_idx,
                lg_col_index=lg_idx,
                confidence=1.0,
                metadata={"detected_dynamically": True},
            ))

        return courses, col_mapping

    # -----------------------------------------------------------------------
    # Row Parsing
    # -----------------------------------------------------------------------

    def _parse_table_row(
        self,
        row_idx: int,
        cells: List[str],
        headers: List[str],
        courses: List[ParsedCourse],
        col_mapping: Dict[str, Any],
    ) -> Optional[ParsedStudent]:
        """Parse a single student row with dynamic courses."""
        # 1. Student ID
        id_idx = col_mapping.get("id_idx", 1)
        raw_id = cells[id_idx] if id_idx < len(cells) else ""
        norm_id, id_raw, is_valid_id, id_warn = normalize_student_id(raw_id)

        if not norm_id:
            return None

        # 2. Student Name
        name_idx = col_mapping.get("name_idx", 2)
        raw_name = cells[name_idx] if name_idx < len(cells) else ""
        norm_name, name_raw, is_valid_name, name_warn = normalize_student_name(raw_name)

        # 3. Serial Number
        sn_idx = col_mapping.get("sn_idx")
        sn_raw = cells[sn_idx] if sn_idx is not None and sn_idx < len(cells) else str(row_idx + 1)
        digits_only = re.sub(r"\D", "", sn_raw)
        serial_no = int(digits_only) if digits_only else (row_idx + 1)

        # 4. Course Results
        results: List[ParsedStudentResult] = []
        earned_credits = Decimal("0.00")
        total_grade_points = Decimal("0.00")
        total_course_credits = Decimal("0.00")
        review_reasons: List[str] = []

        for course in courses:
            c_code = course.course_code
            gp_idx = col_mapping["course_gp_idx"].get(c_code)
            lg_idx = col_mapping["course_lg_idx"].get(c_code)

            raw_gp = cells[gp_idx] if (gp_idx is not None and gp_idx < len(cells)) else ""
            raw_lg = cells[lg_idx] if (lg_idx is not None and lg_idx < len(cells)) else ""

            norm_gp, _, is_valid_gp, gp_warn = normalize_grade_point(raw_gp)
            norm_lg, _, _, _ = normalize_letter_grade(raw_lg)

            # Auto-infer letter grade from GP if missing
            if not norm_lg and norm_gp is not None:
                for lg_k, (gp_scale, _) in self.template.grading_scale.items():
                    if norm_gp == gp_scale:
                        norm_lg = lg_k
                        break

            c_cred = course.credit_hours or Decimal("3.00")
            total_course_credits += c_cred

            if norm_gp is not None and norm_gp > Decimal("0.00"):
                earned_credits += c_cred
                total_grade_points += (norm_gp * c_cred)

            res_review = []
            if not is_valid_gp and gp_warn:
                res_review.append(gp_warn)

            results.append(ParsedStudentResult(
                course_code=c_code,
                grade_point=norm_gp,
                grade_point_raw=raw_gp,
                letter_grade=norm_lg,
                letter_grade_raw=raw_lg,
                is_valid_match=True if (norm_gp is not None and norm_lg) else None,
                confidence=1.0 if is_valid_gp else 0.85,
                requires_review=bool(res_review),
                review_reasons=res_review,
            ))

        # 5. Compute or extract GPA
        calc_gpa = None
        if total_course_credits > Decimal("0.00"):
            calc_gpa = (total_grade_points / total_course_credits).quantize(Decimal("0.01"))

        gpa_idx = col_mapping.get("gpa_idx")
        extracted_gpa = None
        if gpa_idx is not None and gpa_idx < len(cells):
            try:
                clean_num = re.sub(r"[^\d.]", "", cells[gpa_idx])
                if clean_num:
                    extracted_gpa = Decimal(clean_num)
            except (InvalidOperation, ValueError):
                pass

        final_gpa = calc_gpa if calc_gpa is not None else extracted_gpa

        # 6. Cumulative CGPA & Cumulative Credits
        cgpa_idx = col_mapping.get("cgpa_idx")
        extracted_cgpa = None
        if cgpa_idx is not None and cgpa_idx < len(cells):
            try:
                clean_cgpa = re.sub(r"[^\d.]", "", cells[cgpa_idx])
                if clean_cgpa:
                    extracted_cgpa = Decimal(clean_cgpa)
            except (InvalidOperation, ValueError):
                pass

        cum_credits_idx = col_mapping.get("cum_credits_idx")
        extracted_cum_credits = None
        if cum_credits_idx is not None and cum_credits_idx < len(cells):
            try:
                clean_cum_cr = re.sub(r"[^\d.]", "", cells[cum_credits_idx])
                if clean_cum_cr:
                    extracted_cum_credits = Decimal(clean_cum_cr)
            except (InvalidOperation, ValueError):
                pass

        # 1st Semester / 1.1 Special Rule:
        # If CGPA is omitted on the sheet (common in 1.1 first exams), CGPA is identical to GPA
        # and Cumulative Credits equals Semester Credits.
        if extracted_cgpa is None and final_gpa is not None:
            extracted_cgpa = final_gpa
        if extracted_cum_credits is None:
            extracted_cum_credits = earned_credits if earned_credits > Decimal("0.00") else total_course_credits

        # 7. Result Status (P / CP / NP / F)
        status_idx = col_mapping.get("status_idx")
        extracted_status = cells[status_idx].strip() if (status_idx is not None and status_idx < len(cells)) else ""
        final_status = extracted_status if extracted_status else ("P" if (final_gpa and final_gpa > Decimal("0.00")) else "F")

        # 8. Summaries
        curr_summary = ParsedCurrentSemesterSummary(
            gpa=final_gpa,
            gpa_raw=str(extracted_gpa or final_gpa or ""),
            grade_points=total_grade_points,
            grade_points_raw=str(total_grade_points),
            earned_credit=earned_credits,
            earned_credit_raw=str(earned_credits),
            total_credit=total_course_credits,
            total_credit_raw=str(total_course_credits),
            result_status=final_status,
            result_status_raw=extracted_status,
        )

        cum_summary = None
        if extracted_cgpa is not None:
            cum_summary = ParsedCumulativeSummary(
                cgpa=extracted_cgpa,
                cgpa_raw=str(extracted_cgpa),
                total_credit=extracted_cum_credits,
                total_credit_raw=str(extracted_cum_credits or ""),
                earned_credit=earned_credits,
                earned_credit_raw=str(earned_credits),
            )

        return ParsedStudent(
            student_id=norm_id,
            student_id_raw=id_raw,
            student_name=norm_name,
            student_name_raw=name_raw,
            serial_no=serial_no,
            serial_no_raw=str(serial_no),
            row_index=row_idx,
            results=results,
            current_semester_summary=curr_summary,
            cumulative_summary=cum_summary,
            confidence=0.99,
            requires_review=bool(review_reasons),
            review_reasons=review_reasons,
        )

    def _parse_from_json_data(
        self, 
        data: Any, 
        meta: Dict[str, str], 
        filename: str,
        declared_courses: Dict[str, Dict[str, Any]]
    ) -> ParsedSheet:
        """Parse structured JSON representation if returned by AI."""
        students_list = data if isinstance(data, list) else data.get("students", [])
        courses_list = data.get("courses", []) if isinstance(data, dict) else []

        # If courses were in JSON
        courses = []
        if courses_list:
            for i, c in enumerate(courses_list):
                courses.append(ParsedCourse(
                    course_code=c.get("course_code", f"COURSE-{i+1}"),
                    course_code_raw=c.get("course_code", ""),
                    course_title=c.get("course_title", ""),
                    credit_hours=Decimal(str(c.get("credit_hours", 3.0))),
                    column_index=i,
                    confidence=1.0,
                ))
        elif declared_courses:
            for i, (code, c_info) in enumerate(declared_courses.items()):
                courses.append(ParsedCourse(
                    course_code=code,
                    course_code_raw=code,
                    course_title=c_info.get("course_title", ""),
                    credit_hours=c_info.get("credit_hours", Decimal("3.0")),
                    column_index=i,
                    confidence=1.0,
                ))

        students = []
        for row_idx, s in enumerate(students_list):
            norm_id, id_raw, _, _ = normalize_student_id(s.get("student_id", ""))
            norm_name, name_raw, _, _ = normalize_student_name(s.get("student_name", ""))
            
            results = []
            earned_credits = Decimal("0.00")
            total_gp = Decimal("0.00")
            total_credits = Decimal("0.00")

            raw_results = s.get("results", {})
            if isinstance(raw_results, list):
                raw_results = {r.get("course_code"): r for r in raw_results}

            for c in courses:
                r_data = raw_results.get(c.course_code, {})
                raw_gp = str(r_data.get("grade_point", r_data.get("gp", "")))
                raw_lg = str(r_data.get("letter_grade", r_data.get("lg", "")))
                
                gp_val, _, _, _ = normalize_grade_point(raw_gp)
                lg_val, _, _, _ = normalize_letter_grade(raw_lg)

                if gp_val is not None and gp_val > Decimal("0.00"):
                    earned_credits += c.credit_hours or Decimal("3.00")
                    total_gp += (gp_val * (c.credit_hours or Decimal("3.00")))
                total_credits += (c.credit_hours or Decimal("3.00"))

                results.append(ParsedStudentResult(
                    course_code=c.course_code,
                    grade_point=gp_val,
                    grade_point_raw=raw_gp,
                    letter_grade=lg_val,
                    letter_grade_raw=raw_lg,
                    confidence=1.0,
                ))

            calc_gpa = (total_gp / total_credits).quantize(Decimal("0.01")) if total_credits > Decimal("0.00") else None
            cgpa_val = Decimal(str(s.get("cgpa"))) if s.get("cgpa") is not None else None

            students.append(ParsedStudent(
                student_id=norm_id or s.get("student_id", ""),
                student_id_raw=id_raw,
                student_name=norm_name or s.get("student_name", ""),
                student_name_raw=name_raw,
                serial_no=s.get("serial_no", row_idx + 1),
                row_index=row_idx,
                results=results,
                current_semester_summary=ParsedCurrentSemesterSummary(
                    gpa=calc_gpa or Decimal(str(s.get("gpa", 0.0))),
                    grade_points=total_gp,
                    earned_credit=earned_credits,
                    total_credit=total_credits,
                    result_status="P" if (calc_gpa and calc_gpa > Decimal("0.00")) else "F",
                ),
                cumulative_summary=ParsedCumulativeSummary(cgpa=cgpa_val) if cgpa_val else None,
                confidence=1.0,
            ))

        return ParsedSheet(
            institution=meta.get("institution", "University"),
            program=meta.get("program", "Department"),
            semester=meta.get("semester", "Academic Semester"),
            exam_session=meta.get("exam_session", ""),
            courses=courses,
            students=students,
            template_name="Universal AI Parser",
            overall_confidence=1.0,
            warnings=[],
            metadata={"source_type": "ai_json", "filename": filename},
        )
