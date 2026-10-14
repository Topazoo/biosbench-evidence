"""Pure supplied browser buffers. No persistent-variable attributes or actions."""

from dataclasses import dataclass
from typing import Sequence

from .core import Snapshot, _require, compare_set


@dataclass(frozen=True)
class BrowserBuffer:
    guid: bytes
    name: bytes
    data: bytes

    def _snapshot(self) -> Snapshot:
        # Internal comparison reuse only; zero is not an observed attribute value.
        result = Snapshot(self.guid, self.name, 0, self.data)
        result.validate()
        return result


@dataclass(frozen=True)
class BrowserPlan:
    baseline: BrowserBuffer
    edits: Sequence[tuple[int, int, int]] = ()


def verify_browser(plans: Sequence[BrowserPlan], observed: Sequence[BrowserBuffer],
                   *, staged: bool = False) -> list[str]:
    """Check every supplied dependency at baseline or after staging.

    Plans are validated even in baseline mode. Missing evidence is incomplete;
    unchanged data cannot satisfy a plan requiring changed bytes in staged mode.
    """
    _require(type(staged) is bool, "Invalid browser phase")
    _require(0 < len(plans) <= 16 and len(observed) <= 16, "Browser store count limit")
    converted = []
    for plan in plans:
        snapshot = plan.baseline._snapshot()
        _require(len(plan.edits) <= 4096, "Too many browser edits")
        previous = -1
        for edit in plan.edits:
            _require(isinstance(edit, (list, tuple)) and len(edit) == 3, "Invalid edit shape")
            offset, old, new = edit
            _require(all(type(value) is int for value in edit), "Edits require integers")
            _require(previous < offset < len(snapshot.data), "Invalid browser edit order or bounds")
            _require(0 <= old <= 255 and 0 <= new <= 255, "Invalid browser edit byte")
            _require(snapshot.data[offset] == old, "Browser plan baseline mismatch", "mismatch")
            previous = offset
        converted.append((snapshot, plan.edits if staged else ()))
    return compare_set(converted, [buffer._snapshot() for buffer in observed])


def decode_case(value: object) -> tuple[list[BrowserPlan], list[BrowserBuffer]]:
    """Strict synthetic/browser-case JSON adapter; does not open referenced files."""
    _require(isinstance(value, dict) and set(value) == {"version", "plans", "observed"},
             "Invalid browser case fields")
    _require(type(value["version"]) is int and value["version"] == 1, "Unknown browser version")
    _require(isinstance(value["plans"], list) and 0 < len(value["plans"]) <= 16
             and isinstance(value["observed"], list) and len(value["observed"]) <= 16,
             "Invalid browser case lists")

    def buffer(record):
        _require(isinstance(record, dict) and set(record) == {"guid", "name_utf16le", "data"},
                 "Invalid browser buffer fields")
        import re
        decoded = []
        for key, limit in (("guid", 32), ("name_utf16le", 1024), ("data", 131072)):
            text = record[key]
            _require(isinstance(text, str) and 0 < len(text) <= limit and len(text) % 2 == 0
                     and bool(re.fullmatch(r"[0-9a-fA-F]+", text)), "Invalid browser hex")
            decoded.append(bytes.fromhex(text))
        result = BrowserBuffer(*decoded)
        result._snapshot()
        return result

    plans = []
    for record in value["plans"]:
        _require(isinstance(record, dict) and set(record) == {"baseline", "edits"}
                 and isinstance(record["edits"], list), "Invalid browser plan fields")
        plans.append(BrowserPlan(buffer(record["baseline"]), record["edits"]))
    return plans, [buffer(record) for record in value["observed"]]
