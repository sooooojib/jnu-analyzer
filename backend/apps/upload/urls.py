from django.urls import path
from .views import FileUploadView

app_name = 'upload'

urlpatterns = [
    path('', FileUploadView.as_view(), name='file_upload'),
]
