"""Shared helpers for name normalization and case-insensitive matching.

Matching policy:
- Names are trimmed of leading/trailing whitespace.
- Empty names after trim are rejected.
- Duplicate matching is case-insensitive (DB unique constraints remain case-sensitive
  for SQLite; application layer enforces case-insensitive uniqueness).
- Original capitalization of the first-seen / updated value is preserved.
"""

from __future__ import annotations


def normalize_name(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip()


def names_equal(a: str, b: str) -> bool:
    return normalize_name(a).casefold() == normalize_name(b).casefold()
