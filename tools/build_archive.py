"""Deterministic source ZIP: explicit allowlist, fixed metadata, no binaries."""

import hashlib
from pathlib import Path
import zipfile

from check_repository import ROOT, allowed_files, check


def build(output: Path) -> str:
    check()
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name in allowed_files():
            item = zipfile.ZipInfo("biosbench-evidence/" + name, date_time=(2026, 1, 1, 0, 0, 0))
            item.create_system = 3
            item.external_attr = 0o100644 << 16
            archive.writestr(item, (ROOT / name).read_bytes())
    return hashlib.sha256(output.read_bytes()).hexdigest()


if __name__ == "__main__":
    destination = ROOT / "dist" / "biosbench-evidence-review.zip"
    digest = build(destination)
    destination.with_suffix(".zip.sha256").write_text(
        digest + "  " + destination.name + "\n", encoding="ascii", newline="\n")
    print(f"{digest}  {destination.name}")
