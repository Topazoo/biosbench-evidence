"""Offline evidence checks. No collector, hardware access, or write authority."""

from .browser import BrowserBuffer, BrowserPlan, verify_browser
from .hii import inspect_hii

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
    "BrowserBuffer", "BrowserPlan", "verify_browser", "inspect_hii",
]
