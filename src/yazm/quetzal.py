"""Quetzal IFF/IFZS save-file format: serializer and parser.

Implements the standard Quetzal 1.4 format with CMem (compressed memory) chunks.
"""

from __future__ import annotations

import struct
from typing import TYPE_CHECKING

from .frame import Frame

if TYPE_CHECKING:
    from .zmachine import ZMachine


def _write_chunk(chunk_id: bytes, data: bytes) -> bytes:
    """Build an IFF chunk: 4-byte ID, 4-byte big-endian length, data, pad to even."""
    out = chunk_id + struct.pack(">I", len(data)) + data
    if len(data) % 2 != 0:
        out += b"\x00"
    return out


def _parse_chunks(data: bytes) -> dict[bytes, bytes]:
    """Parse IFF chunks from raw data, return {chunk_id: chunk_data}."""
    chunks: dict[bytes, bytes] = {}
    pos = 0
    while pos + 8 <= len(data):
        chunk_id = data[pos : pos + 4]
        length = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        chunk_data = data[pos + 8 : pos + 8 + length]
        chunks[chunk_id] = chunk_data
        pos += 8 + length
        if length % 2 != 0:
            pos += 1  # skip padding byte
    return chunks


def _compress_cmem(dynamic: bytes | bytearray, original: bytes | bytearray) -> bytes:
    """XOR dynamic against original, then run-length compress trailing zeros."""
    xor = bytes(a ^ b for a, b in zip(dynamic, original, strict=False))
    # Trim trailing zeros from XOR diff
    end = len(xor)
    while end > 0 and xor[end - 1] == 0:
        end -= 1
    xor = xor[:end]

    result = bytearray()
    i = 0
    while i < len(xor):
        b = xor[i]
        if b != 0:
            result.append(b)
            i += 1
        else:
            # Count run of zeros
            run = 0
            i += 1
            while i < len(xor) and xor[i] == 0 and run < 255:
                run += 1
                i += 1
            result.append(0x00)
            result.append(run)
    return bytes(result)


def _decompress_cmem(cmem: bytes, original: bytes | bytearray) -> bytearray:
    """Decompress CMem data and XOR against original to reconstruct dynamic memory."""
    xor = bytearray(len(original))
    src = 0
    dst = 0
    while src < len(cmem) and dst < len(xor):
        b = cmem[src]
        src += 1
        if b != 0:
            xor[dst] = b
            dst += 1
        else:
            # Zero byte followed by count of additional zeros
            if src < len(cmem):
                count = cmem[src] + 1  # the zero itself plus count extra
                src += 1
            else:
                count = 1
            dst += count  # already zero-filled
    return bytearray(a ^ b for a, b in zip(xor, original, strict=False))


def save(zm: ZMachine, pc: int) -> bytes:
    """Build a Quetzal IFF FORM/IFZS save file from current ZMachine state."""
    # IFhd chunk: release(2) + serial(6) + checksum(2) + PC(3) = 13 bytes
    ifhd_data = bytearray()
    ifhd_data += struct.pack(">H", zm.header.release)
    ifhd_data += bytes(zm.header.serial_number)
    ifhd_data += struct.pack(">H", zm.header.checksum)
    ifhd_data.append((pc >> 16) & 0xFF)
    ifhd_data.append((pc >> 8) & 0xFF)
    ifhd_data.append(pc & 0xFF)

    # CMem chunk: compressed XOR diff of dynamic memory
    static_addr = zm.header.static_memory_addr
    dynamic = bytes(zm.memory[0:static_addr])
    cmem_data = _compress_cmem(dynamic, zm.original_dynamic)

    # Stks chunk: concatenated frame data
    stks_data = bytearray()
    for frame in zm.frames:
        stks_data.extend(frame.to_list())

    # Build FORM/IFZS container
    body = _write_chunk(b"IFhd", bytes(ifhd_data))
    body += _write_chunk(b"CMem", cmem_data)
    body += _write_chunk(b"Stks", bytes(stks_data))

    return b"FORM" + struct.pack(">I", len(body) + 4) + b"IFZS" + body


def restore(zm: ZMachine, data: bytes):
    """Parse a Quetzal IFF FORM/IFZS save file and restore ZMachine state.

    Raises ValueError on format errors or mismatched story file.
    """
    if len(data) < 12:
        raise ValueError("Save file too short")
    if data[0:4] != b"FORM":
        raise ValueError("Not an IFF file")
    if data[8:12] != b"IFZS":
        raise ValueError("Not a Quetzal save file")

    chunks = _parse_chunks(data[12:])

    # IFhd — validate story identity
    if b"IFhd" not in chunks:
        raise ValueError("Missing IFhd chunk")
    ifhd = chunks[b"IFhd"]
    if len(ifhd) < 13:
        raise ValueError("IFhd chunk too short")

    release = struct.unpack(">H", ifhd[0:2])[0]
    serial = ifhd[2:8]
    checksum = struct.unpack(">H", ifhd[8:10])[0]
    pc = (ifhd[10] << 16) | (ifhd[11] << 8) | ifhd[12]

    if release != zm.header.release:
        raise ValueError(f"Release mismatch: save={release}, story={zm.header.release}")
    if bytes(serial) != bytes(zm.header.serial_number):
        raise ValueError("Serial number mismatch")
    if checksum != zm.header.checksum:
        raise ValueError(f"Checksum mismatch: save={checksum}, story={zm.header.checksum}")

    # Memory — CMem or UMem
    static_addr = zm.header.static_memory_addr
    if b"CMem" in chunks:
        dynamic = _decompress_cmem(chunks[b"CMem"], zm.original_dynamic)
    elif b"UMem" in chunks:
        dynamic = bytearray(chunks[b"UMem"])
    else:
        raise ValueError("Missing CMem or UMem chunk")

    if len(dynamic) > static_addr:
        raise ValueError("Restored dynamic memory too large")

    # Stks — reconstruct frames
    if b"Stks" not in chunks:
        raise ValueError("Missing Stks chunk")
    frames = _parse_stks(chunks[b"Stks"])

    # Apply restored state
    zm.memory[0 : len(dynamic)] = dynamic
    zm.pc = pc
    zm.frames = frames


def _parse_stks(data: bytes) -> list[Frame]:
    """Parse the Stks chunk into a list of Frame objects."""
    frames = []
    pos = 0
    while pos < len(data):
        if pos + 8 > len(data):
            raise ValueError("Stks chunk truncated in frame header")
        # Read frame header to determine total size
        flags = data[pos + 3]
        num_locals = flags & 0x0F
        stack_length = (data[pos + 6] << 8) | data[pos + 7]
        frame_size = 8 + num_locals * 2 + stack_length * 2
        if pos + frame_size > len(data):
            raise ValueError("Stks chunk truncated in frame body")
        frame_bytes = bytearray(data[pos : pos + frame_size])
        frames.append(Frame.from_bytes(frame_bytes))
        pos += frame_size
    return frames
