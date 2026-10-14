"""Read only explicitly named regular files; never follow report references."""

import argparse
import json
from pathlib import Path
import stat
import sys

from .core import (
    COMPANIONS, MAX_REPORT, MAX_SNAPSHOT, EvidenceError,
    compare_snapshots, parse_report, parse_snapshot, validate_bundle,
)


def load(path: Path, limit: int) -> bytes:
    # Reject non-regular paths before opening; recheck the opened descriptor.
    # Inputs should be in a caller-controlled directory (see security notes).
    if not stat.S_ISREG(path.stat().st_mode):
        raise EvidenceError("invalid", "Expected a regular file")
    with path.open("rb") as stream:
        import os
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise EvidenceError("invalid", "Expected a regular file")
        data = stream.read(limit + 1)
    if not data or len(data) > limit:
        raise EvidenceError("invalid", "Empty or oversized file")
    return data


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError("invalid", "Duplicate JSON field")
        result[key] = value
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    report = commands.add_parser("report")
    report.add_argument("file", type=Path)
    bundle = commands.add_parser("bundle")
    bundle.add_argument("file", type=Path)
    bundle.add_argument("companions", nargs="*", type=Path)
    compare = commands.add_parser("compare")
    compare.add_argument("before", type=Path)
    compare.add_argument("after", type=Path)
    compare.add_argument("--plan", type=Path, help="JSON array of [decimal_offset, old_byte, new_byte]")
    hii = commands.add_parser("hii", help="Inspect supplied HII package/IFR structure")
    hii.add_argument("file", type=Path)
    hii.add_argument("--hex", action="store_true", help="Read a strict hex fixture instead of binary")
    browser = commands.add_parser("browser", help="Compare a supplied browser-case JSON file")
    browser.add_argument("file", type=Path)
    browser.add_argument("--staged", action="store_true", help="Require planned staged bytes")
    args = parser.parse_args()
    try:
        if args.command == "report":
            fields = parse_report(load(args.file, MAX_REPORT))
            result = {"state": "parsed", "fields": len(fields), "semantics": "not_checked"}
        elif args.command == "bundle":
            raw = load(args.file, MAX_REPORT)
            fields = parse_report(raw)
            limits = {fields[k + "_bundle_file"]: limit for k, (_, limit) in COMPANIONS.items()
                      if fields.get(k + "_status") == "SAVED"}
            names = [p.name for p in args.companions]
            if len(names) > 3 or len(names) != len(set(names)) or not set(names) <= set(limits):
                raise EvidenceError("invalid", "Duplicate or unexpected companion selection")
            result = validate_bundle(raw, {p.name: load(p, limits[p.name]) for p in args.companions})
        elif args.command == "hii":
            from .hii import MAX_BYTES, inspect_hii
            raw = load(args.file, MAX_BYTES * 2 + 1 if args.hex else MAX_BYTES)
            if args.hex:
                import re
                text = raw.decode("ascii").removesuffix("\n")
                if len(text) % 2 or not re.fullmatch(r"[0-9a-fA-F]+", text):
                    raise EvidenceError("invalid", "Invalid HII hex fixture")
                raw = bytes.fromhex(text)
            result = {"state": "parsed", "structure": inspect_hii(raw), "semantics": "not_checked"}
        elif args.command == "browser":
            from .browser import decode_case, verify_browser
            plans, observed = decode_case(json.loads(load(args.file, 5 * 1024 * 1024),
                                                     object_pairs_hook=unique_object))
            result = {"state": "matched", "stores": verify_browser(plans, observed, staged=args.staged),
                      "phase": "staged" if args.staged else "baseline", "semantics": "not_checked"}
        else:
            edits = json.loads(load(args.plan, 100_000)) if args.plan else []
            if (not isinstance(edits, list) or len(edits) > 4096
                    or any(not isinstance(e, list) or len(e) != 3 for e in edits)):
                raise EvidenceError("invalid", "Expected an array of three-integer edits")
            state = compare_snapshots(parse_snapshot(load(args.before, MAX_SNAPSHOT)),
                                      parse_snapshot(load(args.after, MAX_SNAPSHOT)), edits)
            result = {"state": state, "semantics": "not_checked"}
        result["limits"] = "Byte evidence only; authenticity, freshness, persistence and firmware safety unverified"
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1 if result["state"] == "invalid" else 2 if result["state"] == "incomplete" else 0
    except FileNotFoundError:
        result = {"state": "missing", "detail": "An explicitly selected file is missing"}
        code = 2
    except ValueError as error:
        detail = str(error) if isinstance(error, EvidenceError) else "Invalid encoding or JSON plan"
        result = {"state": getattr(error, "category", "invalid"), "detail": detail}
        code = 2 if result["state"] == "incomplete" else 1
    except OSError:
        result = {"state": "unavailable", "detail": "Selected file could not be read"}
        code = 2
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
