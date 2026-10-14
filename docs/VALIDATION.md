# Validation record

## Coverage and known unknowns

All tests listed here use synthetic inputs. A test passing establishes the
implemented behavior for its cases, not general firmware compatibility.

| Area | Published test evidence | What remains unknown |
| --- | --- | --- |
| Report and bundle | `test_evidence.py`: encoding, field limits, companion declarations, missing selections, digest corruption, partial-save examples. | Unknown report-field semantics, capture freshness/authenticity, atomicity, flush/close success. |
| Boot inventory | `test_inventory.py`: bounds, alignment, overflow, overlap, failure counts, malformed structure despite matching digest. | Whether records describe real memory/images, installed RAM, or complete real-world observations. |
| Snapshot comparison | `test_evidence.py`: identity/attributes/length, exact plans, one-bit corruption, stale plans, declared dependency sets. | Setting meanings, undeclared dependencies, effective state, safe replay, persistence. |
| HII/IFR structure | `test_expansion.py`: every synthetic fixture truncation, known declaration shapes, unknown packages, late scope errors, resource boundaries. | Expression/callback behavior, vendor extensions, full UEFI revision conformance, firmware identity. |
| Browser buffers | `test_expansion.py`: both phases, 192 one-bit cases, reordered/missing/duplicate/extra dependencies, malformed plans and JSON. | Provider/session ownership, freshness, atomicity, NVRAM state, callbacks and hardware effects. |
| CLI and packaging | CLI tests, reproducible synthetic fixtures, explicit file allowlist, syntax/format checks, deterministic archive build. | Compatibility beyond tested environments; the limited privacy scan cannot detect every private identifier. |
| Rust failure examples | 8 one-use/session tests and 6 save-fault tests; Cargo and direct compiler runner. Sources and tests retain their published bytes. | Concurrent writers, actual UEFI behavior, durability, power loss, authentication, and physical effects are not modeled. |
| Emulator observations | No emulator run is part of this package's recorded validation. | Emulator-specific behavior and transfer to physical machines. |
| Physical validation | No physical settings trial is part of this package's recorded validation. | Board/BIOS compatibility, reboot persistence, effective hardware behavior and safety. |

Test sources: [report/snapshot/CLI](../tests/test_evidence.py),
[inventories](../tests/test_inventory.py), and
[HII/browser](../tests/test_expansion.py). See the
[evidence-level guide](../README.md#what-the-evidence-establishes) when interpreting
results. Emulator observations and physical trials would need separately
identified environments, methods, and results before supporting new claims.

## Recorded runs

The consolidated workflow runs separate Rust and Python jobs on Linux and
Windows. Rust uses 1.99.0; Python uses 3.12.10. Existing required Python `test`
jobs depend on both Rust matrix jobs, so either language's failures block merge
without changing branch protections. The root allowlist now covers 57 text
files, including the 16-file standalone Rust package. The 16 Python synthetic
fixtures are unchanged. The historical counts below describe earlier scopes.
See [Rust provenance and historical validation](../examples/failure-examples/docs/SCOPE.md).

Local expansion: 34 Python test methods pass on Windows and Linux, including
192 browser-buffer one-bit cases and HII/IFR truncation/shape/boundary tests.
The expanded package has 41 allowlisted text files and 16 reproducible synthetic
fixture files. The expanded scope also passed hosted Linux/Windows checks:
https://github.com/Topazoo/biosbench-evidence/actions/runs/38524718461

This file records local and hosted synthetic checks. No collector, driver, firmware,
owner workspace test, or physical settings trial is involved.

Local environment: Windows, Python 3.12.14.
Commands to reproduce from the repository root:

```console
python -m unittest discover -s tests -v
python tools/check_repository.py
python tools/build_archive.py
```

Initial scope executed successfully on 2026-10-14: **22 unittest test methods**, including
128 individual one-bit corruption cases; a **33-file allowlist/format/source
syntax check**; and exact reproduction of all **12 synthetic fixture files**.
The complete-bundle CLI smoke check returned three matching byte links,
validated generic inventories, explicitly unsupported flash-survey structure,
and unverified authenticity/save completion.

The final task handoff records archive reproducibility and archive SHA-256.
Initial hosted run 38520070956 passed on Linux/Python 3.12.14. Windows setup
failed because that Python patch version has no Windows build in the Actions
manifest. The matrix now pins Python 3.12.10, verified available for Linux and
Windows; the latest run is linked from the repository Actions tab.
Full original-report semantic compatibility and hardware validation are not
established by these checks. Source and dependency provenance is recorded in PROVENANCE.md.

The archive includes only allowlisted text source, tests, docs, configuration,
and deterministic synthetic fixtures. It excludes Git history, bytecode,
private source audit copies, build output, and runtime binaries. Archive metadata
and file order are fixed; repeated builds of identical source must match.

The privacy scan is a limited local-path/key-pattern check, supplemented by the
explicit file allowlist and human-readable source review. It is not a guarantee
that every possible private identifier can be detected automatically.
