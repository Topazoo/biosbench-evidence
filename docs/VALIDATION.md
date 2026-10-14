# Validation record

This file records local synthetic checks only. No collector, driver, firmware,
owner workspace test, account operation, or physical settings trial is involved.

Local environment: Windows, Python 3.12.14.
Commands to reproduce from the repository root:

```console
python -m unittest discover -s tests -v
python tools/check_repository.py
python tools/build_archive.py
```

Executed successfully on 2026-10-14: **22 unittest test methods**, including
128 individual one-bit corruption cases; a **34-file allowlist/format/source
syntax check**; and exact reproduction of all **12 synthetic fixture files**.
The complete-bundle CLI smoke check returned three matching byte links,
validated generic inventories, explicitly unsupported flash-survey structure,
and unverified authenticity/save completion.

The final task handoff records archive reproducibility and archive SHA-256.
The CI matrix is configured but has not been run on GitHub. Linux execution,
full original-report semantic compatibility, hardware validation, ownership,
and final license clearance are not established by these checks.

The archive includes only allowlisted text source, tests, docs, configuration,
and deterministic synthetic fixtures. It excludes Git history, bytecode,
private source audit copies, build output, and runtime binaries. Archive metadata
and file order are fixed; repeated builds of identical source must match.

The privacy scan is a limited local-path/key-pattern check, supplemented by the
explicit file allowlist and human-readable source review. It is not a guarantee
that every possible private identifier can be detected automatically.
