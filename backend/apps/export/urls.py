from django.urls import path
from .views import (
    StudentPdfExportView,
    StudentExcelExportView,
    StudentExportDispatcherView,
    ClassPdfExportView,
    ComparisonPdfExportView,
)

app_name = 'export'

urlpatterns = [
    path('<uuid:session_id>/export/student/<str:student_id>/pdf/', StudentPdfExportView.as_view(), name='export_student_pdf'),
    path('<uuid:session_id>/export/student/<str:student_id>/excel/', StudentExcelExportView.as_view(), name='export_student_excel'),
    path('<uuid:session_id>/export/student/<str:student_id>/xlsx/', StudentExcelExportView.as_view(), name='export_student_xlsx'),
    path('<uuid:session_id>/export/student/<str:student_id>/', StudentExportDispatcherView.as_view(), name='export_student'),
    path('<uuid:session_id>/export/class/pdf/', ClassPdfExportView.as_view(), name='export_class_pdf'),
    path('<uuid:session_id>/export/class/', ClassPdfExportView.as_view(), name='export_class'),
    path('<uuid:session_id>/export/comparison/pdf/', ComparisonPdfExportView.as_view(), name='export_comparison_pdf'),
    path('<uuid:session_id>/export/comparison/', ComparisonPdfExportView.as_view(), name='export_comparison'),
]
