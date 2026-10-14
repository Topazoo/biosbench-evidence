# Supported saved formats

All text uses printable ASCII and LF; CRLF, NUL, and non-ASCII bytes are rejected.
A final LF is optional. These are file formats, not hardware interfaces.

## Report envelope

Maximum 32,768 bytes, 1,024 distinct fields. Header is
`BiosBench | Rust diagnostics v1`; legacy personally named headers are not
accepted by this extraction. Subsequent nonblank lines use `key=value`. Keys
contain 1–64 ASCII letters, digits, `_ . [ ] -`; values have at most 2,048 bytes.
Duplicate fields are invalid. `board_verified`, `profile_applied`, and
`firmware_flashed` must each be present and exactly `false`.

Unknown fields are retained as uninterpreted claims, not validated extensions.
Unlike the original application, this library makes no board-specific checks.

Companion prefixes are `flash_survey`, `boot_inventory_memory`, and
`boot_inventory_images`. Each declared prefix allows only `_status`,
`_bundle_file`, and `_sha256`. Status uses uppercase letters/digits/underscore,
beginning with a letter. `SAVED` requires both filename and lowercase 64-digit
SHA-256; other statuses prohibit them. Filenames are respectively `BFLAnnn.TXT`,
`BMAPnnn.TXT`, `BIMGnnn.TXT`, where nnn is 001–999. Paths are prohibited.
Limits are 32,768 bytes for flash surveys and 5 MiB for either inventory.

Only explicitly selected files are read. All selections are checked before any
companion is opened. Duplicate basenames and unreferenced selections are invalid.
The digest covers the in-memory bytes used by the structure validator.

## Boot inventories

At most 5 MiB, 16,400 fields, 8,300 bytes per line, 64 bytes per key. Blank lines,
duplicate keys, unknown fields, and missing fields are rejected. Required common
fields: `biosbench_boot_inventory_version=1`, `kind`, `authenticated=false`,
`atomic=false`, and `count`. Numbers use canonical unsigned decimal (no leading
zeros except zero itself) and fit u64 unless a smaller bound is specified.

For `kind=memory_map`: `count` is 0–4096 and `complete=true`. Each
`region[i].` has `start`, `pages`, `type`, and `attributes`. Start is page-aligned,
pages are positive and at most floor(u64::MAX/4096), type fits u32, and the
half-open spans must not overlap or extend beyond 2^64. Described bytes are span
totals, not verified installed or usable RAM.

For `kind=loaded_images`: `count` is 0–512, `enumeration_complete=true`, and
`failed_observations` is 0–count. Each `image[i].status` is an uppercase status
of at most 64 characters. `SUCCESS` requires `base`, `size`, u32 `code_type` and
`data_type`, and either `path` (1–4096 bytes of lowercase hex) or a non-success
`path_status`. Base plus size must not exceed 2^64. Failed image observations
and failed paths must sum to `failed_observations`. Failure observations may
therefore be structurally valid. No path is opened and no address is accessed.

## Supplied snapshot v1

Exactly five lines, maximum 140,000 bytes:

```text
BiosBench supplied snapshot v1
guid_bytes=00000000000000000000000000000000
name_utf16le=4500780061006d0070006c006500
attributes_le=07000000
data=010203
```

GUID is 16 raw bytes, not a reformatted GUID string. Name is 1–256 UTF-16LE code
units with valid surrogate pairs and no NUL. Attributes are four little-endian
bytes. Data is 1–65,536 bytes. Uppercase hex is accepted. Identity comparison
uses exact GUID/name bytes, followed by attributes, length, and every data byte.

CLI plans are JSON arrays of `[offset, before_byte, after_byte]` using integers
(booleans rejected). Up to 4,096 edits must have strictly increasing unique
offsets. Unlisted bytes must be unchanged. Empty plans assert unchanged bytes;
this differs from the original Rust single-store API, which rejected an empty
plan, but agrees with its unchanged-dependency set behavior. Explicit no-ops
are allowed and produce `unchanged` if the whole snapshot is identical.
