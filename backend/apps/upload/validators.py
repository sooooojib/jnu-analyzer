"""
File upload validation strictly enforcing Markdown (.md) documents and valid UTF-8 encoding.
"""
from django.conf import settings
from apps.core.exceptions import FileValidationError

SUPPORTED_MIME_TYPES = {
    'text/markdown': 'md',
    'text/plain': 'md',
    'text/x-markdown': 'md',
}

# Binary magic signatures that must be explicitly rejected
REJECTED_BINARY_SIGNATURES = {
    b'%PDF-': 'PDF document',
    b'\x89PNG\r\n\x1a\n': 'PNG image',
    b'\xff\xd8\xff': 'JPEG image',
    b'GIF87a': 'GIF image',
    b'GIF89a': 'GIF image',
}

def validate_uploaded_file(file_obj):
    """
    Validates uploaded file size, enforces Markdown (.md) extension, and verifies UTF-8 text encoding.
    Returns detected normalized extension ('md').
    """
    if not file_obj:
        raise FileValidationError("No file was uploaded.")

    # 1. Size Validation
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE_BYTES', 25 * 1024 * 1024)
    if file_obj.size > max_size:
        max_mb = getattr(settings, 'MAX_UPLOAD_SIZE_MB', 25)
        raise FileValidationError(f"File size exceeds maximum permitted limit of {max_mb}MB.")

    if file_obj.size == 0:
        raise FileValidationError("Uploaded file is empty (0 bytes).")

    # 2. Inspect Header Bytes to reject binary formats
    initial_pos = file_obj.tell() if hasattr(file_obj, 'tell') else 0
    file_obj.seek(0)
    header_bytes = file_obj.read(64)
    file_obj.seek(initial_pos)

    for signature, type_name in REJECTED_BINARY_SIGNATURES.items():
        if header_bytes.startswith(signature):
            raise FileValidationError(
                f"Binary {type_name} detected. The system exclusively accepts AI-extracted Markdown (.md) files. Please upload a .md file."
            )

    name = getattr(file_obj, 'name', '') or ''
    ext = name.lower().rsplit('.', 1)[-1] if '.' in name else ''

    if ext not in ('md', 'markdown', 'txt'):
        raise FileValidationError(
            f"Unsupported file format '.{ext}'. Please upload an AI-extracted Markdown (.md) result sheet file."
        )

    # 3. Validate UTF-8 decoding
    try:
        header_bytes.decode('utf-8')
    except UnicodeDecodeError:
        raise FileValidationError("Markdown file contains invalid non-UTF-8 characters. Please ensure the file is plain text UTF-8.")

    return 'md'
