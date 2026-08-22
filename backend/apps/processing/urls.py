from django.urls import path
from .views import (
    ProcessDatasetView,
    DatasetDetailView,
    DatasetVerificationView,
    UpdateVerificationCellView,
    ConfirmVerificationView,
    StudentScorecardView,
    CohortAnalyticsView,
    StudentComparisonView,
    ClaudePromptView,
    UploadMarkdownTextView,
)

app_name = 'processing'

urlpatterns = [
    path('claude-prompt/', ClaudePromptView.as_view(), name='claude_prompt'),
    path('upload-markdown/', UploadMarkdownTextView.as_view(), name='upload_markdown'),
    path('<uuid:session_id>/process/', ProcessDatasetView.as_view(), name='process_dataset'),
    path('<uuid:session_id>/verification/', DatasetVerificationView.as_view(), name='dataset_verification'),
    path('<uuid:session_id>/verification/update-cell/', UpdateVerificationCellView.as_view(), name='update_verification_cell'),
    path('<uuid:session_id>/verification/confirm/', ConfirmVerificationView.as_view(), name='confirm_verification'),
    path('<uuid:session_id>/dataset/', DatasetDetailView.as_view(), name='dataset_detail'),
    path('<uuid:session_id>/students/<str:student_id>/', StudentScorecardView.as_view(), name='student_scorecard'),
    path('<uuid:session_id>/analytics/', CohortAnalyticsView.as_view(), name='cohort_analytics'),
    path('<uuid:session_id>/compare/', StudentComparisonView.as_view(), name='student_comparison'),
]
