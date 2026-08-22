"""
SheetParserService — Concrete result sheet semantic parsing service.
Parses Markdown text and structured tables into normalized data models.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import BaseSheetParser
from .schema import ParsedSheet
from .markdown_parser import MarkdownSheetParser
from .template import ResultSheetTemplate, get_default_template

logger = logging.getLogger(__name__)


class SheetParserService(BaseSheetParser):
    """
    High-level academic result sheet parser service using deterministic Markdown parsing.
    """

    def __init__(self, default_template: Optional[ResultSheetTemplate] = None):
        self.default_template = default_template or get_default_template()
        self._parser = MarkdownSheetParser(template=self.default_template)

    def parse_markdown(self, markdown_text: str, filename: str = "result_sheet.md") -> ParsedSheet:
        """
        Parse Markdown text directly into normalized ParsedSheet.
        """
        return self._parser.parse_markdown_content(markdown_text, filename=filename)
