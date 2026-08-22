"""
Custom exception hierarchy for Result Analyzer with friendly user-facing messages.
"""

from rest_framework.exceptions import APIException
from rest_framework import status


class ResultAnalyzerBaseException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "An error occurred during result processing."
    default_code = "processing_error"

    def __init__(self, detail=None, code=None, status_code=None):
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail=detail, code=code)


class FileValidationError(ResultAnalyzerBaseException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The uploaded file is invalid or unsupported. Please upload a valid PDF, PNG, or JPEG result sheet."
    default_code = "file_validation_error"


class CorruptedFileError(ResultAnalyzerBaseException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The uploaded file appears to be damaged or corrupted. Please re-export or upload a valid document."
    default_code = "corrupted_file_error"


class SessionNotFoundError(ResultAnalyzerBaseException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "The requested dataset session does not exist or has expired."
    default_code = "session_not_found"


class SessionExpiredError(ResultAnalyzerBaseException):
    status_code = status.HTTP_410_GONE
    default_detail = "This dataset session has expired and been cleaned up."
    default_code = "session_expired"


class StudentNotFoundError(ResultAnalyzerBaseException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "The Student ID was not found in this result sheet."
    default_code = "student_not_found"


class BlurryImageError(ResultAnalyzerBaseException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "The uploaded image is too blurry to extract text reliably. Please upload a clearer image."
    default_code = "blurry_image_error"


class TableDetectionError(ResultAnalyzerBaseException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Could not identify tabular boundaries or result grid in the document. Please ensure the full result sheet is visible, uncropped, and properly oriented."
    default_code = "table_detection_error"


class LowConfidenceOCRError(ResultAnalyzerBaseException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Some values could not be read confidently. Some extracted values require verification."
    default_code = "low_confidence_ocr"


class DuplicateStudentIdError(ResultAnalyzerBaseException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Duplicate Student IDs were detected in the result sheet. Please review and verify the records."
    default_code = "duplicate_student_id"


class InconsistentRowError(ResultAnalyzerBaseException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Some rows in the result sheet have missing subjects or mismatched columns. Verification is required before calculations."
    default_code = "inconsistent_row_error"


class ProcessingTimeoutError(ResultAnalyzerBaseException):
    status_code = status.HTTP_504_GATEWAY_TIMEOUT
    default_detail = "Document processing timed out. Please upload a single-page result sheet or optimized PDF."
    default_code = "processing_timeout"


class DocumentProcessingError(ResultAnalyzerBaseException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Failed to parse document structure or extract table. Please upload a clearer image."
    default_code = "document_processing_error"
