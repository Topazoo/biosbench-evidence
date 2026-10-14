"""Generic boot-inventory structure checks. No pointers are followed."""

import re

from .core import _ascii, _require


def parse_inventory(data: bytes, kind: str) -> dict:
    """Validate v1 inventory structure and internal count/span consistency.

    This does not establish that records describe real devices or memory.
    Values are summarized rather than echoed, avoiding path/address disclosure.
    """
    fields = {}
    for line in _ascii(data, 5 * 1024 * 1024).splitlines():
        key, separator, value = line.partition("=")
        _require(bool(separator) and 0 < len(key) <= 64 and len(line) <= 8300,
                 "Malformed inventory field")
        _require(key not in fields and len(fields) < 16400, "Duplicate or excessive inventory fields")
        fields[key] = value

    def take(key):
        _require(key in fields, "Missing inventory field")
        return fields.pop(key)

    def exact(key, value):
        _require(take(key) == value, "Unexpected inventory value")

    def number(key, low=0, high=2**64 - 1):
        value = take(key)
        _require(bool(re.fullmatch(r"0|[1-9][0-9]{0,19}", value)), "Invalid inventory number")
        number = int(value)
        _require(low <= number <= high, "Inventory number out of bounds")
        return number

    def status(key):
        value = take(key)
        _require(bool(re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", value)), "Invalid inventory status")
        return value

    exact("biosbench_boot_inventory_version", "1")
    exact("kind", kind)
    exact("authenticated", "false")
    exact("atomic", "false")
    if kind == "memory_map":
        count = number("count", high=4096)
        exact("complete", "true")
        ranges = []
        for index in range(count):
            prefix = f"region[{index}]."
            start = number(prefix + "start")
            pages = number(prefix + "pages", 1, (2**64 - 1) // 4096)
            number(prefix + "type", high=2**32 - 1)
            number(prefix + "attributes")
            end = start + pages * 4096
            _require(start % 4096 == 0 and end <= 2**64, "Invalid inventory span")
            ranges.append((start, end))
        ranges.sort()
        _require(all(a[1] <= b[0] for a, b in zip(ranges, ranges[1:])), "Overlapping inventory spans")
        result = {"regions": count, "described_bytes": sum(end - start for start, end in ranges)}
    elif kind == "loaded_images":
        count = number("count", high=512)
        failed = number("failed_observations", high=count)
        exact("enumeration_complete", "true")
        failed_images = failed_paths = 0
        for index in range(count):
            prefix = f"image[{index}]."
            if status(prefix + "status") != "SUCCESS":
                failed_images += 1
                continue
            base = number(prefix + "base")
            size = number(prefix + "size")
            _require(base + size <= 2**64, "Overflowing inventory span")
            number(prefix + "code_type", high=2**32 - 1)
            number(prefix + "data_type", high=2**32 - 1)
            if prefix + "path" in fields:
                path = take(prefix + "path")
                _require(0 < len(path) <= 8192 and len(path) % 2 == 0
                         and bool(re.fullmatch(r"[0-9a-f]+", path)), "Invalid inventory path bytes")
            else:
                _require(status(prefix + "path_status") != "SUCCESS", "Missing successful path")
                failed_paths += 1
        _require(failed_images + failed_paths == failed, "Inventory failure count mismatch")
        result = {"images": count, "failed_images": failed_images, "failed_paths": failed_paths}
    else:
        _require(False, "Unknown inventory kind")
    _require(not fields, "Unexpected inventory fields")
    return result
