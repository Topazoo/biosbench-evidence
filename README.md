# BiosBench Evidence

Offline Python library and CLI for checking saved firmware evidence. Use it in
support tooling, lab automation, or regression tests to distinguish missing
inputs, partial saves, invalid evidence, and exact byte matches. Python 3.12+
and its standard library are the only runtime requirements.

Licensed under [MIT](LICENSE), copyright 2026 Peter Swanson. See the scoped
[source and dependency audit](docs/PROVENANCE.md) and
[publication record](docs/PUBLICATION.md). 

## What it checks

| Input | Supported check |
| --- | --- |
| Saved report | Bounded envelope syntax and explicit companion declarations. |
| Companion bundle | Exact SHA-256 byte links; generic memory/image inventory structure. |
| Settings snapshots | Exact identity, attributes, length, and every byte against a baseline or explicit edit plan. |
| HII package lists | Package/IFR framing, scope balance, and a limited declaration subset. |
| Browser buffers | Exact declared buffer sets and baseline or staged bytes; no persistent-variable attributes. |

There is no collector, driver, firmware writer, or hardware access. Unknown
report fields and HII opcode bodies remain opaque. Flash-survey payload
structure is unsupported even when its byte link matches.

## Quick start

Open a terminal in this repository. No installation or network is needed.
Every example below uses synthetic fixtures and should exit successfully.

Parse a report, then check its explicitly selected companion files:

```console
python -m biosbench_evidence report fixtures/complete-report.txt
python -m biosbench_evidence bundle fixtures/complete-report.txt fixtures/BFLA001.TXT fixtures/BMAP001.TXT fixtures/BIMG001.TXT
```

The first command returns `parsed`; the second checks all three byte links.
Compare unchanged bytes, then a planned change from 2 to 9 at byte offset 1:

```console
python -m biosbench_evidence compare fixtures/before.snapshot fixtures/before.snapshot
python -m biosbench_evidence compare fixtures/before.snapshot fixtures/after.snapshot --plan fixtures/plan.json
```

Inspect HII/IFR structure and check browser buffers before and after staging:

```console
python -m biosbench_evidence hii fixtures/hii-valid.hex --hex
python -m biosbench_evidence browser fixtures/browser-baseline.json
python -m biosbench_evidence browser fixtures/browser-staged.json --staged
```

HII validation checks lengths/end markers and forms, form sets, buffer stores,
name/value stores, and EFI store declaration shapes. It returns counts only
after the entire input validates. It does not evaluate expressions or execute
callbacks. Browser baseline mode checks original bytes; staged mode checks the
complete planned result, including unedited bytes and declared dependencies.
See [HII/IFR and browser formats, APIs, and bounds](docs/EXPANSION.md).

## Interpret results

| Result | Meaning |
| --- | --- |
| `missing` / `unavailable` | An explicitly selected file is absent or unreadable. |
| `incomplete` | A required flag, store, or companion byte link is unavailable. |
| `invalid` | Syntax, bounds, digest agreement, or supported structure failed. |
| `mismatch` | Identity, attributes, length, baseline, or expected bytes differ. |
| `unchanged` | Supplied identity, attributes where applicable, and all bytes match. |
| `matched` | Supplied bytes match the complete explicit edit plan. |
| `complete` | All three companion byte links match and supported structure checks pass. |

CLI exit codes are **0** for a successful supported check, **1** for invalid or
mismatching evidence, and **2** for missing, unavailable, or incomplete evidence.
Argument usage errors also exit 2; use the JSON result to distinguish cases.

Hash consistency is not authenticity or firmware safety. `complete` does not
prove an atomic capture or successful flush/close. Exact bytes do not establish
setting semantics, freshness, provider ownership, effective hardware state,
reboot persistence, safe replay, or permission to change firmware. The supplied
store set may omit real dependencies; this tool cannot discover them.

## Library example

Run from the repository root with the shipped fixtures:

```python
from pathlib import Path
from biosbench_evidence import parse_snapshot, compare_snapshots

before = parse_snapshot(Path("fixtures/before.snapshot").read_bytes())
after = parse_snapshot(Path("fixtures/after.snapshot").read_bytes())
result = compare_snapshots(before, after, [(1, 2, 9)])
print(result)
```

For external inputs, callers must bound acquisition before passing bytes to the
library. `compare_set([(baseline, edits), ...], observed)` checks at most 16
explicit stores. Empty edit plans include unchanged dependencies.
`EvidenceError.category` distinguishes invalid, incomplete, and mismatch cases.

## Synthetic tests and reproducible source package

```console
python -m unittest discover -s tests -v
python tools/check_repository.py
python tools/build_archive.py
```

The checks cover malformed/incomplete reports, partial saves, byte corruption,
HII truncation and resource bounds, and missing/duplicate browser dependencies.
All fixtures are synthetic; `python tools/generate_fixtures.py` recreates them.
The repository checker verifies fixture bytes, basic formatting, Python syntax,
and an explicit text-file allowlist. The archive builder writes a deterministic
source ZIP and SHA-256 under `dist/`. CI uses pinned actions and Python 3.12.10
on Linux and Windows; see [validation scope](docs/VALIDATION.md).

The companion [BiosBench Failure Examples](https://github.com/Topazoo/biosbench-failure-examples)
contains reusable host-only save-fault, one-use, and session examples. It is
a separate package, not a runtime dependency.

See [formats](docs/FORMATS.md), [fault cases](docs/FAULTS.md), and
[input handling and disclosure](SECURITY.md). Source packages exclude real
device reports, private paths/identifiers, vendor code, firmware images,
drivers, board mappings, experimental writers, and runtime binaries.
