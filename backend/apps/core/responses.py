"""
Standardized API Response Helpers.
"""
from rest_framework.response import Response
from rest_framework import status

def success_response(data=None, message="Operation completed successfully.", status_code=status.HTTP_200_OK, meta=None):
    """
    Standard envelope for successful API responses.
    """
    payload = {
        "success": True,
        "message": message,
        "data": data if data is not None else {},
    }
    if meta is not None:
        payload["meta"] = meta
    return Response(payload, status=status_code)

def error_response(message="An error occurred.", errors=None, error_code="error", status_code=status.HTTP_400_BAD_REQUEST):
    """
    Standard envelope for error API responses.
    """
    payload = {
        "success": False,
        "message": message,
        "error_code": error_code,
        "errors": errors if errors is not None else [],
    }
    return Response(payload, status=status_code)
