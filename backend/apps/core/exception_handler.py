"""
Custom DRF exception handler enforcing user-friendly JSON error envelopes
and structured server logging without exposing raw stack traces or private student data.
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from .exceptions import ResultAnalyzerBaseException

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Returns sanitized, user-friendly JSON structure for all exceptions.
    Never exposes raw internal tracebacks to the client.
    """
    # Call REST framework's default exception handler first to get standard response
    response = exception_handler(exc, context)

    if isinstance(exc, ResultAnalyzerBaseException):
        # Structured server log without sensitive student details
        logger.warning(
            f"Business logic event: code={getattr(exc, 'default_code', 'error')} status={exc.status_code} detail={exc.detail}"
        )
        return Response(
            {
                "success": False,
                "message": str(exc.detail),
                "error_code": getattr(exc, 'default_code', 'processing_error'),
                "errors": [str(exc.detail)],
            },
            status=exc.status_code,
        )

    if response is not None:
        # Standard DRF validation error / auth error
        errors = []
        if isinstance(response.data, dict):
            for field, messages in response.data.items():
                if isinstance(messages, list):
                    for msg in messages:
                        errors.append(f"{field}: {msg}")
                else:
                    errors.append(f"{field}: {messages}")
        elif isinstance(response.data, list):
            errors = [str(e) for e in response.data]
        else:
            errors = [str(response.data)]

        return Response(
            {
                "success": False,
                "message": "Input validation error. Please check your request parameters.",
                "error_code": "validation_error",
                "errors": errors,
            },
            status=response.status_code,
        )

    # Unhandled 500 server error — Structured server logging with trace, but clean client response
    view_name = context.get('view').__class__.__name__ if context and context.get('view') else 'UnknownView'
    logger.exception(f"Unhandled server error in {view_name}: {exc}", exc_info=exc)

    return Response(
        {
            "success": False,
            "message": "A server error occurred while processing your request. Please try again or upload a clearer image.",
            "error_code": "internal_server_error",
            "errors": ["Processing could not be completed. Please ensure your result sheet is clearly readable and properly oriented."],
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
