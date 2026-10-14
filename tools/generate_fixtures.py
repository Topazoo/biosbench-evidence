"""Generate only synthetic examples, with deterministic content and hashes."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def expected_files() -> dict[str, bytes]:
    common = "biosbench_boot_inventory_version=1\nauthenticated=false\natomic=false\ncount=0\n"
    payloads = {
        "BFLA001.TXT": b"Synthetic opaque flash-survey payload. Structure is unsupported.\n",
        "BMAP001.TXT": (common + "kind=memory_map\ncomplete=true\n").encode(),
        "BIMG001.TXT": (common + "kind=loaded_images\nfailed_observations=0\nenumeration_complete=true\n").encode(),
    }
    report = ("BiosBench | Rust diagnostics v1\nboard_verified=false\n"
              "profile_applied=false\nfirmware_flashed=false\n")
    for kind, name in zip(("flash_survey", "boot_inventory_memory", "boot_inventory_images"), payloads):
        report += (f"{kind}_status=SAVED\n{kind}_bundle_file={name}\n"
                   f"{kind}_sha256={hashlib.sha256(payloads[name]).hexdigest()}\n")
    snapshot = ("BiosBench supplied snapshot v1\nguid_bytes=" + "00" * 16
                + "\nname_utf16le=4500780061006d0070006c006500\nattributes_le=07000000\ndata=")
    files = dict(payloads)
    files.update({
        "complete-report.txt": report.encode(),
        "partial-save-report.txt": (report + "save_status=FLUSH_FAILED\n").encode(),
        "malformed-report.txt": (report + "board_verified=false\n").encode(),
        "missing-reference-report.txt": "\n".join(
            line for line in report.split("\n") if not line.startswith("flash_survey_sha256=")
        ).encode(),
        "malformed-inventory.txt": b"biosbench_boot_inventory_version=1\nkind=memory_map\n",
        "before.snapshot": (snapshot + "010203\n").encode(),
        "after.snapshot": (snapshot + "010903\n").encode(),
        "plan.json": b"[[1, 2, 9]]\n",
    })
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}
    files["SHA256.json"] = (json.dumps(hashes, indent=2, sort_keys=True) + "\n").encode()
    return files


if __name__ == "__main__":
    folder = ROOT / "fixtures"
    folder.mkdir(exist_ok=True)
    for name, data in expected_files().items():
        (folder / name).write_bytes(data)
    print(f"Generated {len(expected_files())} synthetic fixture files")
