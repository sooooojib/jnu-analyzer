from django.urls import path
from .views import SessionStatusView

app_name = 'sessions_manager'

urlpatterns = [
    path('<uuid:session_id>/status/', SessionStatusView.as_view(), name='session_status'),
    path('<uuid:session_id>/', SessionStatusView.as_view(), name='session_delete'),
]
