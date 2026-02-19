"""Tests for the Header class."""

import pytest

from yazm.zmachine import ZMachine
from yazm.zdata import ZData
from yazm.zheader import Header, Flag1, Flag2

from ._sample_data import ZSAMPLE_DATA


def make_zm():
    return ZMachine(ZSAMPLE_DATA)


def test_header():
    zmachine = ZMachine(ZSAMPLE_DATA)
    assert zmachine.header.version == 3
    assert zmachine.header.release == 34


def test_header_file_length_v3():
    zm = make_zm()
    # v3: file_length = raw * 2
    raw = ZData(ZSAMPLE_DATA).u16(0x1A)
    assert zm.header.file_length == raw * 2


def test_header_file_length_v4():
    """Simulate a v4 header: file_length = raw * 4."""
    data = bytearray(ZSAMPLE_DATA)
    data[0x0] = 4                          # version = 4
    data[0x1A] = 0x01; data[0x1B] = 0x00  # raw_file_length = 256
    header = Header(ZData(bytes(data)))
    assert header.file_length == 256 * 4


def test_header_file_length_v6():
    """Simulate a v6 header: file_length = raw * 8."""
    data = bytearray(ZSAMPLE_DATA)
    data[0x0] = 6
    data[0x1A] = 0x01; data[0x1B] = 0x00  # raw = 256
    header = Header(ZData(bytes(data)))
    assert header.file_length == 256 * 8


def test_flag1_v3_score_mode():
    zm = make_zm()
    flag1 = zm.header.flag1
    from yazm.enums import StatusLineType
    assert flag1.status_line_type == StatusLineType.score


def test_flag1_v3_time_mode():
    zm = make_zm()
    original = zm.memory[0x1]
    zm.memory[0x1] = 0b00000010  # bit 1 = time mode
    flag1 = zm.header.flag1
    from yazm.enums import StatusLineType
    # bit 1 set → status_line_type != score (non-zero value)
    assert flag1.status_line_type != StatusLineType.score
    zm.memory[0x1] = original


def test_flag1_v4_path():
    """Simulate v4 header to exercise the v4+ flag1 branch."""
    data = bytearray(ZSAMPLE_DATA)
    data[0x0] = 5  # version = 5
    data[0x1] = 0b00000101  # colors_available=1, bold=1
    header = Header(ZData(bytes(data)))
    flag1 = header.flag1
    assert flag1.colors_available is True
    assert flag1.bold is True


def test_flag2_properties():
    zm = make_zm()
    flag2 = zm.header.flag2
    assert isinstance(flag2.transcripting_on, bool)
    assert isinstance(flag2.force_fixed_pitch, bool)
    assert isinstance(flag2.use_undo, bool)


def test_flag2_transcripting():
    data = bytearray(ZSAMPLE_DATA)
    data[0x10] = 0x00; data[0x11] = 0b00000001  # transcripting_on bit
    header = Header(ZData(bytes(data)))
    assert header.flag2.transcripting_on is True


def test_header_hdr_ext_tab():
    """Extension table parsing when present."""
    # The sample v3 data should have hdr_ext_tab_addr = 0
    zm = make_zm()
    assert zm.header.unicode_tab_addr == 0
