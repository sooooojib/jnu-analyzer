"""
API views for Markdown result sheet processing, verification, scorecards, analytics, and comparison.
"""

import os
import logging
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework import status
from apps.core.responses import success_response, error_response
from apps.core.exceptions import SessionNotFoundError, SessionExpiredError, StudentNotFoundError
from apps.sessions_manager.models import ResultSession
from apps.sessions_manager.serializers import SessionDetailSerializer

from .serializers import CompareRequestSerializer
from .parser.markdown_parser import MarkdownSheetParser
from .validation import ValidationService, FieldValidators, ValidationStatus
from .analysis import AnalysisEngineService
from .ranking import RankingEngineService
from .comparison import ComparisonEngineService

logger = logging.getLogger(__name__)


def get_active_session_or_404(session_id) -> ResultSession:
    try:
        session = ResultSession.objects.get(id=session_id)
    except (ResultSession.DoesNotExist, ValueError):
        raise SessionNotFoundError()

    if session.is_expired:
        session.purge_file()
        session.delete()
        raise SessionExpiredError()

    return session


def _build_verification_payload(session: ResultSession) -> dict:
    """
    Builds the flattened verification table rows and diagnostic summary.
    """
    parsed = session.parsed_dataset or {}
    courses = parsed.get("courses", [])
    students = parsed.get("students", [])

    rows = []
    valid_count = 0
    warning_count = 0
    needs_review_count = 0
    invalid_count = 0

    for s_idx, student in enumerate(students):
        student_id = student.get("student_id", "")
        student_name = student.get("student_name", "")
        results = student.get("results", [])
        student_status = student.get("status", "VALID")

        for course in courses:
            c_code = course.get("course_code", "")
            c_credit = course.get("credit_hours", 3.0)

            # Find matching result
            res = next((r for r in results if r.get("course_code") == c_code), None)
            gp = res.get("grade_point") if res else None
            lg = res.get("letter_grade", "") if res else ""
            res_status = res.get("status", "VALID") if res else "NEEDS_REVIEW"
            warnings = res.get("review_reasons", []) if res else ["No result extracted."]
            corrections = res.get("applied_corrections", []) if res else []

            # Calculate field counts
            if res_status == "VALID":
                valid_count += 1
            elif res_status == "WARNING":
                warning_count += 1
            elif res_status == "NEEDS_REVIEW":
                needs_review_count += 1
            elif res_status == "INVALID":
                invalid_count += 1

            row_item = {
                "row_id": f"{student_id}_{c_code}",
                "student_id": student_id,
                "student_name": student_name,
                "course_code": c_code,
                "credit_hours": c_credit,
                "grade_point": gp,
                "letter_grade": lg,
                "status": res_status,
                "warnings": warnings,
                "errors": [w for w in warnings if "exceeds" in w.lower() or "outside" in w.lower()],
                "applied_corrections": corrections,
                "is_usable_in_calculations": res_status != "INVALID",
            }
            rows.append(row_item)

    return {
        "session_id": str(session.id),
        "status": session.status,
        "original_filename": session.original_filename,
        "summary": {
            "total_students": len(students),
            "total_courses": len(courses),
            "valid_fields_count": valid_count,
            "warnings_count": warning_count,
            "invalid_fields_count": invalid_count,
            "needs_review_count": needs_review_count,
        },
        "courses": courses,
        "rows": rows,
        "students": students,
    }


