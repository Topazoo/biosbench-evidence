"""Synthetic inventory faults, separate from hash agreement."""

import unittest

from biosbench_evidence.core import EvidenceError, validate_bundle
from biosbench_evidence.inventory import parse_inventory
from test_evidence import BASE, reference

MEMORY = (b"biosbench_boot_inventory_version=1\nkind=memory_map\nauthenticated=false\n"
          b"atomic=false\ncount=1\ncomplete=true\nregion[0].start=0\nregion[0].pages=1\n"
          b"region[0].type=0\nregion[0].attributes=0\n")
IMAGES = (b"biosbench_boot_inventory_version=1\nkind=loaded_images\nauthenticated=false\n"
          b"atomic=false\ncount=2\nfailed_observations=2\nenumeration_complete=true\n"
          b"image[0].status=NOT_FOUND\nimage[1].status=SUCCESS\nimage[1].base=0\n"
          b"image[1].size=0\nimage[1].code_type=0\nimage[1].data_type=0\n"
          b"image[1].path_status=NOT_FOUND\n")


class InventoryTests(unittest.TestCase):
    def test_memory_bounds_alignment_overflow_and_duplicates(self):
        self.assertEqual(parse_inventory(MEMORY, "memory_map")["described_bytes"], 4096)
        for old, new in ((b"start=0", b"start=1"), (b"pages=1", b"pages=0"),
                         (b"count=1", b"count=01"), (b"count=1", b"count=4097"),
                         (b"atomic=false", b"atomic=true"), (b"type=0", b"type=4294967296"),
                         (b"pages=1", b"pages=18446744073709551615")):
            with self.assertRaises(EvidenceError):
                parse_inventory(MEMORY.replace(old, new), "memory_map")
        for extra in (b"count=1\n", b"unknown=1\n", b"\n"):
            with self.assertRaises(EvidenceError):
                parse_inventory(MEMORY + extra, "memory_map")

    def test_overlap(self):
        second = (b"region[1].start=0\nregion[1].pages=1\n"
                  b"region[1].type=0\nregion[1].attributes=0\n")
        with self.assertRaises(EvidenceError):
            parse_inventory(MEMORY.replace(b"count=1", b"count=2") + second, "memory_map")

    def test_partial_images_are_valid_structure_with_failures(self):
        result = parse_inventory(IMAGES, "loaded_images")
        self.assertEqual(result, {"images": 2, "failed_images": 1, "failed_paths": 1})
        for old, new in ((b"failed_observations=2", b"failed_observations=1"),
                         (b"path_status=NOT_FOUND", b"path_status=SUCCESS")):
            with self.assertRaises(EvidenceError):
                parse_inventory(IMAGES.replace(old, new), "loaded_images")

    def test_matching_digest_preserves_invalid_structure(self):
        lines, name, data = reference("boot_inventory_memory", b"malformed\n")
        result = validate_bundle(BASE + lines, {name: data})
        self.assertEqual(result["state"], "invalid")
        self.assertEqual(result["declared_links"], "matched")
        self.assertEqual(result["companions"][1]["structure"], "invalid")
