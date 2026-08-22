"""
Deterministic OCR error detection and correction engine.

Detects and corrects common OCR scanning artifacts:
  - Letter 'O' / 'o' vs digit '0' in numeric contexts
  - Letter 'I' / 'l' / '|' vs digit '1' in numeric contexts
  - Missing decimal points in standardized 2-decimal numbers (e.g. '400' -> '4.00')
  - Stray internal whitespace (e.g. '3 . 75' -> '3.75')
  - Duplicated characters from jitter (e.g. 'A++' -> 'A+')

Guiding Principle:
  - Apply deterministic corrections ONLY when evidence/confidence is high.
  - Never guess ambiguous values.
  - Transparently record all applied corrections for auditability.
"""

from __future__ import annotations

import logging
import re
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Precompiled regexes
RE_STRAY_SPACES_DECIMAL = re.compile(r"(\d)\s+[\.]\s*(\d)|(\d)\s*[\.]\s+(\d)")
RE_DUPLICATE_PLUS = re.compile(r"\+{2,}")
RE_DUPLICATE_DOTS = re.compile(r"\.{2,}")
RE_DUPLICATE_HYPHENS = re.compile(r"-{2,}")


class OCRCorrector:
    """
    Applies deterministic, rule-based OCR fixes to extracted text strings.
    """

    @classmethod
    def clean_student_id(
        cls,
        raw_text: str,
        confidence: float = 1.0,
        min_confidence: float = 0.60,
    ) -> Tuple[str, List[str], bool]:
        """
        Detects and corrects OCR substitutions in Student ID strings.
        e.g. '21O2O45' -> '2102045', '2I02045' -> '2102045'.

        Returns:
          (cleaned_text, applied_corrections, is_uncertain)
        """
        corrections: List[str] = []
        text = str(raw_text).strip()
        if not text:
            return "", [], False

        orig = text

        # 1. Remove internal spaces and hyphens if mostly digits
        clean_spaces = text.replace(" ", "")
        if clean_spaces != text:
            corrections.append("Removed internal whitespace from Student ID.")
            text = clean_spaces

        # 2. Check for 'O' or 'o' surrounded by or adjacent to digits
        if re.search(r"\d[Oo]|[Oo]\d|^[Oo]\d+|\d+[Oo]$", text) and confidence >= min_confidence:
            replaced = re.sub(r"[Oo]", "0", text)
            if replaced.isdigit():
                corrections.append("Corrected OCR letter 'O'/'o' to digit '0' in Student ID.")
                text = replaced

        # 3. Check for 'I' or 'l' or '|' in otherwise all-digit ID
        if re.search(r"\d[Il|]|[Il|]\d", text) and confidence >= min_confidence:
            replaced = re.sub(r"[Il|]", "1", text)
            if replaced.isdigit():
                corrections.append("Corrected OCR character 'I'/'l'/'|' to digit '1' in Student ID.")
                text = replaced

        is_uncertain = (len(text) < 5 or not text.isalnum())
        return text, corrections, is_uncertain

    @classmethod
    def clean_grade_point(
        cls,
        raw_text: str,
        confidence: float = 1.0,
        min_confidence: float = 0.60,
    ) -> Tuple[str, List[str], bool]:
        """
        Corrects OCR errors in Grade Point strings (0.00–4.00).
        e.g. '4.OO' -> '4.00', '3 . 75' -> '3.75', '400' -> '4.00'.
        """
        corrections: List[str] = []
        text = str(raw_text).strip()
        if not text:
            return "", [], False

        # 1. Fix stray whitespace around decimal points: "3 . 75" -> "3.75"
        if RE_STRAY_SPACES_DECIMAL.search(text):
            text = re.sub(r"(\d)\s*\.\s*(\d)", r"\1.\2", text)
            corrections.append("Removed stray spaces around decimal point.")

        # 2. Fix 'O'/'o' in decimal: "4.OO" -> "4.00", "3.8O" -> "3.80"
        if re.search(r"\d\.[Oo0-9]{1,2}", text) and ("O" in text or "o" in text) and confidence >= min_confidence:
            text = text.replace("O", "0").replace("o", "0")
            corrections.append("Corrected OCR letter 'O'/'o' to digit '0' in Grade Point.")

        # 3. Fix missing decimal point in known 3-digit GP patterns: "400" -> "4.00", "375" -> "3.75", "350" -> "3.50"
        clean_digits = re.sub(r"[^\d]", "", text)
        if len(clean_digits) == 3 and "." not in text and confidence >= min_confidence:
            first_digit = int(clean_digits[0])
            two_decimals = int(clean_digits[1:])
            # If it starts with 0..4 and two decimals are valid increments (00, 25, 50, 75, etc.)
            if first_digit <= 4 and two_decimals in (0, 25, 50, 75, 80, 85, 90):
                text = f"{first_digit}.{clean_digits[1:]}"
                corrections.append(f"Inserted missing decimal point ('{clean_digits}' -> '{text}').")

        # 4. Fix duplicate dots: "3..75" -> "3.75"
        if ".." in text:
            text = RE_DUPLICATE_DOTS.sub(".", text)
            corrections.append("Removed duplicate decimal points.")

        # Validation check
        is_uncertain = False
        try:
            val = float(text)
            if val < 0.0 or val > 4.0:
                is_uncertain = True
        except ValueError:
            is_uncertain = True

        return text, corrections, is_uncertain

    @classmethod
    def clean_letter_grade(
        cls,
        raw_text: str,
        confidence: float = 1.0,
    ) -> Tuple[str, List[str], bool]:
        """
        Corrects letter grade OCR artifacts.
        e.g. 'A++' -> 'A+', 'a -' -> 'A-', 'A +' -> 'A+'.
        """
        corrections: List[str] = []
        text = str(raw_text).strip()
        if not text:
            return "", [], False

        # Remove internal spaces: "A +" -> "A+", "B -" -> "B-"
        no_spaces = text.replace(" ", "").upper()
        if no_spaces != text:
            corrections.append("Removed whitespace from letter grade.")
            text = no_spaces

        # Fix duplicate plus/minus: "A++" -> "A+"
        if "++" in text:
            text = RE_DUPLICATE_PLUS.sub("+", text)
            corrections.append("Normalized duplicated '+' in letter grade.")

        valid_set = {"A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F", "I", "W", "UW", "NA", "P", "S", "U"}
        is_uncertain = text not in valid_set

        return text, corrections, is_uncertain

    @classmethod
    def clean_course_code(
        cls,
        raw_text: str,
        confidence: float = 1.0,
    ) -> Tuple[str, List[str], bool]:
        """
        Standardizes course codes and fixes stray spaces / OCR hyphens.
        e.g. 'CSE - 2201' -> 'CSE-2201', 'CSE--2201' -> 'CSE-2201'.
        """
        corrections: List[str] = []
        text = str(raw_text).strip().upper()
        if not text:
            return "", [], False

        # Remove extra duplicate hyphens
        if "--" in text:
            text = RE_DUPLICATE_HYPHENS.sub("-", text)
            corrections.append("Normalized duplicate hyphens in course code.")

        # Standardize spacing around hyphen: "CSE - 2201" -> "CSE-2201"
        cleaned_hyphen = re.sub(r"\s*-\s*", "-", text)
        if cleaned_hyphen != text:
            corrections.append("Normalized hyphen spacing in course code.")
            text = cleaned_hyphen

        # If space separated: "CSE 2201" -> "CSE-2201"
        if " " in text and "-" not in text:
            text = text.replace(" ", "-")
            corrections.append("Standardized course code separator to hyphen.")

        # Check for 'O' in number portion: e.g. "CSE-22O1" -> "CSE-2201"
        match = re.match(r"^([A-Z]{2,5})-([A-Z0-9]+)$", text)
        if match:
            dept, num = match.groups()
            if "O" in num and any(c.isdigit() for c in num):
                fixed_num = num.replace("O", "0")
                text = f"{dept}-{fixed_num}"
                corrections.append("Corrected OCR letter 'O' to digit '0' in course number.")

        is_uncertain = not bool(re.match(r"^[A-Z]{2,5}-\d{3,4}[A-Z]?$", text))
        return text, corrections, is_uncertain

    @classmethod
    def clean_credit_hours(
        cls,
        raw_text: str,
        confidence: float = 1.0,
    ) -> Tuple[str, List[str], bool]:
        """
        Cleans credit hours strings (e.g. '3.OO' -> '3.00', '150' -> '1.50').
        """
        corrections: List[str] = []
        text = str(raw_text).strip()
        if not text:
            return "", [], False

        # Fix 'O' to '0'
        if "O" in text or "o" in text:
            text = text.replace("O", "0").replace("o", "0")
            corrections.append("Corrected OCR letter 'O'/'o' to digit '0' in credit hours.")

        # Fix missing decimal: "300" -> "3.00", "150" -> "1.50", "075" -> "0.75"
        clean_digits = re.sub(r"[^\d]", "", text)
        if len(clean_digits) == 3 and "." not in text:
            val_int = int(clean_digits)
            if val_int in (75, 100, 150, 200, 300, 400, 500, 600):
                text = f"{int(clean_digits[0])}.{clean_digits[1:]}"
                corrections.append(f"Inserted missing decimal point in credit hours ('{clean_digits}' -> '{text}').")

        is_uncertain = False
        try:
            val = float(text)
            if val < 0.0 or val > 20.0:
                is_uncertain = True
        except ValueError:
            is_uncertain = True

        return text, corrections, is_uncertain
