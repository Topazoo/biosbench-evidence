# Synthetic fault examples

| Fixture | Expected observation |
| --- | --- |
| `complete-report.txt` plus all three named companions | Complete byte links; generic inventory structure validated; flash structure unsupported. |
| `partial-save-report.txt` plus companions | Byte links can match while save completion remains unverified; an opaque failure claim does not become success. |
| `missing-reference-report.txt` | Saved filename present without digest: incomplete. |
| `malformed-report.txt` | Duplicate field: invalid. |
| `complete-report.txt` with no selected companions | Missing byte links: incomplete. |
| `malformed-inventory.txt` | Invalid structure, even if a report contains its correct digest. |
| `before.snapshot` versus itself | Unchanged supplied bytes. |
| `before.snapshot` versus `after.snapshot`, with `plan.json` | Exact plan matched. |
| Same pair without plan | Mismatch. |

The tests also simulate truncation/missing fields, wrong digests, partial image
observations, inconsistent failure counts, duplicate file selection, invalid
UTF-16, limits, overlapping spans, stale plans, unexpected dependency changes,
and every one-bit corruption of a 16-byte synthetic expected result.

These are portable saved-evidence fault examples, not a port of the original
UEFI save writer or its flush/close fault injector. No hardware failure cause is
claimed to have been reproduced.
