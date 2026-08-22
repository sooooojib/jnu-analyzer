import logging
from rest_framework.views import APIView
from rest_framework import status
from apps.core.responses import success_response, error_response
from apps.core.exceptions import SessionNotFoundError, SessionExpiredError
from .models import ResultSession
from .serializers import ResultSessionSerializer, SessionDetailSerializer

logger = logging.getLogger(__name__)

class SessionStatusView(APIView):
    """
    Retrieves status and metadata of an ephemeral analysis session.
    """
    def get(self, request, session_id):
        try:
            session = ResultSession.objects.get(id=session_id)
        except (ResultSession.DoesNotExist, ValueError):
            raise SessionNotFoundError()

        if session.is_expired:
            session.purge_file()
            session.delete()
            raise SessionExpiredError()

        serializer = ResultSessionSerializer(session)
        return success_response(
            data=serializer.data,
            message="Session status retrieved successfully."
        )

    def delete(self, request, session_id):
        """
        Explicitly terminates and purges a dataset session.
        """
        try:
            session = ResultSession.objects.get(id=session_id)
            session.purge_file()
            from apps.dataset.models import ResultSheet
            ResultSheet.objects.filter(id=session_id).delete()
            session.delete()
            return success_response(
                data={"session_id": str(session_id)},
                message="Session and ephemeral data successfully purged.",
                status_code=status.HTTP_200_OK
            )
        except (ResultSession.DoesNotExist, ValueError):
            return error_response(
                message="Session not found or already purged.",
                error_code="session_not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )
