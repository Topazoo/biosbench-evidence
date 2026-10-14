"""Bounded HII package/IFR framing; no expression evaluation or live access."""

from .core import _require

MAX_BYTES = 16 * 1024 * 1024
MAX_LISTS = 1024
MAX_PACKAGES = 16384
MAX_OPERATIONS = 262144
MAX_DEPTH = 256


def inspect_hii(data: bytes) -> dict:
    """Return counts only after the entire supplied package stream validates.

    Known identity opcodes receive shape checks. Unknown packages and opcode
    bodies remain opaque. Counts do not establish semantic validity or identity.
    """
    _require(0 < len(data) <= MAX_BYTES, "HII byte limit")
    result = {"lists": 0, "packages": 0, "operations": 0, "form_sets": 0,
              "forms": 0, "buffer_stores": 0, "other_stores": 0,
              "max_depth": 0, "unknown_operations": 0, "package_types": {}}
    position = 0
    while position < len(data):
        _require(result["lists"] < MAX_LISTS, "HII list limit")
        _require(len(data) - position >= 20, "Truncated HII list")
        size = int.from_bytes(data[position + 16:position + 20], "little")
        _require(24 <= size <= len(data) - position, "Invalid HII list size")
        end = position + size
        cursor = position + 20
        ended = False
        while cursor < end:
            _require(result["packages"] < MAX_PACKAGES, "HII package limit")
            _require(end - cursor >= 4, "Truncated package header")
            length = int.from_bytes(data[cursor:cursor + 3], "little")
            kind = data[cursor + 3]
            _require(4 <= length <= end - cursor, "Invalid package length")
            if kind == 0xDF:
                _require(length == 4 and cursor + length == end, "Invalid package end marker")
                ended = True
            elif kind == 2:
                _inspect_ifr(memoryview(data)[cursor + 4:cursor + length], result)
            key = f"{kind:02x}"
            result["package_types"][key] = result["package_types"].get(key, 0) + 1
            result["packages"] += 1
            cursor += length
        _require(ended, "Missing package end marker")
        result["lists"] += 1
        position = end
    return result


def _inspect_ifr(data: memoryview, result: dict) -> None:
    position = depth = 0
    while position < len(data):
        _require(result["operations"] < MAX_OPERATIONS, "IFR operation limit")
        _require(len(data) - position >= 2, "Truncated IFR header")
        opcode, flags = data[position:position + 2]
        length, scoped = flags & 0x7F, bool(flags & 0x80)
        _require(2 <= length <= len(data) - position, "Invalid IFR length")
        record = data[position:position + length]
        if opcode == 0x29:
            _require(length == 2 and not scoped and depth > 0, "Unmatched IFR end")
            depth -= 1
        else:
            if scoped:
                _require(depth < MAX_DEPTH, "IFR depth limit")
                depth += 1
                result["max_depth"] = max(depth, result["max_depth"])
            if opcode == 1:
                _require(length == 6 and scoped, "Invalid form shape")
                result["forms"] += 1
            elif opcode == 14:
                _require(length >= 23 and scoped, "Invalid form-set shape")
                _require(record[22] & 0xFC == 0 and length == 23 + (record[22] & 3) * 16,
                         "Invalid form-set class identifiers")
                result["form_sets"] += 1
            elif opcode == 0x24:
                _require(not scoped and length >= 23 and record[-1] == 0,
                         "Invalid buffer-store shape")
                _require(all(32 <= byte <= 126 for byte in record[22:-1]), "Invalid store name")
                _require(int.from_bytes(record[18:20], "little") != 0, "Zero store identifier")
                result["buffer_stores"] += 1
            elif opcode in (0x25, 0x26):
                _require(not scoped, "Scoped store declaration")
                if opcode == 0x25:
                    _require(length == 20, "Invalid name/value store shape")
                else:
                    _require(length >= 27 and record[-1] == 0
                             and all(32 <= byte <= 126 for byte in record[26:-1]),
                             "Invalid EFI store shape")
                _require(int.from_bytes(record[2:4], "little") != 0, "Zero store identifier")
                result["other_stores"] += 1
            else:
                result["unknown_operations"] += 1
        result["operations"] += 1
        position += length
    _require(depth == 0, "Unclosed IFR scope")
