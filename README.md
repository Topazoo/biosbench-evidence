# BiosBench Evidence

A small offline Python library and CLI for inspecting saved firmware evidence.
It parses bounded report envelopes, verifies explicitly selected companion byte
links, validates generic boot inventories, and compares every snapshot byte
against an explicit plan. Python 3.12+, standard library only.

Licensed under the [MIT License](LICENSE), copyright 2026 Peter Swanson.
Public GitHub publication is authorized and pending authenticated access and
the remaining [publication checks](docs/PUBLICATION.md).

Useful for support tooling, lab automation, and tests that must distinguish
missing evidence, partial saves, corrupt input, and unchanged snapshots.
There is no collector or firmware writer in this project.

## Quick start

From this directory (no installation or network needed):

```console
python -m biosbench_evidence report fixtures/complete-report.txt
python -m biosbench_evidence bundle fixtures/complete-report.txt fixtures/BFLA001.TXT fixtures/BMAP001.TXT fixtures/BIMG001.TXT
python -m biosbench_evidence compare fixtures/before.snapshot fixtures/before.snapshot
python -m biosbench_evidence compare fixtures/before.snapshot fixtures/after.snapshot --plan fixtures/plan.json
python -m unittest discover -s tests -v
```

All shipped fixtures are synthetic. `python tools/generate_fixtures.py` recreates
them deterministically. `python tools/check_repository.py` checks their hashes,
formatting basics, source syntax, and the explicit deliverable file allowlist.
`python tools/build_archive.py` creates a deterministic source ZIP in `dist/`.

## Results and limits

| Result | Meaning |
| --- | --- |
| `missing` / `unavailable` | An explicitly named file is absent or unreadable. |
| `incomplete` | A required flag/store or one of the three companion byte links is unavailable. |
| `invalid` | Syntax, bounds, digest agreement, or supported inventory structure failed. |
| `mismatch` | Snapshot identity, attributes, length, baseline, or exact expected bytes differ. |
| `unchanged` | Supplied snapshot identity, attributes and all bytes match. |
| `matched` | Supplied snapshot bytes match the complete explicit edit plan. |
| `complete` | All three companion byte links match and no supported structure check failed. |

CLI exit codes: **0** for a successful supported check, **1** for invalid or
mismatching evidence, **2** for missing, unavailable, or incomplete evidence.
Argument usage errors also use argparse's exit code 2. JSON output is the stable
way to distinguish these cases. A single `report` command returns `parsed`;
it does not establish bundle completeness.

`complete` does **not** mean an atomic capture or successful flush/close. Hash
agreement does not authenticate a collector, device, capture time, or firmware.
Byte identity does not establish setting semantics, effective hardware state,
reboot persistence, safe replay, firmware safety, or permission to change it.

This extraction intentionally has a narrower validation scope than the original
engineering application. Unknown main-report fields are opaque claims; board
extensions are not interpreted. Memory and loaded-image inventories have
structural checks. Flash-survey payload structure is explicitly `unsupported`;
its byte link can still be checked. No vendor code, board offsets, device reports,
drivers, firmware images, profile mappings, or experimental writers are included.

## Library use

```python
from biosbench_evidence import parse_snapshot, compare_snapshots

# Caller supplies bounded bytes obtained from its own input source.
before = parse_snapshot(before_bytes)
after = parse_snapshot(after_bytes)
result = compare_snapshots(before, after, [(1, 2, 9)])
```

`compare_set([(baseline, edits), ...], observed)` checks up to 16 explicitly
declared stores, including unchanged dependencies with empty edit plans. It
does not discover dependencies or infer completeness outside the supplied set.
`EvidenceError.category` distinguishes `invalid`, `incomplete`, and `mismatch`.

See [formats](docs/FORMATS.md), [fault examples](docs/FAULTS.md),
[security and input handling](SECURITY.md), and [provenance](docs/PROVENANCE.md).
