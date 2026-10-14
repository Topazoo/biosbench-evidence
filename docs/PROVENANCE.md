# Source and dependency audit

This isolated Python port was prepared from generic source components inspected
read-only on 2026-10-14. Original source snapshots and local paths remain outside
the repository in a private audit directory. No engineering workspace was used
as a build/test directory or modified. No archives were imported wholesale.

| Original component | SHA-256 of inspected copy | Treatment |
| --- | --- | --- |
| `readback.rs` | `3d6f3e67a2d9c60a60b90ef68e1f420a888fff67d72d53a46db6356eaa3adb4b` | Ported exact identity/attribute/byte and set comparison rules. |
| `snapshot_text.rs` | `6e23e8407b4d409d4c777924419eaf606ca28bbda475aaca5608f6930f0fa980` | Ported bounded five-line decoder; display of raw values omitted. |
| `firmware_report.rs` | `765638ceee8d09e98312abdf92228b6cb940a3393e6ef02a048bb1558d45b559` | Generic envelope and companion references only; board analysis excluded. |
| `firmware_bundle.rs` | `6b7965ddb67a1a60006976fa887b4bbe9327c933a9e41fea536e4526d06e858a` | Explicit selection and same-buffer digest checks ported. |
| `boot_inventory.rs` | `0506c02c29672a7a381f43a6dad76daa253547b8f3d27a1c5c04c901f0059941` | Generic memory/image inventory structure checks ported. |

The inspected original client/profile manifests have no license declaration
and `publish=false`. A scoped search of the three source crate directories found
no LICENSE, NOTICE, COPYRIGHT, or AUTHORS files outside build output. Source
headers identify purpose, not ownership. This is insufficient to assert the requester
or any other person holds all necessary redistribution rights. No broader
third-party clearance is inferred from the absence of notices.

The original client uses local bridge/profile/firmware-verification crates and
`windows-sys = 0.61.2`; its bundle hash uses Windows CNG. None is included or
depended upon here. The deliverable has **zero third-party Python dependencies**;
Python and its standard library are prerequisites, not bundled. `hashlib.sha256`
replaces CNG. No copied hashing implementation, Rust crates, runtime binaries,
vendor blobs, or dependency caches are shipped. Packaging uses Python `zipfile`.

Tests, fixture generator, CLI, archive/check scripts, and documentation were
written for this extraction. Fixtures use zero GUIDs and generic Example names,
empty inventories, or explicitly synthetic failures, not captured hardware.
Source-derived Python ports still require ownership clearance. MIT is a proposal,
not a claim that missing original licenses have been resolved.