class ProcessDatasetView(APIView):
    """
    Triggers deterministic Markdown extraction and transitions session to PENDING_VERIFICATION.
    """
    def post(self, request, session_id):
        session = get_active_session_or_404(session_id)
        
        session.status = 'PROCESSING'
        session.save(update_fields=['status'])

        from apps.dataset.models import ResultSheet
        sheet = ResultSheet.objects.filter(id=session.id).first()
        if sheet:
            sheet.status = ResultSheet.ProcessingStatus.PROCESSING
            sheet.save(update_fields=['status'])

        # Deterministic Markdown Parsing
        parsed_data = session.parsed_dataset
        if not parsed_data or not parsed_data.get("students"):
            if session.file_path and os.path.exists(session.file_path):
                try:
                    with open(session.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        md_content = f.read()
                    md_parser = MarkdownSheetParser()
                    parsed_sheet = md_parser.parse_markdown_content(md_content, filename=session.original_filename)
                    parsed_data = parsed_sheet.as_dict()
                except Exception as e:
                    logger.exception(f"Markdown parsing failed for session {session.id}: {e}")
                    parsed_data = {"courses": [], "students": [], "institution": "", "warnings": [f"Markdown parsing error: {e}"]}
            else:
                parsed_data = {"courses": [], "students": [], "institution": "", "warnings": ["No file available."]}

        session.meta_info = {
            **session.meta_info,
            "pipeline_ready": True,
            "ingestion_source": "markdown_parser",
        }
        session.parsed_dataset = parsed_data
        session.status = 'PENDING_VERIFICATION' if parsed_data.get("students") else 'FAILED'
        session.save(update_fields=['status', 'meta_info', 'parsed_dataset'])

        if sheet:
            sheet.status = ResultSheet.ProcessingStatus.PENDING if parsed_data.get("students") else ResultSheet.ProcessingStatus.FAILED
            sheet.save(update_fields=['status'])

        return success_response(
            data=SessionDetailSerializer(session).data,
            message="Markdown parsing completed. Ready for result verification."
        )


class ClaudePromptView(APIView):
    """
    Returns the universal multi-page extraction prompt and links for top vision AI assistants
    (Google AI Studio Gemini Pro, Claude AI, ChatGPT).
    """
    def get(self, request):
        prompt_text = (
            "You are an expert academic tabulation and document extraction assistant.\n"
            "You are provided with one or more scanned/photographed academic result sheet image(s) from a university or college.\n\n"
            "Please perform comprehensive tabular data extraction across ALL provided pages and merge them into a single, complete Markdown document.\n\n"
            "### Extraction Instructions:\n"
            "1. Header Metadata: Extract the exact University/Institution Name, Faculty, Department, Degree/Program, Semester/Year, Session/Batch, and Total Semester Credits from the sheet header.\n"
            "2. Course Detection: Extract ALL courses present on the sheet, noting Course Code, Course Title, and Credit Hours.\n"
            "3. Multi-Page Merging: If multiple photos/pages are uploaded, extract EVERY single student across Page 1, Page 2, Page 3, etc., and merge all student rows sequentially sorted by Serial Number (S/N) or Student ID into ONE continuous table. Do NOT skip or truncate any student rows.\n\n"
            "Output strictly in clean Markdown format with the exact structure below:\n\n"
            "# Academic Result Sheet\n"
            "- **Institution**: [Extracted Institution Name, e.g. Jagannath University]\n"
            "- **Department**: [Extracted Department Name, e.g. Department of Computer Science & Engineering / EEE / BBA]\n"
            "- **Semester**: [Extracted Semester / Exam Name, e.g. B.Sc. 1st Year 2nd Semester Examination 2023]\n"
            "- **Session / Batch**: [Extracted Session / Batch, e.g. 2022-2023 / 15th Batch]\n"
            "- **Total Semester Credit**: [e.g. 21.50]\n\n"
            "### Course List:\n"
            "- [Course Code 1]: [Course Title 1] (Credit: [X.XX])\n"
            "- [Course Code 2]: [Course Title 2] (Credit: [X.XX])\n"
            "...\n\n"
            "| S/N | Student ID | Student Name | [CODE_1] GP | [CODE_1] LG | [CODE_2] GP | [CODE_2] LG | ... | Total GP | GPA | Cumulative Credits | CGPA | Result Status |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
            "| 1 | [Student ID 1] | [Student Name 1] | 4.00 | A+ | 3.75 | A | ... | 78.50 | 3.85 | 40.00 | 3.72 | P |\n"
            "| 2 | [Student ID 2] | [Student Name 2] | 3.50 | A- | 4.00 | A+ | ... | 72.00 | 3.55 | 40.00 | 3.48 | P |\n\n"
            "### Strict Output Constraints:\n"
            "- CRITICAL: Output ONLY the clean Markdown document starting directly with `# Academic Result Sheet`.\n"
            "- Do NOT write any conversational intro (e.g. 'Here is your extracted table...'), notes, apologies, or trailing comments.\n"
            "- Grade Points (GP): Normalize to 2 decimal places (e.g. 4.00, 3.75, 3.50, 3.25, 3.00, 2.75, 2.50, 2.25, 2.00, 0.00).\n"
            "- Letter Grades (LG): Exact grades (A+, A, A-, B+, B, B-, C+, C, D, F).\n"
            "- Student IDs: Keep original university student ID format without truncation.\n"
            "- Output pure raw Markdown so it can be parsed instantly by the analyzer."
        )
        return success_response(
            data={
                "prompt": prompt_text,
                "ai_tools": [
                    {
                        "name": "Google AI Studio",
                        "model": "Gemini 1.5 Pro / 2.0 Pro (Latest)",
                        "url": "https://aistudio.google.com",
                        "description": "Recommended for multi-page documents (supports 10+ high-res result sheets with 2M token window).",
                        "badge": "Best for Multi-Page",
                        "color": "amber",
                    },
                    {
                        "name": "Claude AI",
                        "model": "Claude 3.5 Sonnet / 3.7",
                        "url": "https://claude.ai",
                        "description": "Top precision optical recognition for fine academic tabulation details.",
                        "badge": "High Precision",
                        "color": "indigo",
                    },
                    {
                        "name": "ChatGPT",
                        "model": "GPT-4o Vision",
                        "url": "https://chatgpt.com",
                        "description": "Fast table parsing and multi-image extraction.",
                        "badge": "Fast",
                        "color": "emerald",
                    },
                ],
                "claude_url": "https://claude.ai",
                "google_ai_studio_url": "https://aistudio.google.com",
            },
            message="Universal AI extraction prompt retrieved successfully."
        )


class UploadMarkdownTextView(APIView):
    """
    Directly ingests raw Markdown text produced by Claude AI,
    parses it into structured dataset, and transitions to PENDING_VERIFICATION.
    """
    def post(self, request):
        import uuid
        from apps.sessions_manager.models import ResultSession
        from .parser.markdown_parser import MarkdownSheetParser

        markdown_text = request.data.get("markdown_text", "") or request.data.get("content", "")
        session_id = request.data.get("session_id")
        filename = request.data.get("filename", "claude_extracted.md")

        if not markdown_text or not markdown_text.strip():
            return error_response(
                message="markdown_text is required and cannot be empty.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if session_id:
            session = get_active_session_or_404(session_id)
        else:
            # Create a new session for this markdown dataset
            session = ResultSession.objects.create(
                original_filename=filename,
                file_size_bytes=len(markdown_text.encode('utf-8')),
                status='PROCESSING',
                meta_info={"ingestion_source": "claude_ai_markdown"},
            )

        parser = MarkdownSheetParser()
        parsed_sheet = parser.parse_markdown_content(markdown_text, filename=filename)
        parsed_dict = parsed_sheet.as_dict()

        session.parsed_dataset = parsed_dict
        session.status = 'PENDING_VERIFICATION'
        session.save(update_fields=['status', 'parsed_dataset', 'meta_info'])

        verification_payload = _build_verification_payload(session)

        return success_response(
            data={
                "session": SessionDetailSerializer(session).data,
                "verification": verification_payload,
            },
            message="Markdown dataset parsed successfully! Ready for verification."
        )


class DatasetVerificationView(APIView):
    """
    Returns extraction diagnostic counters, course column headers,
    and editable flattened rows for the verification interface.
    """
    def get(self, request, session_id):
        session = get_active_session_or_404(session_id)
        data = _build_verification_payload(session)
        return success_response(
            data=data,
            message="Verification data retrieved successfully."
        )


class UpdateVerificationCellView(APIView):
    """
    Applies an inline correction to a student result field and
    immediately re-validates the field and student consistency.
    """
    def patch(self, request, session_id):
        session = get_active_session_or_404(session_id)
        
        student_id = request.data.get("student_id")
        course_code = request.data.get("course_code")
        field_name = request.data.get("field_name")  # "grade_point" | "letter_grade" | "student_name" | "student_id" | "credit_hours"
        new_value = request.data.get("new_value")

        if not student_id or not field_name:
            return error_response(
                message="student_id and field_name are required.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        parsed = session.parsed_dataset or {}
        students = parsed.get("students", [])
        student = next((s for s in students if s.get("student_id") == student_id), None)

        if not student:
            return error_response(
                message=f"Student ID '{student_id}' not found in dataset.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Apply correction
        if field_name == "student_name":
            vf = FieldValidators.validate_student_name(new_value)
            student["student_name"] = vf.normalized_value or new_value
        elif field_name == "student_id":
            vf = FieldValidators.validate_student_id(new_value)
            student["student_id"] = vf.normalized_value or new_value
        elif course_code and field_name in ("grade_point", "letter_grade"):
            results = student.get("results", [])
            res = next((r for r in results if r.get("course_code") == course_code), None)
            if not res:
                res = {"course_code": course_code, "grade_point": None, "letter_grade": "", "status": "VALID", "review_reasons": []}
                results.append(res)
                student["results"] = results

            if field_name == "grade_point":
                vf_gp = FieldValidators.validate_grade_point(new_value)
                res["grade_point"] = float(vf_gp.normalized_value) if vf_gp.normalized_value is not None else None
            elif field_name == "letter_grade":
                vf_lg = FieldValidators.validate_letter_grade(new_value)
                res["letter_grade"] = vf_lg.normalized_value or new_value.upper()

            # Cross-validate GP and LG
            v_res = FieldValidators.validate_student_result(
                course_code_raw=course_code,
                gp_raw=str(res.get("grade_point") if res.get("grade_point") is not None else ""),
                lg_raw=res.get("letter_grade", ""),
            )
            res["status"] = v_res.status.value
            res["review_reasons"] = v_res.grade_point.warnings + v_res.letter_grade.warnings
            res["applied_corrections"] = v_res.grade_point.applied_corrections + v_res.letter_grade.applied_corrections

        # Re-save session
        session.parsed_dataset = parsed
        session.save(update_fields=['parsed_dataset'])

        updated_payload = _build_verification_payload(session)
        return success_response(
            data=updated_payload,
            message="Field updated and re-validated successfully."
        )


class ConfirmVerificationView(APIView):
    """
    Confirms 'Data looks correct'. Transitions session to VERIFIED/COMPLETED
    and computes final analytics and rankings.
    """
    def post(self, request, session_id):
        session = get_active_session_or_404(session_id)
        
        parsed = session.parsed_dataset or {}
        students = parsed.get("students", [])
        courses = parsed.get("courses", [])

        # Trigger downstream analytics & rankings
        ranking_service = RankingEngineService()
        analysis_service = AnalysisEngineService()

        session.analytics_data = analysis_service.calculate_cohort_statistics(
            students=students, courses=courses
        )

        session.status = 'VERIFIED'
        session.save(update_fields=['status', 'analytics_data'])

        from apps.dataset.models import ResultSheet
        sheet = ResultSheet.objects.filter(id=session.id).first()
        if sheet:
            sheet.status = ResultSheet.ProcessingStatus.COMPLETED
            sheet.save(update_fields=['status'])

        return success_response(
            data=SessionDetailSerializer(session).data,
            message="Dataset verified successfully! Analysis engine unlocked."
        )


class DatasetDetailView(APIView):
    """
    Returns full parsed tabular dataset for the session.
    """
    def get(self, request, session_id):
        session = get_active_session_or_404(session_id)
        return success_response(
            data=session.parsed_dataset,
            message="Dataset retrieved successfully."
        )


class StudentScorecardView(APIView):
    """
    Searches ONLY the specified dataset session for the given Student ID.
    Applies safe input normalization (stripping leading/trailing/stray spaces)
    and strictly avoids guessing IDs or exposing unrelated records.
    """
    def get(self, request, session_id, student_id):
        import re
        session = get_active_session_or_404(session_id)
        
        raw_query = str(student_id).strip()
        if not raw_query:
            return error_response(
                message="Student ID cannot be empty.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Normalize query: strip all internal/external whitespace and uppercase
        norm_query = re.sub(r"\s+", "", raw_query).upper()

        parsed = session.parsed_dataset or {}
        students = parsed.get("students", [])
        courses = parsed.get("courses", [])

        # Strict matching only within this dataset: match raw or normalized ID
        target_student = None
        for s in students:
            curr_id = str(s.get("student_id", "")).strip()
            curr_norm = re.sub(r"\s+", "", curr_id).upper()
            if curr_id == raw_query or curr_norm == norm_query:
                target_student = s
                break

        if not target_student:
            raise StudentNotFoundError("The Student ID was not found in this result sheet.")

        # Augment course results with course title & credits
        course_map = {c.get("course_code"): c for c in courses}
        course_grades = []
        for r in target_student.get("results", []):
            c_code = r.get("course_code", "")
            c_meta = course_map.get(c_code, {})
            course_grades.append({
                "course_code": c_code,
                "course_title": c_meta.get("course_title", c_code),
                "credits": float(c_meta.get("credit_hours", 3.0)),
                "grade_point": float(r.get("grade_point")) if r.get("grade_point") is not None else None,
                "letter_grade": r.get("letter_grade", ""),
                "status": r.get("status", "VALID"),
                "review_reasons": r.get("review_reasons", []),
            })

        # Summaries
        cur_sem = target_student.get("current_semester_summary") or {}
        cum_sem = target_student.get("cumulative_summary") or {}
        
        # Calculate deterministic rankings dynamically from all students in this dataset
        ranking_service = RankingEngineService()
        ranking_report = ranking_service.get_full_ranking_report(students, courses)
        sem_ranks = ranking_report.get("semester_rankings", {})
        cum_ranks = ranking_report.get("cumulative_rankings", {})

        target_raw_id = str(target_student.get("student_id", "")).strip()
        target_norm_id = re.sub(r"\s+", "", target_raw_id).upper()

        sem_info = sem_ranks.get(target_raw_id) or sem_ranks.get(target_norm_id)
        if not sem_info:
            for s_id, s_data in sem_ranks.items():
                if re.sub(r"\s+", "", str(s_id)).upper() == target_norm_id:
                    sem_info = s_data
                    break
        sem_info = sem_info or {}

        cum_info = cum_ranks.get(target_raw_id) or cum_ranks.get(target_norm_id)
        if not cum_info:
            for s_id, s_data in cum_ranks.items():
                if re.sub(r"\s+", "", str(s_id)).upper() == target_norm_id:
                    cum_info = s_data
                    break
        cum_info = cum_info or {}

        student_sem_rank = sem_info.get("rank")
        student_sem_percentile = sem_info.get("percentile")
        student_cum_rank = cum_info.get("rank")
        student_cum_percentile = cum_info.get("percentile")

        # Compute full individual analysis using deterministic analysis engine
        analysis_service = AnalysisEngineService()
        ind_analysis = analysis_service.calculate_individual_student(
            student=target_student,
            courses=courses,
            all_students=students,
        )

        scorecard_data = {
            "student_id": target_student.get("student_id"),
            "student_name": target_student.get("student_name", "UNKNOWN"),
            "serial_no": target_student.get("serial_no"),
            "status": target_student.get("status", "VALID"),
            "results": target_student.get("results", []),
            "course_grades": course_grades,
            "individual_analysis": ind_analysis,
            "semester_result": {
                "gpa": float(cur_sem.get("gpa") or 0.0) if cur_sem.get("gpa") is not None else 0.0,
                "credits_attempted": float(cur_sem.get("total_credit") or sum(cg["credits"] for cg in course_grades) or 0.0),
                "credits_earned": float(cur_sem.get("earned_credit") or cur_sem.get("total_credit") or sum(cg["credits"] for cg in course_grades) or 0.0),
                "semester_rank": student_sem_rank,
                "semester_percentile": student_sem_percentile,
                "result_status": cur_sem.get("result_status", "PASSED"),
                "remarks": cur_sem.get("remarks", ""),
            },
            "cumulative_result": {
                "cgpa": float(cum_sem.get("cgpa") or 0.0) if (cum_sem and cum_sem.get("cgpa") is not None) else 0.0,
                "total_credits_earned": float(cum_sem.get("earned_credit") or cum_sem.get("total_credit") or cur_sem.get("earned_credit") or 0.0) if cum_sem else 0.0,
                "cumulative_rank": student_cum_rank,
                "cumulative_percentile": student_cum_percentile,
                "result_status": cum_sem.get("result_status", "PASSED") if cum_sem else "PASSED",
                "remarks": cum_sem.get("remarks", "") if cum_sem else "",
            },
            "current_semester_summary": cur_sem,
            "cumulative_summary": cum_sem,
            "validation_status": {
                "is_arithmetic_valid": target_student.get("status") == "VALID",
                "calculated_gpa": float(cur_sem.get("gpa", 0.0)) if cur_sem.get("gpa") is not None else 0.0,
                "confidence_score": float(target_student.get("confidence", 1.0)),
            },
            "metadata": {
                "institution": parsed.get("institution", ""),
                "semester": parsed.get("semester", ""),
                "exam_session": parsed.get("exam_session", ""),
                "original_filename": session.original_filename,
            },
        }

        return success_response(
            data=scorecard_data,
            message=f"Scorecard for student {target_student.get('student_id')} retrieved."
        )


class CohortAnalyticsView(APIView):
    """
    Returns deterministic cohort statistics: Class Analysis (GPA Mean/Median/Mode),
    Cumulative Analysis (CGPA Mean/Median/Mode), and Subject Analysis (GP Mean/Median/Mode).
    """
    def get(self, request, session_id):
        session = get_active_session_or_404(session_id)
        
        parsed = session.parsed_dataset or {}
        students = parsed.get("students", [])
        courses = parsed.get("courses", [])

        analysis_service = AnalysisEngineService()
        stats = analysis_service.calculate_cohort_statistics(
            students=students,
            courses=courses,
            selected_student_id=request.query_params.get("student_id"),
        )

        return success_response(
            data=stats,
            message="Cohort analytics retrieved successfully."
        )


class StudentComparisonView(APIView):
    """
    Compares two students strictly within the same uploaded result sheet dataset.
    Computes subject-by-subject deltas, semester/cumulative differences, and win/loss tallies.
    """
    def get(self, request, session_id):
        import re
        session = get_active_session_or_404(session_id)
        
        serializer = CompareRequestSerializer(data=request.query_params)
        if not serializer.is_valid():
            return error_response(
                message="Invalid comparison parameters. Both student_a and student_b are required.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        raw_a = serializer.validated_data['student_a'].strip()
        raw_b = serializer.validated_data['student_b'].strip()

        norm_a = re.sub(r"\s+", "", raw_a).upper()
        norm_b = re.sub(r"\s+", "", raw_b).upper()

        parsed = session.parsed_dataset or {}
        students = parsed.get("students", [])
        courses = parsed.get("courses", [])

        # Match only within this dataset session
        student_a = None
        student_b = None
        for s in students:
            curr_id = str(s.get("student_id", "")).strip()
            curr_norm = re.sub(r"\s+", "", curr_id).upper()
            if curr_id == raw_a or curr_norm == norm_a:
                student_a = s
            if curr_id == raw_b or curr_norm == norm_b:
                student_b = s

        if not student_a or not student_b:
            missing = []
            if not student_a:
                missing.append(f"Student A '{raw_a}'")
            if not student_b:
                missing.append(f"Student B '{raw_b}'")
            raise StudentNotFoundError(f"{' and '.join(missing)} was not found in this result sheet.")

        ranking_service = RankingEngineService()
        ranking_data = ranking_service.get_full_ranking_report(students, courses)

        comparison_service = ComparisonEngineService()
        result = comparison_service.compare_students(
            student_a=student_a,
            student_b=student_b,
            courses=courses,
            cohort_data=session.analytics_data,
            ranking_data=ranking_data,
        )

        return success_response(
            data=result,
            message=f"Comparative analysis between student {raw_a} and {raw_b} completed successfully."
        )
