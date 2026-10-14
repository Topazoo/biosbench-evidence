"""Synthetic tests only. No device evidence, hardware, network, or collectors."""

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from biosbench_evidence.core import (
    COMPANIONS, MAX_DATA, MAX_FIELDS, MAX_REPORT, EvidenceError, Snapshot,
    compare_set, compare_snapshots, parse_report, parse_snapshot, validate_bundle,
)

BASE = (b"BiosBench | Rust diagnostics v1\nboard_verified=false\n"
        b"profile_applied=false\nfirmware_flashed=false\n")


def reference(kind="flash_survey", data=b"synthetic payload\n"):
    if kind.startswith("boot_inventory_") and data == b"synthetic payload\n":
        inventory_kind = "memory_map" if kind.endswith("memory") else "loaded_images"
        ending = "complete=true\n" if inventory_kind == "memory_map" else "failed_observations=0\nenumeration_complete=true\n"
        data = (f"biosbench_boot_inventory_version=1\nkind={inventory_kind}\n"
                "authenticated=false\natomic=false\ncount=0\n" + ending).encode()
    prefix, _ = COMPANIONS[kind]
    name = prefix + "001.TXT"
    lines = (f"{kind}_status=SAVED\n{kind}_bundle_file={name}\n"
             f"{kind}_sha256={hashlib.sha256(data).hexdigest()}\n")
    return lines.encode(), name, data


def snapshot(data=b"\x01\x02\x03"):
    return Snapshot(bytes(16), "Example".encode("utf-16le"), 7, data)


def snapshot_text(data=b"\x01\x02\x03"):
    return ("BiosBench supplied snapshot v1\nguid_bytes=" + "00" * 16
            + "\nname_utf16le=4500780061006d0070006c006500\nattributes_le=07000000\ndata="
            + data.hex() + "\n").encode()


class ReportTests(unittest.TestCase):
    def test_valid_and_opaque_fields(self):
        self.assertEqual(parse_report(BASE + b"extension=a=b\n")["extension"], "a=b")

    def test_bad_encoding_header_and_fields(self):
        for data in (b"", BASE.replace(b"\n", b"\r\n"), BASE + b"x=\x00\n",
                     BASE + b"x=\xff\n", BASE + b"x\n", BASE + b"=a\n",
                     BASE + b"bad key=a\n", BASE + b"k=" + b"a" * 2049,
                     BASE + b"board_verified=false\n", BASE[1:]):
            with self.subTest(data=data[:25]), self.assertRaises(EvidenceError):
                parse_report(data)

    def test_missing_is_incomplete_not_false(self):
        with self.assertRaises(EvidenceError) as context:
            parse_report(BASE.replace(b"board_verified=false\n", b""))
        self.assertEqual(context.exception.category, "incomplete")
        with self.assertRaises(EvidenceError):
            parse_report(BASE.replace(b"board_verified=false", b"board_verified=true"))

    def test_byte_and_field_limits(self):
        valid = BASE + b"".join(f"k{i}=x\n".encode() for i in range(MAX_FIELDS - 3))
        self.assertEqual(len(parse_report(valid)), MAX_FIELDS)
        with self.assertRaises(EvidenceError):
            parse_report(valid + b"extra=x\n")
        valid = BASE + b"\n" * (MAX_REPORT - len(BASE))
        parse_report(valid)
        with self.assertRaises(EvidenceError):
            parse_report(valid + b"\n")

    def test_companion_reference_rejections(self):
        lines, _, _ = reference()
        for bad in (lines.replace(b"BFLA001.TXT", b"../BFLA001.TXT"),
                    lines.replace(b"BFLA001.TXT", b"BFLA000.TXT"),
                    lines.replace(b"SAVED", b"DEVICE_ERROR"),
                    lines + b"flash_survey_extra=x\n",
                    lines.replace(b"_sha256=", b"_digest=")):
            with self.assertRaises(EvidenceError):
                parse_report(BASE + bad)


class BundleTests(unittest.TestCase):
    def test_missing_and_unreported_are_distinct(self):
        lines, _, _ = reference()
        result = validate_bundle(BASE + lines, {})
        self.assertEqual(result["state"], "incomplete")
        self.assertEqual(result["companions"][0]["bytes"], "missing")
        self.assertEqual(result["companions"][1]["reported_status"], "UNREPORTED")

    def test_hash_match_does_not_validate_malformed_content_or_failed_save(self):
        lines, name, data = reference(data=b"not a valid semantic inventory")
        result = validate_bundle(BASE + lines + b"save_status=FLUSH_FAILED\n", {name: data})
        self.assertEqual(result["declared_links"], "matched")
        self.assertEqual(result["companions"][0]["semantics"], "not_checked")
        self.assertEqual(result["save_completion"], "unverified")

    def test_complete_only_when_all_three_byte_links_match(self):
        parts = [reference(kind) for kind in COMPANIONS]
        result = validate_bundle(BASE + b"".join(p[0] for p in parts),
                                 {name: data for _, name, data in parts})
        self.assertEqual(result["state"], "complete")
        self.assertEqual(result["authenticity"], "unverified")

    def test_digest_mismatch_unexpected_empty_and_oversize(self):
        lines, name, data = reference()
        for selected in ({name: data + b"x"}, {"wrong.txt": data}, {name: b""},
                         {name: b"x" * 32769}):
            with self.assertRaises(EvidenceError):
                validate_bundle(BASE + lines, selected)


