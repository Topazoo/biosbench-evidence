# HII/IFR and browser-buffer checks

Two independent offline APIs extend report and snapshot inspection.

## HII/IFR structure

`inspect_hii(bytes)` validates concatenated HII package lists and IFR framing.
Bounds: 16 MiB, 1,024 lists, 16,384 packages, 262,144 operations, 256 scope levels.
It checks length/end markers and the shape of form sets, forms, and three store
declaration types. Unknown package/opcode bodies remain opaque. Results are
counts and type totals, returned only after the entire input validates. Nothing
is emitted from an input that fails late. No extracted device identity is echoed.

```console
python -m biosbench_evidence hii fixtures/hii-valid.hex --hex
python -m biosbench_evidence hii explicitly-selected-package.bin
```

This is a Python port of the generic framing rules in the project's
`hii_packages.rs` and `hii_forms.rs`. It deliberately does not expose the original
identity selector. It does not evaluate expressions, execute callbacks, follow
addresses, authenticate packages, or establish setting semantics.

## Browser buffers

`BrowserBuffer(guid, name, data)` contains exact GUID bytes, UTF-16LE name bytes,
and data. `BrowserPlan(baseline, edits)` declares sorted `(offset, old, new)` byte
edits. `verify_browser(plans, observed, staged=False)` checks original bytes;
`staged=True` checks the exact planned result, including unchanged dependencies.
Both phases validate the whole plan. There are no persistent-variable attributes.
Missing stores remain incomplete; duplicates and malformed input are invalid.

The count/name/data/edit bounds match the existing snapshot APIs. Identity sets
are exact and order-independent. The library returns one `unchanged` or `matched`
result per plan; success does not prove the caller declared every real dependency.

```console
python -m biosbench_evidence browser fixtures/browser-baseline.json
python -m biosbench_evidence browser fixtures/browser-staged.json --staged
```

Case JSON has exactly `version` (integer 1), `plans`, and `observed`. Each plan
contains `baseline` and `edits`; each buffer contains `guid`, `name_utf16le`, and
`data` as unspaced hex. CLI case files are capped at 5 MiB. No filenames or paths
inside JSON are followed. Example GUIDs, names, and bytes are wholly synthetic.

This ports `browser_state.rs` without its application/profile dependencies.
Browser bytes do not establish freshness, provider/session ownership, atomicity,
NVRAM state, safe callbacks, persistence, or effective hardware settings.

## Provenance and checks

These project-source adaptations use the existing MIT license. They introduce
no third-party dependency or copied vendor implementation.
Existing UEFI references are format descriptions, not copied specification text.

Synthetic tests exercise every fixture truncation, malformed shapes, late scope
errors, resource boundaries, 192 per-bit browser corruptions across both phases,
missing/duplicate dependencies, plan validation, and CLI examples. No collector,
emulator, real capture, driver, firmware, or hardware operation is involved.
