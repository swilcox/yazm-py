"""Tests for quetzal.py (Quetzal IFF save-file format)."""

import struct

import pytest

import yazm.quetzal as quetzal
from yazm.zmachine import ZMachine

from ._sample_data import ZSAMPLE_DATA


def make_zm():
    return ZMachine(ZSAMPLE_DATA)


# --- _write_chunk ---


def test_write_chunk_even_data():
    chunk = quetzal._write_chunk(b"TEST", b"HELL")
    assert chunk[:4] == b"TEST"
    length = struct.unpack(">I", chunk[4:8])[0]
    assert length == 4
    assert chunk[8:12] == b"HELL"
    assert len(chunk) == 12  # no padding needed


def test_write_chunk_odd_data():
    chunk = quetzal._write_chunk(b"TEST", b"HELLO")
    assert chunk[:4] == b"TEST"
    length = struct.unpack(">I", chunk[4:8])[0]
    assert length == 5
    assert chunk[8:13] == b"HELLO"
    assert len(chunk) == 14  # 4+4+5+1 pad


def test_write_chunk_empty():
    chunk = quetzal._write_chunk(b"TEST", b"")
    assert len(chunk) == 8  # just id + length


# --- _parse_chunks ---


def test_parse_chunks_single():
    chunk = quetzal._write_chunk(b"TEST", b"ABCD")
    chunks = quetzal._parse_chunks(chunk)
    assert b"TEST" in chunks
    assert chunks[b"TEST"] == b"ABCD"


def test_parse_chunks_multiple():
    data = quetzal._write_chunk(b"AAA ", b"12") + quetzal._write_chunk(b"BBB ", b"34")
    chunks = quetzal._parse_chunks(data)
    assert b"AAA " in chunks
    assert b"BBB " in chunks
    assert chunks[b"AAA "] == b"12"
    assert chunks[b"BBB "] == b"34"


def test_parse_chunks_odd_padded():
    chunk = quetzal._write_chunk(b"ODD ", b"ABC")  # 3 bytes, padded to 4
    chunks = quetzal._parse_chunks(chunk)
    assert chunks[b"ODD "] == b"ABC"


# --- _compress_cmem / _decompress_cmem ---


def test_compress_identical_returns_empty():
    data = bytes([1, 2, 3, 4, 5])
    result = quetzal._compress_cmem(data, data)
    assert result == b""


def test_compress_decompress_roundtrip():
    original = bytes([1, 2, 3, 0, 0, 4, 5])
    dynamic = bytes([1, 2, 9, 0, 0, 4, 6])
    compressed = quetzal._compress_cmem(dynamic, original)
    restored = quetzal._decompress_cmem(compressed, original)
    assert bytes(restored) == dynamic


def test_compress_with_zero_run():
    original = bytes([0] * 10)
    dynamic = bytes([1] + [0] * 9)
    compressed = quetzal._compress_cmem(dynamic, original)
    restored = quetzal._decompress_cmem(compressed, original)
    assert bytes(restored) == dynamic


def test_compress_all_different():
    original = bytes([0] * 5)
    dynamic = bytes([1, 2, 3, 4, 5])
    compressed = quetzal._compress_cmem(dynamic, original)
    restored = quetzal._decompress_cmem(compressed, original)
    assert bytes(restored) == dynamic


# --- save / restore roundtrip ---


def test_save_produces_iff_form():
    zm = make_zm()
    data = zm.make_save_state(zm.pc)
    assert data[:4] == b"FORM"
    assert data[8:12] == b"IFZS"


def test_save_restore_roundtrip():
    zm = make_zm()
    original_pc = zm.pc
    data = zm.make_save_state(zm.pc)
    zm.pc = 0x1234
    zm.restore_state(data)
    assert zm.pc == original_pc


def test_save_restore_preserves_globals():
    zm = make_zm()
    zm.write_global(10, 0xABCD)
    data = zm.make_save_state(zm.pc)
    zm.write_global(10, 0)
    zm.restore_state(data)
    assert zm.read_global(10) == 0xABCD


# --- restore error cases ---


def test_restore_too_short():
    zm = make_zm()
    with pytest.raises(ValueError, match="too short"):
        quetzal.restore(zm, b"short")


def test_restore_not_iff():
    zm = make_zm()
    with pytest.raises(ValueError, match="Not an IFF"):
        quetzal.restore(zm, b"XXXX" + b"\x00" * 8)


def test_restore_not_quetzal():
    zm = make_zm()
    data = b"FORM" + struct.pack(">I", 4) + b"XXXX"
    with pytest.raises(ValueError, match="Not a Quetzal"):
        quetzal.restore(zm, data)


def test_restore_missing_ifhd():
    zm = make_zm()
    body = quetzal._write_chunk(b"CMem", b"")
    data = b"FORM" + struct.pack(">I", len(body) + 4) + b"IFZS" + body
    with pytest.raises(ValueError, match="Missing IFhd"):
        quetzal.restore(zm, data)


def test_restore_ifhd_too_short():
    zm = make_zm()
    body = quetzal._write_chunk(b"IFhd", b"\x00" * 5)  # less than 13 bytes
    data = b"FORM" + struct.pack(">I", len(body) + 4) + b"IFZS" + body
    with pytest.raises(ValueError, match="IFhd chunk too short"):
        quetzal.restore(zm, data)


def test_restore_release_mismatch():
    zm = make_zm()
    # Build IFhd with wrong release number
    bad_ifhd = struct.pack(">H", 9999)  # wrong release
    bad_ifhd += bytes(zm.header.serial_number)
    bad_ifhd += struct.pack(">H", zm.header.checksum)
    bad_ifhd += bytes([0, 0, 0])  # PC
    body = quetzal._write_chunk(b"IFhd", bad_ifhd)
    data = b"FORM" + struct.pack(">I", len(body) + 4) + b"IFZS" + body
    with pytest.raises(ValueError, match="Release mismatch"):
        quetzal.restore(zm, data)


def test_restore_missing_memory_chunk():
    zm = make_zm()
    # Valid IFhd but no CMem/UMem chunk
    ifhd = struct.pack(">H", zm.header.release)
    ifhd += bytes(zm.header.serial_number)
    ifhd += struct.pack(">H", zm.header.checksum)
    ifhd += bytes([0, 0, 0])  # PC
    body = quetzal._write_chunk(b"IFhd", ifhd)
    data = b"FORM" + struct.pack(">I", len(body) + 4) + b"IFZS" + body
    with pytest.raises(ValueError, match="Missing CMem or UMem"):
        quetzal.restore(zm, data)
