import logging
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from apps.core.responses import success_response, error_response
from apps.sessions_manager.serializers import ResultSessionSerializer
from .serializers import FileUploadSerializer
from .services import handle_file_upload

logger = logging.getLogger(__name__)

class FileUploadView(APIView):
    """
    Accepts academic result sheet files (PDF, PNG, JPEG, JPG),
    validates format/size, allocates an ephemeral session, and prepares for processing.
    """
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="File upload validation failed.",
                errors=serializer.errors,
                error_code="invalid_upload_payload",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = serializer.validated_data['file']
        session = handle_file_upload(uploaded_file)
        
        session_data = ResultSessionSerializer(session).data
        return success_response(
            data=session_data,
            message="Result sheet uploaded successfully. Ready for processing.",
            status_code=status.HTTP_201_CREATED
        )
