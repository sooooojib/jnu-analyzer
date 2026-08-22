"""
Export API Views for Student, Class, and Comparison Analysis Reports.
"""

from __future__ import annotations

import logging
import re
from django.http import HttpResponse
from rest_framework.exceptions import ValidationError
from rest_framework.renderers import BaseRenderer
from rest_framework.views import APIView
from apps.processing.views import get_active_session_or_404
from .data_builders import (
    build_class_report_data,
    build_comparison_report_data,
    build_student_report_data,
)
from .services.class_pdf_exporter import build_class_pdf
from .services.comparison_pdf_exporter import build_comparison_pdf
from .services.student_excel_exporter import build_student_excel
from .services.student_pdf_exporter import build_student_pdf

logger = logging.getLogger(__name__)


class PassthroughBinaryRenderer(BaseRenderer):
    """
    Passthrough renderer that supports streaming binary streams
    (PDF, Excel XLSX, CSV) without DRF content-negotiation interference.
    """
    media_type = '*/*'
    format = 'binary'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class BaseExportAPIView(APIView):
    """Base API view for binary exports bypassing DRF format suffix negotiation."""
    renderer_classes = [PassthroughBinaryRenderer]

    def perform_content_negotiation(self, request, force=False):
        return PassthroughBinaryRenderer(), '*/*'


class StudentPdfExportView(BaseExportAPIView):
    """
    Generates and downloads a dedicated Student Academic Analysis PDF.
    Strictly scoped to the requested student within the specified session dataset.
    """

    def get(self, request, session_id, student_id):
        session = get_active_session_or_404(session_id)
        report_data = build_student_report_data(session=session, student_id=student_id)
        pdf_bytes = build_student_pdf(report_data)

        raw_id = str(report_data.get("student_info", {}).get("student_id", student_id)).strip()
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", raw_id) or "student"
        filename = f"JNU_Student_Analysis_{safe_id}.pdf"

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Content-Length"] = len(pdf_bytes)
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response


class StudentExcelExportView(BaseExportAPIView):
    """
    Generates and downloads a multi-tab Student Academic Analysis Excel (.xlsx) workbook.
    Contains: Student Summary, Subject Results, and Student Statistics sheets.
    """

    def get(self, request, session_id, student_id):
        session = get_active_session_or_404(session_id)
        report_data = build_student_report_data(session=session, student_id=student_id)
        xlsx_bytes = build_student_excel(report_data)

        raw_id = str(report_data.get("student_info", {}).get("student_id", student_id)).strip()
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", raw_id) or "student"
        filename = f"JNU_Student_Analysis_{safe_id}.xlsx"

        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        response = HttpResponse(xlsx_bytes, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Content-Length"] = len(xlsx_bytes)
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response


class StudentExportDispatcherView(BaseExportAPIView):
    """
    Dispatches to PDF or Excel based on ?format=xlsx|pdf (defaults to PDF).
    """

    def get(self, request, session_id, student_id):
        fmt = (request.query_params.get("format") or request.GET.get("format") or "pdf").lower().strip()
        session = get_active_session_or_404(session_id)
        report_data = build_student_report_data(session=session, student_id=student_id)

        raw_id = str(report_data.get("student_info", {}).get("student_id", student_id)).strip()
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", raw_id) or "student"

        if fmt in ("xlsx", "excel"):
            xlsx_bytes = build_student_excel(report_data)
            filename = f"JNU_Student_Analysis_{safe_id}.xlsx"
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            response = HttpResponse(xlsx_bytes, content_type=content_type)
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            response["Content-Length"] = len(xlsx_bytes)
            response["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response

        pdf_bytes = build_student_pdf(report_data)
        filename = f"JNU_Student_Analysis_{safe_id}.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Content-Length"] = len(pdf_bytes)
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response


class ClassPdfExportView(BaseExportAPIView):
    """
    Generates and downloads a dedicated Class Cohort Analysis PDF.
    Strictly scoped to whole-class metrics, UGC letter grade distribution,
    merit leaderboard, and subject analyses.
    """

    def get(self, request, session_id):
        session = get_active_session_or_404(session_id)
        report_data = build_class_report_data(session=session)
        pdf_bytes = build_class_pdf(report_data)

        filename = "JNU_Class_Analysis.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Content-Length"] = len(pdf_bytes)
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response


class ComparisonPdfExportView(BaseExportAPIView):
    """
    Generates and downloads a dedicated Student Comparison PDF.
    Strictly scoped to Student A vs Student B head-to-head metrics,
    profile comparison, subject outcomes, and course breakdown.
    """

    def get(self, request, session_id):
        student_a = (request.query_params.get("student_a") or request.GET.get("student_a") or "").strip()
        student_b = (request.query_params.get("student_b") or request.GET.get("student_b") or "").strip()

        if not student_a or not student_b:
            raise ValidationError("Both 'student_a' and 'student_b' query parameters are required.")

        session = get_active_session_or_404(session_id)
        report_data = build_comparison_report_data(
            session=session,
            student_a_id=student_a,
            student_b_id=student_b,
        )
        pdf_bytes = build_comparison_pdf(report_data)

        safe_a = re.sub(r"[^a-zA-Z0-9_-]", "_", student_a) or "studentA"
        safe_b = re.sub(r"[^a-zA-Z0-9_-]", "_", student_b) or "studentB"
        filename = f"JNU_Comparison_{safe_a}_vs_{safe_b}.pdf"

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Content-Length"] = len(pdf_bytes)
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response
