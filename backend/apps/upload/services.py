import os
import re
import uuid
import logging
from pathlib import Path
from django.conf import settings
from django.db import transaction
from apps.sessions_manager.models import ResultSession
from apps.dataset.models import ResultSheet
from apps.processing.parser.markdown_parser import MarkdownSheetParser
from .validators import validate_uploaded_file

logger = logging.getLogger(__name__)

def handle_file_upload(file_obj) -> ResultSession:
    """
    Validates the uploaded Markdown file, saves it to the ephemeral upload directory,
    parses it into structured academic records using MarkdownSheetParser, and
    initializes the ResultSession and ResultSheet in PENDING_VERIFICATION status.
    """
    detected_type = validate_uploaded_file(file_obj)
    
    session_id = uuid.uuid4()
    from django.conf import settings as _s
    upload_dir = Path(getattr(_s, 'UPLOAD_DIR', Path(__file__).resolve().parent.parent.parent / 'uploads'))
    session_dir = upload_dir / str(session_id)
    session_dir.mkdir(parents=True, exist_ok=True)
    
    clean_filename = f"source.{detected_type}"
    file_path = session_dir / clean_filename

    # Save to disk
    file_content_bytes = b""
    with open(file_path, 'wb+') as destination:
        for chunk in file_obj.chunks():
            destination.write(chunk)
            file_content_bytes += chunk

    raw_name = getattr(file_obj, 'name', 'result_sheet.md')
    safe_name = os.path.basename(raw_name)
    safe_name = re.sub(r'[^a-zA-Z0-9._ -]', '_', safe_name)
    if not safe_name:
        safe_name = f"sheet.{detected_type}"

    # Deterministically parse Markdown content
    try:
        md_text = file_content_bytes.decode('utf-8', errors='replace')
        parser = MarkdownSheetParser()
        parsed_sheet = parser.parse_markdown_content(md_text, filename=safe_name)
        parsed_dataset = parsed_sheet.as_dict()
    except Exception as e:
        logger.exception(f"Markdown parsing failed during upload for {safe_name}: {e}")
        parsed_dataset = {
            "institution": "University",
            "program": "Department",
            "semester": "Examination Results",
            "courses": [],
            "students": [],
            "warnings": [f"Parsing error: {e}"],
        }

    with transaction.atomic():
        session = ResultSession.objects.create(
            id=session_id,
            original_filename=safe_name,
            file_path=str(file_path),
            file_type=detected_type,
            file_size_bytes=file_obj.size,
            status='PENDING_VERIFICATION' if parsed_dataset.get("students") else 'FAILED',
            parsed_dataset=parsed_dataset,
            meta_info={
                "original_name": safe_name,
                "detected_type": detected_type,
                "ingestion_source": "markdown_upload",
                "total_students": len(parsed_dataset.get("students", [])),
                "total_courses": len(parsed_dataset.get("courses", [])),
            }
        )

        # Also create structured ResultSheet in dataset app
        ResultSheet.objects.create(
            id=session_id,
            session=session,
            original_filename=safe_name,
            file_type=detected_type,
            file_size_bytes=file_obj.size,
            status=ResultSheet.ProcessingStatus.PENDING if parsed_dataset.get("students") else ResultSheet.ProcessingStatus.FAILED,
        )

    logger.info(
        f"Initialized ResultSession {session.id} from Markdown file '{safe_name}' "
        f"({len(parsed_dataset.get('students', []))} students, {len(parsed_dataset.get('courses', []))} courses)"
    )
    return session
