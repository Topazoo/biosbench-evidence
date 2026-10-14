"""Check a bounded explicit source allowlist; never scan owner workspaces."""

import ast
from pathlib import Path
import re
import runpy

from generate_fixtures import expected_files

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = (
    ".editorconfig", ".gitattributes", ".gitignore", ".github/workflows/check.yml",
    "README.md", "LICENSE", "SECURITY.md",
    "biosbench_evidence/__init__.py", "biosbench_evidence/__main__.py",
    "biosbench_evidence/core.py", "biosbench_evidence/inventory.py",
    "biosbench_evidence/hii.py", "biosbench_evidence/browser.py",
    "tests/test_evidence.py", "tests/test_inventory.py",
    "tests/test_expansion.py", "docs/EXPANSION.md",
    "tools/generate_fixtures.py", "tools/check_repository.py", "tools/build_archive.py",
    "docs/FORMATS.md", "docs/FAULTS.md", "docs/PROVENANCE.md", "docs/PUBLICATION.md",
    "docs/VALIDATION.md",
)


def allowed_files() -> list[str]:
    examples = runpy.run_path(str(ROOT / "examples/failure-examples/tools/check_package.py"))
    return sorted([*SOURCE_FILES, *("fixtures/" + name for name in expected_files()),
                   *("examples/failure-examples/" + name for name in examples["FILES"])])


def check() -> None:
    expected = set(allowed_files())
    actual = {
        file.relative_to(ROOT).as_posix() for file in ROOT.rglob("*")
        if file.is_file() and not any(part in {".git", "dist", "target", "__pycache__", ".venv"}
                                      for part in file.relative_to(ROOT).parts)
    }
    if actual != expected:
        raise ValueError(f"Allowlist mismatch: missing={expected - actual}, extra={actual - expected}")
    for name in sorted(expected):
        data = (ROOT / name).read_bytes()
        text = data.decode("utf-8")
        if not data.endswith(b"\n") or b"\r" in data or b"\t" in data:
            raise ValueError(f"Line formatting: {name}")
        if any(line.rstrip() != line for line in text.splitlines()):
            raise ValueError(f"Trailing whitespace: {name}")
        if name.endswith(".py"):
            ast.parse(text, filename=name)
        # This catches common accidental local paths, not all sensitive data.
        private_pattern = r"[A-Za-z]:\\|/" + r"Users/|/" + r"home/|app\.slack\.com|BEGIN " + r".*PRIVATE KEY"
        # The scanner contains its own illustrative detection expressions.
        scanners = {"tools/check_repository.py", "examples/failure-examples/tools/check_package.py"}
        if name not in scanners and re.search(private_pattern, text):
            raise ValueError(f"Potential private material: {name}")
    for name, data in expected_files().items():
        if (ROOT / "fixtures" / name).read_bytes() != data:
            raise ValueError(f"Fixture not reproducible: {name}")
    print(f"PASS: {len(expected)} allowlisted text files; synthetic fixtures reproduce exactly")


if __name__ == "__main__":
    check()
