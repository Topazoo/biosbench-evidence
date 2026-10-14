"""Bounded saved-file parsing and exact comparisons, using only the stdlib."""

from dataclasses import dataclass
import hashlib
import re
from typing import Mapping, Sequence

MAX_REPORT = 32_768
MAX_FIELDS = 1_024
MAX_SNAPSHOT = 140_000
MAX_DATA = 65_536
COMPANIONS = {
    "flash_survey": ("BFLA", 32_768),
    "boot_inventory_memory": ("BMAP", 5 * 1024 * 1024),
    "boot_inventory_images": ("BIMG", 5 * 1024 * 1024),
}


class EvidenceError(ValueError):
    """A machine-readable category plus a non-sensitive explanation."""

    def __init__(self, category: str, detail: str):
        self.category = category
        super().__init__(detail)


def _require(ok: bool, detail: str, category: str = "invalid") -> None:
    if not ok:
        raise EvidenceError(category, detail)


def _ascii(data: bytes, limit: int) -> str:
    _require(0 < len(data) <= limit, "Empty or oversized input")
    _require(all(b == 10 or 32 <= b <= 126 for b in data), "Expected ASCII and LF")
    return data.decode("ascii")


def parse_report(data: bytes) -> dict[str, str]:
    """Validate the generic envelope; unknown fields remain opaque claims.

    This is not the board-specific engineering parser. Hash declarations and
    safety flags are checked. Supported inventory structure is checked separately;
    board-specific semantics are not decoded.
    """
    text = _ascii(data, MAX_REPORT)
    header, separator, body = text.partition("\n")
    _require(bool(separator), "Missing header separator")
    _require(header == "BiosBench | Rust diagnostics v1", "Unknown report header")
    fields: dict[str, str] = {}
    for line in body.splitlines():
        if not line:
            continue
        key, separator, value = line.partition("=")
        _require(bool(separator) and bool(re.fullmatch(r"[A-Za-z0-9_.\[\]-]{1,64}", key)),
                 "Invalid field key")
        _require(len(value) <= 2048, "Field value too long")
        _require(key not in fields, "Duplicate field")
        fields[key] = value
        _require(len(fields) <= MAX_FIELDS, "Too many fields")
    for key in ("board_verified", "profile_applied", "firmware_flashed"):
        _require(key in fields, "Missing required safety flag", "incomplete")
        _require(fields[key] == "false", "Unexpected safety claim")
    for kind, (prefix, _) in COMPANIONS.items():
        members = {key[len(kind) + 1:] for key in fields if key.startswith(kind + "_")}
        if not members:
            continue
        _require(members <= {"status", "bundle_file", "sha256"}, "Unknown companion field")
        status = fields.get(kind + "_status", "")
        _require(bool(re.fullmatch(r"[A-Z][A-Z0-9_]*", status)), "Invalid companion status")
        if status == "SAVED":
            _require(members == {"status", "bundle_file", "sha256"},
                     "Incomplete saved reference", "incomplete")
            name = fields[kind + "_bundle_file"]
            _require(bool(re.fullmatch(prefix + r"[0-9]{3}\.TXT", name))
                     and name[4:7] != "000", "Invalid companion basename")
            _require(bool(re.fullmatch(r"[0-9a-f]{64}", fields[kind + "_sha256"])),
                     "Invalid SHA-256 declaration")
        else:
            _require(members == {"status"}, "Unsaved companion has a file or digest")
    return fields


def validate_bundle(report: bytes, selected: Mapping[str, bytes]) -> dict:
    """Validate explicit basename-to-bytes selections without opening paths.

    Byte identity is independent of payload semantics and save completion.
    Missing declared companions produce an incomplete result, not unchanged.
    """
    fields = parse_report(report)
    _require(len(selected) <= 3, "Too many companions")
    declared = {
        fields[kind + "_bundle_file"]: kind
        for kind in COMPANIONS if fields.get(kind + "_status") == "SAVED"
    }
    _require(set(selected) <= set(declared), "Unexpected companion selection")
    rows = []
    for kind, (_, limit) in COMPANIONS.items():
        status = fields.get(kind + "_status", "UNREPORTED")
        row = {"kind": kind, "reported_status": status, "bytes": "unavailable",
               "semantics": "not_checked"}
        if status == "SAVED":
            name = fields[kind + "_bundle_file"]
            if name not in selected:
                row["bytes"] = "missing"
            else:
                data = selected[name]
                _require(0 < len(data) <= limit, "Empty or oversized companion")
                actual = hashlib.sha256(data).hexdigest()
                _require(actual == fields[kind + "_sha256"], "Companion digest mismatch")
                row["bytes"] = "matched"
                if kind.startswith("boot_inventory_"):
                    from .inventory import parse_inventory
                    inventory_kind = "memory_map" if kind.endswith("memory") else "loaded_images"
                    try:
                        row["summary"] = parse_inventory(data, inventory_kind)
                        row["structure"] = "validated"
                    except EvidenceError:
                        row["structure"] = "invalid"
                else:
                    row["structure"] = "unsupported"
        rows.append(row)
    return {
        "state": ("invalid" if any(r.get("structure") == "invalid" for r in rows)
                  else "complete" if all(r["bytes"] == "matched" for r in rows) else "incomplete"),
        "declared_links": ("none_declared" if not declared else "matched"
                           if all(name in selected for name in declared) else "missing"),
        "saved_references": len(declared),
        "verified_companions": sum(r["bytes"] == "matched" for r in rows),
        "report_sha256": hashlib.sha256(report).hexdigest(),
        "companions": rows,
        "save_completion": "unverified",
        "authenticity": "unverified",
    }


