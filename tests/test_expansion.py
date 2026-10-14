"""Synthetic structure and browser-buffer cases; no firmware inputs."""

from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from biosbench_evidence import BrowserBuffer, BrowserPlan, EvidenceError, inspect_hii, verify_browser
from biosbench_evidence.browser import decode_case
from biosbench_evidence import hii


def package(body: bytes, kind=2) -> bytes:
    payload = (len(body) + 4).to_bytes(3, "little") + bytes([kind]) + body + b"\x04\0\0\xdf"
    return bytes(16) + (20 + len(payload)).to_bytes(4, "little") + payload


def body() -> bytes:
    return (bytes([14, 0x97]) + bytes(21) + bytes([1, 0x86, 1, 0, 2, 0])
            + bytes([0x24, 24]) + bytes(16) + bytes([1, 0, 4, 0, 83, 0])
            + bytes([0xEE, 2, 0x29, 2, 0x29, 2]))


class HiiTests(unittest.TestCase):
    def test_counts_and_unknown_packages(self):
        summary = inspect_hii(package(body()) + package(b"opaque", kind=0xE7))
        self.assertEqual((summary["lists"], summary["packages"], summary["operations"]), (2, 4, 6))
        self.assertEqual((summary["form_sets"], summary["forms"], summary["buffer_stores"]), (1, 1, 1))
        self.assertEqual((summary["max_depth"], summary["unknown_operations"]), (2, 1))

    def test_every_truncation_rejected(self):
        data = package(body())
        for end in range(len(data)):
            with self.subTest(end=end), self.assertRaises(EvidenceError):
                inspect_hii(data[:end])

    def test_bad_list_package_and_end_lengths(self):
        data = package(body())
        for offset, values in ((16, (0, 23, 255)), (20, (0, 1, 3, 255))):
            for value in values:
                bad = bytearray(data)
                bad[offset] = value
                with self.assertRaises(EvidenceError):
                    inspect_hii(bytes(bad))
        for data in (package(b"\x29\x02"), package(body() + b"\x29\x02"),
                     package(b"\xee\x82"), package(b"\xee\x00"), package(b"\xee\x03")):
            with self.assertRaises(EvidenceError):
                inspect_hii(data)

    def test_known_shapes_names_and_scope(self):
        for record in (bytes([1, 6, 0, 0, 0, 0]), bytes([14, 0x97]) + bytes(20) + b"\x04",
                       bytes([0x24, 24]) + bytes(16) + bytes([0, 0, 4, 0, 83, 0]),
                       bytes([0x24, 24]) + bytes(16) + bytes([1, 0, 4, 0, 0, 0]),
                       bytes([0x25, 20]) + bytes(18), bytes([0x26, 27]) + bytes(25)):
            with self.assertRaises(EvidenceError):
                inspect_hii(package(record))
        for opcode, length in ((0x25, 20), (0x26, 27)):
            record = bytearray(length)
            record[:3] = bytes([opcode, length, 1])
            self.assertEqual(inspect_hii(package(bytes(record)))["other_stores"], 1)

    def test_resource_caps_at_and_over_boundaries(self):
        data = package(body())
        for constant, exact in (("MAX_BYTES", len(data)), ("MAX_LISTS", 1),
                                ("MAX_PACKAGES", 2), ("MAX_OPERATIONS", 6), ("MAX_DEPTH", 2)):
            with patch.object(hii, constant, exact):
                inspect_hii(data)
            with patch.object(hii, constant, exact - 1), self.assertRaises(EvidenceError):
                inspect_hii(data)
        # Exercise the actual depth cap as well as reduced-cap boundary checks.
        nested = b"\xee\x82" * 256 + b"\x29\x02" * 256
        self.assertEqual(inspect_hii(package(nested))["max_depth"], 256)
        with self.assertRaises(EvidenceError):
            inspect_hii(package(b"\xee\x82" + nested + b"\x29\x02"))


class BrowserTests(unittest.TestCase):
    def setUp(self):
        self.buffers = [BrowserBuffer(bytes([i]) * 16, b"S\0", bytes(4)) for i in range(3)]
        self.plans = [BrowserPlan(self.buffers[0], [(1, 0, 5)])]
        self.plans += [BrowserPlan(buffer) for buffer in self.buffers[1:]]
        self.staged = [replace(self.buffers[0], data=b"\0\x05\0\0"), *self.buffers[1:]]

    def test_baseline_staged_reordering_and_unchanged_dependencies(self):
        self.assertEqual(verify_browser(self.plans, self.buffers), ["unchanged"] * 3)
        self.assertEqual(verify_browser(self.plans, list(reversed(self.staged)), staged=True),
                         ["matched", "unchanged", "unchanged"])
        with self.assertRaises(EvidenceError):
            verify_browser(self.plans, self.buffers, staged=True)

    def test_every_dependency_bit_in_both_phases(self):
        for staged, baseline in ((False, self.buffers), (True, self.staged)):
            for store in range(3):
                for offset in range(4):
                    for bit in range(8):
                        observed = list(baseline)
                        data = bytearray(observed[store].data)
                        data[offset] ^= 1 << bit
                        observed[store] = replace(observed[store], data=bytes(data))
                        with self.assertRaises(EvidenceError):
                            verify_browser(self.plans, observed, staged=staged)

    def test_missing_duplicate_extra_and_invalid_names(self):
        with self.assertRaises(EvidenceError) as context:
            verify_browser(self.plans, self.buffers[:2])
        self.assertEqual(context.exception.category, "incomplete")
        for observed in ([self.buffers[0]] * 3, [*self.buffers, replace(self.buffers[0], name=b"T\0")],
                         [replace(self.buffers[0], name=b"\0\xd8"), *self.buffers[1:]]):
            with self.assertRaises(EvidenceError):
                verify_browser(self.plans, observed)

    def test_baseline_validates_entire_plan(self):
        for edits in ([(1, 1, 5)], [(1, 0, 5), (1, 0, 5)], [(-1, 0, 0)],
                      [(4, 0, 0)], [(0, 0, 256)], [(True, 0, 0)], [[0]], [(0, 0, 0)] * 4097):
            with self.assertRaises(EvidenceError):
                verify_browser([BrowserPlan(self.buffers[0], edits)], [self.buffers[0]])

    def test_case_decoder_rejects_shape_and_identity_errors(self):
        for value in (None, {}, {"version": True, "plans": [], "observed": []},
                      {"version": 1, "plans": [{}], "observed": []}):
            with self.assertRaises(EvidenceError):
                decode_case(value)


class ExpansionCliTests(unittest.TestCase):
    def test_duplicate_json_fields_are_invalid(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "duplicate.json"
            path.write_text('{"version":1,"version":1,"plans":[],"observed":[]}', encoding="ascii")
            result = subprocess.run([sys.executable, "-m", "biosbench_evidence", "browser", str(path)],
                                    text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["detail"], "Duplicate JSON field")

    def test_synthetic_cli_examples(self):
        cases = [("hii", "fixtures/hii-valid.hex", "--hex"),
                 ("browser", "fixtures/browser-baseline.json"),
                 ("browser", "fixtures/browser-staged.json", "--staged")]
        for args in cases:
            result = subprocess.run([sys.executable, "-m", "biosbench_evidence", *args],
                                    text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["semantics"], "not_checked")
        result = subprocess.run([sys.executable, "-m", "biosbench_evidence", "hii",
                                 "fixtures/hii-invalid.hex", "--hex"],
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["state"], "invalid")
