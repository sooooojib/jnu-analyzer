"""
Abstract interface for result sheet parsers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .schema import ParsedSheet
from .template import ResultSheetTemplate


class BaseSheetParser(ABC):
    """
    Abstract interface for academic result-sheet semantic parsing.
    """

    @abstractmethod
    def parse_markdown(
        self,
        markdown_text: str,
        filename: str = "result_sheet.md",
    ) -> ParsedSheet:
        """
        Parse Markdown text directly into normalized ParsedSheet.
        """
        pass