class SnapshotTests(unittest.TestCase):
    def test_decode_and_limits(self):
        self.assertEqual(parse_snapshot(snapshot_text()), snapshot())
        self.assertEqual(len(parse_snapshot(snapshot_text(b"x" * MAX_DATA)).data), MAX_DATA)
        for data in (snapshot_text(b""), snapshot_text(b"x" * (MAX_DATA + 1)),
                     snapshot_text().replace(b"\n", b"\r\n"), snapshot_text() + b"extra\n",
                     snapshot_text().replace(b"data=010203", b"data=xyz")):
            with self.assertRaises(EvidenceError):
                parse_snapshot(data)

    def test_name_and_metadata_rejections(self):
        for name in (b"", b"x", b"\x00\xd8", b"\x00\x00", b"A\x00" * 257):
            with self.assertRaises(EvidenceError):
                replace(snapshot(), name=name).validate()
        for field in ({"guid": b"x"}, {"attributes": -1}, {"attributes": 2**32}):
            with self.assertRaises(EvidenceError):
                replace(snapshot(), **field).validate()

    def test_identity_attributes_and_length(self):
        for field in ({"guid": b"x" * 16}, {"name": b"X\0"},
                      {"attributes": 3}, {"data": b"x"}):
            with self.assertRaises(EvidenceError) as context:
                compare_snapshots(snapshot(), replace(snapshot(), **field))
            self.assertEqual(context.exception.category, "mismatch")

    def test_exact_plan_and_every_unexpected_bit(self):
        before = snapshot(bytes(16))
        after = snapshot(b"\0\0\x05" + bytes(13))
        self.assertEqual(compare_snapshots(before, after, [(2, 0, 5)]), "matched")
        for offset in range(16):
            for bit in range(8):
                data = bytearray(after.data)
                data[offset] ^= 1 << bit
                with self.assertRaises(EvidenceError):
                    compare_snapshots(before, replace(after, data=bytes(data)), [(2, 0, 5)])

    def test_unchanged_noops_and_bad_plans(self):
        self.assertEqual(compare_snapshots(snapshot(), snapshot()), "unchanged")
        self.assertEqual(compare_snapshots(snapshot(), snapshot(), [(0, 1, 1)]), "unchanged")
        for plan in ([(0, 0, 2)], [(3, 0, 1)], [(-1, 0, 1)], [(0, 1, 256)],
                     [(0, 1, 1), (0, 1, 1)], [(1, 2, 2), (0, 1, 1)], [(True, 2, 2)],
                     [("0", 1, 1)]):
            with self.assertRaises(EvidenceError):
                compare_snapshots(snapshot(), snapshot(), plan)

    def test_set_missing_duplicate_extra_and_dependency_changes(self):
        first = snapshot()
        second = replace(first, name=b"D\0")
        plans = [(first, []), (second, [])]
        self.assertEqual(compare_set(plans, [second, first]), ["unchanged", "unchanged"])
        with self.assertRaises(EvidenceError) as context:
            compare_set(plans, [first])
        self.assertEqual(context.exception.category, "incomplete")
        for observed in ([first, first], [first, replace(second, data=b"abc")],
                         [first, second, replace(second, name=b"E\0")]):
            with self.assertRaises(EvidenceError):
                compare_set(plans, observed)


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        process = subprocess.run([sys.executable, "-m", "biosbench_evidence", *map(str, args)],
                                 capture_output=True, text=True, check=False)
        self.assertEqual(process.stderr, "")
        return process.returncode, json.loads(process.stdout)

    def test_missing_partial_invalid_and_unchanged_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(self.run_cli("report", root / "absent")[0], 2)
            report = root / "report.txt"
            report.write_bytes(BASE)
            self.assertEqual(self.run_cli("bundle", report)[0], 2)
            report.write_bytes(b"malformed")
            self.assertEqual(self.run_cli("report", report)[0], 1)
            saved = root / "snapshot.txt"
            saved.write_bytes(snapshot_text())
            code, result = self.run_cli("compare", saved, saved)
            self.assertEqual((code, result["state"]), (0, "unchanged"))

    def test_duplicate_and_unexpected_selection_rejected_before_open(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lines, name, _ = reference()
            report = root / "report.txt"
            report.write_bytes(BASE + lines)
            for names in ((name, name), ("not-declared",)):
                code, result = self.run_cli("bundle", report, *(root / n for n in names))
                self.assertEqual((code, result["state"]), (1, "invalid"))

    def test_malformed_plans_are_json_errors_without_tracebacks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            saved = root / "snapshot.txt"
            saved.write_bytes(snapshot_text())
            plan = root / "plan.json"
            for content in (b"[", b"{}", b"[null]", b"[[true,2,2]]",
                            b"[[" + b"9" * 5000 + b",1,2]]"):
                plan.write_bytes(content)
                code, result = self.run_cli("compare", saved, saved, "--plan", plan)
                self.assertEqual((code, result["state"]), (1, "invalid"))


if __name__ == "__main__":
    unittest.main()
