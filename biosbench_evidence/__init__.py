"""Offline evidence checks. No collector, hardware access, or write authority."""

from .core import (
    EvidenceError,
    Snapshot,
    compare_set,
    compare_snapshots,
    parse_report,
    parse_snapshot,
    validate_bundle,
)

__all__ = [
    "EvidenceError", "Snapshot", "compare_set", "compare_snapshots",
    "parse_report", "parse_snapshot", "validate_bundle",
]
