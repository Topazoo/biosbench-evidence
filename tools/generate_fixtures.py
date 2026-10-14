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
    ifr = (bytes([14, 0x97]) + bytes(21) + bytes([1, 0x86, 1, 0, 2, 0])
           + bytes([0x24, 24]) + bytes(16) + bytes([1, 0, 4, 0, 83, 0])
           + bytes([0xEE, 2, 0x29, 2, 0x29, 2]))
    def hii(body):
        payload = (len(body) + 4).to_bytes(3, "little") + b"\x02" + body + b"\x04\0\0\xdf"
        return bytes(16) + (20 + len(payload)).to_bytes(4, "little") + payload
    files["hii-valid.hex"] = (hii(ifr).hex() + "\n").encode()
    files["hii-invalid.hex"] = (hii(ifr + b"\x29\x02").hex() + "\n").encode()
    baseline = {"guid": "00" * 16, "name_utf16le": "5300", "data": "00000000"}
    for name, observed in (("baseline", baseline), ("staged", {**baseline, "data": "00050000"})):
        case = {"version": 1, "plans": [{"baseline": baseline, "edits": [[1, 0, 5]]}],
                "observed": [observed]}
        files[f"browser-{name}.json"] = (json.dumps(case, indent=2, sort_keys=True) + "\n").encode()
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}
    files["SHA256.json"] = (json.dumps(hashes, indent=2, sort_keys=True) + "\n").encode()
    return files


if __name__ == "__main__":
    folder = ROOT / "fixtures"
    folder.mkdir(exist_ok=True)
    for name, data in expected_files().items():
        (folder / name).write_bytes(data)
    print(f"Generated {len(expected_files())} synthetic fixture files")