@dataclass(frozen=True)
class Snapshot:
    """Exact identity bytes, UTF-16LE name bytes, attributes, and stored bytes."""

    guid: bytes
    name: bytes
    attributes: int
    data: bytes

    def validate(self) -> None:
        _require(len(self.guid) == 16, "GUID must contain 16 bytes")
        _require(0 < len(self.name) <= 512 and len(self.name) % 2 == 0, "Invalid name size")
        try:
            name = self.name.decode("utf-16le", errors="strict")
        except UnicodeDecodeError as error:
            raise EvidenceError("invalid", "Invalid UTF-16 name") from error
        _require("\0" not in name, "Name must not contain a terminator")
        _require(0 <= self.attributes <= 0xFFFFFFFF, "Attributes outside u32")
        _require(0 < len(self.data) <= MAX_DATA, "Invalid snapshot data size")


def parse_snapshot(data: bytes) -> Snapshot:
    """Decode the original five-line supplied-snapshot v1 format."""
    lines = _ascii(data, MAX_SNAPSHOT).splitlines()
    _require(len(lines) == 5 and lines[0] == "BiosBench supplied snapshot v1",
             "Invalid snapshot shape or version")
    values = []
    for line, prefix in zip(lines[1:], ("guid_bytes=", "name_utf16le=", "attributes_le=", "data=")):
        _require(line.startswith(prefix), "Unexpected snapshot field")
        value = line[len(prefix):]
        _require(len(value) % 2 == 0 and bool(re.fullmatch(r"[0-9A-Fa-f]*", value)), "Invalid hex")
        values.append(bytes.fromhex(value))
    guid, name, attrs, body = values
    _require(len(attrs) == 4, "Attributes must contain four bytes")
    result = Snapshot(guid, name, int.from_bytes(attrs, "little"), body)
    result.validate()
    return result


def compare_snapshots(before: Snapshot, after: Snapshot,
                      edits: Sequence[tuple[int, int, int]] = ()) -> str:
    """Match every byte against sorted (offset, old, new) edits.

    An empty plan asserts unchanged bytes. A nonempty plan may contain no-ops.
    Return unchanged or matched; missing/invalid evidence never returns either.
    """
    before.validate()
    after.validate()
    _require((before.guid, before.name) == (after.guid, after.name), "Identity mismatch", "mismatch")
    _require(before.attributes == after.attributes, "Attributes mismatch", "mismatch")
    _require(len(before.data) == len(after.data), "Length mismatch", "mismatch")
    _require(len(edits) <= 4096, "Too many edits")
    expected = bytearray(before.data)
    previous = -1
    for offset, old, new in edits:
        _require(type(offset) is int and type(old) is int and type(new) is int, "Edits must be integers")
        _require(previous < offset < len(expected), "Offsets must be sorted, unique and in bounds")
        _require(0 <= old <= 255 and 0 <= new <= 255, "Edit value outside byte range")
        _require(before.data[offset] == old, "Plan baseline mismatch", "mismatch")
        expected[offset] = new
        previous = offset
    _require(expected == after.data, "Observed bytes differ from exact plan", "mismatch")
    return "unchanged" if before.data == after.data else "matched"


def compare_set(plans: Sequence[tuple[Snapshot, Sequence[tuple[int, int, int]]]],
                observed: Sequence[Snapshot]) -> list[str]:
    """Compare the caller-declared set, including unchanged dependencies.

    No claim is made that the caller supplied every real-world dependency.
    """
    _require(0 < len(plans) <= 16 and len(observed) <= 16, "Invalid store count")
    for snapshot, _ in plans:
        snapshot.validate()
    for snapshot in observed:
        snapshot.validate()
    keys = [(s.guid, s.name) for s, _ in plans]
    actual = {(s.guid, s.name): s for s in observed}
    _require(len(set(keys)) == len(keys) and len(actual) == len(observed), "Duplicate store")
    _require(set(keys) <= set(actual), "Missing observed store", "incomplete")
    _require(set(keys) == set(actual), "Unexpected observed store")
    return [compare_snapshots(s, actual[(s.guid, s.name)], edits) for s, edits in plans]
