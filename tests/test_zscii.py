from yazm import zscii
from yazm.zmachine import ZMachine

from ._sample_data import ZSAMPLE_DATA


def make_zm():
    return ZMachine(ZSAMPLE_DATA)


# --- zscii_to_ascii ---


def test_zscii_to_ascii_basic():
    zm = make_zm()
    result = zscii.zscii_to_ascii(zm, [72, 101, 108, 108, 111])
    assert result == "Hello"


def test_zscii_to_ascii_newline():
    zm = make_zm()
    result = zscii.zscii_to_ascii(zm, [13])  # CR → \n
    assert result == "\n"


def test_zscii_to_ascii_null():
    zm = make_zm()
    result = zscii.zscii_to_ascii(zm, [0])  # null → no effect
    assert result == ""


def test_zscii_to_ascii_mixed():
    zm = make_zm()
    result = zscii.zscii_to_ascii(zm, [0, 72, 105, 0])
    assert result == "Hi"


def test_zscii_to_ascii_space():
    zm = make_zm()
    result = zscii.zscii_to_ascii(zm, [32])
    assert result == " "


def test_zscii_to_ascii_printable_range():
    zm = make_zm()
    # All printable ASCII chars
    chars = list(range(32, 127))
    result = zscii.zscii_to_ascii(zm, chars)
    expected = "".join(chr(c) for c in range(32, 127))
    assert result == expected


def test_zscii_to_ascii_unicode_default_table():
    zm = make_zm()
    # ZSCII 155 → ä (0xE4)
    result = zscii.zscii_to_ascii(zm, [155])
    assert result == chr(0xE4)


def test_zscii_to_ascii_invalid_chars():
    zm = make_zm()
    # Chars 1-12 and 14-31 are invalid/ignored
    result = zscii.zscii_to_ascii(zm, [1, 5, 14, 31])
    assert result == ""


# --- unpack_string (via zmachine.read_zstring) ---


def test_unpack_basic_lowercase():
    zm = make_zm()
    # Read object 1's name - it should be a valid string
    name = zm.get_object_name(1)
    assert isinstance(name, str)
    assert len(name) > 0
    # Should contain only printable characters
    for ch in name:
        assert ch.isprintable() or ch == "\n"


def test_unpack_via_dictionary():
    """Dictionary entries are packed strings that exercise the unpacker."""
    zm = make_zm()
    # Read a dictionary entry
    for word, addr in zm.dictionary.items():
        assert isinstance(word, str)
        assert len(word) > 0
        break  # just check the first one


def test_unpack_abbreviation():
    """Abbreviations use the same unpacking mechanism."""
    zm = make_zm()
    abbrev = zm.get_abbrev(0)
    assert isinstance(abbrev, str)


def test_unpack_multiple_objects_have_names():
    """Verify many objects have unpacked names."""
    zm = make_zm()
    named_count = 0
    for i in range(1, min(zm.get_total_object_count() + 1, 20)):
        name = zm.get_object_name(i)
        if name:
            named_count += 1
    assert named_count > 5


def test_default_alphabets():
    assert len(zscii.DEFAULT_A0) == 26
    assert len(zscii.DEFAULT_A1) == 26
    assert len(zscii.DEFAULT_A2) == 26
    assert zscii.DEFAULT_A0 == "abcdefghijklmnopqrstuvwxyz"
    assert zscii.DEFAULT_A1 == "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def test_zscii_to_ascii_unicode_out_of_range():
    """ZSCII chars 224-251 not in DEFAULT_UNICODE_TABLE → '?'."""
    zm = make_zm()
    # 224 is in range 155-251 but not in DEFAULT_UNICODE_TABLE (which ends at 223)
    result = zscii.zscii_to_ascii(zm, [224])
    assert result == "?"


def test_zscii_to_ascii_high_invalid():
    """ZSCII chars 252+ are invalid and ignored."""
    zm = make_zm()
    result = zscii.zscii_to_ascii(zm, [252, 255])
    assert result == ""


def test_zscii_to_ascii_range_127_154():
    """ZSCII chars 127-154 are invalid/ignored."""
    zm = make_zm()
    result = zscii.zscii_to_ascii(zm, [127, 128, 154])
    assert result == ""


def test_unpack_string_version1_a2():
    """Version 1 uses DEFAULT_A2_Z1 alphabet."""
    zm = make_zm()
    zm.version = 1
    # char=0 → space in any version
    # Use a minimal packed word: pack chars [0, 0, 0] = 0x0000 (no end bit, but no more)
    # Build a terminating packed word: 0x8000 = end bit set, chars [0,0,0]
    result = zscii.unpack_string(zm, [0x8000])
    assert isinstance(result, str)
    # Should produce spaces for char=0
    assert result == "   "


def test_unpack_string_version2_abbrev():
    """Version 2: char==1 triggers abbreviation (not newline)."""
    zm = make_zm()
    zm.version = 2
    # char=1 with version==2 triggers abbrev_shift, then next char=0 picks abbrev 0
    # pack [1, 0, 0] into a word: (1<<10)|(0<<5)|0 = 0x0400, then terminator 0x8000
    result = zscii.unpack_string(zm, [0x0400 | 0x8000])
    # abbrev 0 should expand - just verify it returns a string without error
    assert isinstance(result, str)


def test_unpack_string_version2_shift_lock():
    """Version < 3: shift codes 4 and 5 lock the shift (no unshift after next char)."""
    zm = make_zm()
    zm.version = 2
    # char=4 (shift lock to A1), then char=6 → A1[0]='A'
    # pack [4, 6, 0] → (4<<10)|(6<<5)|0 = 0x10C0, end bit set: 0x90C0
    result = zscii.unpack_string(zm, [0x90C0])
    assert isinstance(result, str)
    # After shift-lock to A1, char 6 → A1[0] = 'A'
    assert "A" in result


def test_unpack_string_shift_back_after_temp():
    """Version 3: temp shift (4 or 5) reverts to A0 after one char."""
    zm = make_zm()
    # char=4 → temp shift to A1; char=6 → A1[0]='A'; next char=6 should be back in A0='a'
    # pack [4, 6, 6] into two words:
    # first word: (4<<10)|(6<<5)|6 = 0x10C6
    # second word (terminator): (0<<10)|(31<<5)|31 = 0x83FF with end bit = 0x83FF
    result = zscii.unpack_string(zm, [0x10C6, 0x8000])
    assert isinstance(result, str)
    assert "A" in result
    assert "a" in result


def test_unpack_string_newline_char7_in_a2():
    """Version > 1: char==7 while current alphabet is A2 → newline (line 172)."""
    zm = make_zm()
    # char=5 (temp shift to A2), char=7 (→ newline), pad=5
    # (5<<10)|(7<<5)|5 = 0x1400|0x00E0|5 = 0x14E5, with end bit: 0x94E5
    result = zscii.unpack_string(zm, [0x94E5])
    assert "\n" in result


def test_unpack_string_version1_char1_newline():
    """Version 1: char==1 → newline (line 176)."""
    zm = make_zm()
    zm.version = 1
    # char=1, pad=5, pad=5: (1<<10)|(5<<5)|5 = 0x0400|0x00A0|5 = 0x04A5, end bit: 0x84A5
    result = zscii.unpack_string(zm, [0x84A5])
    assert "\n" in result


def test_unpack_string_version2_temp_shift():
    """Version < 3: char=2 (temp shift to A1, temp_shift=1) then print a char (line 183)."""
    zm = make_zm()
    zm.version = 2
    # char=2 → temp shift A0→A1, temp_shift=1; char=6 → A1[0]='A'; pad=5
    # (2<<10)|(6<<5)|5 = 0x0800|0x00C0|5 = 0x08C5, end bit: 0x88C5
    result = zscii.unpack_string(zm, [0x88C5])
    assert "A" in result


def test_unpack_string_10bit_escape():
    """Char 6 in A2 triggers 10-bit ZSCII escape sequence."""
    zm = make_zm()
    # Reach A2: char=5 (temp shift to A2), then char=6 (10-bit escape start)
    # Then high bits (char), then low bits (char) → ZSCII for 'A' = 65 = 0b01000001
    # high 5 bits of 65: 65>>5 = 2, low 5 bits: 65&0x1f = 1
    # pack [5, 6, 2] → (5<<10)|(6<<5)|2 = 0x14C2
    # pack [1, 0, 0] terminal → 0x8400 (end bit set, then [1<<10|0|0] = 0x0400 | 0x8000 = 0x8400)
    # wait, we need [1, <padding>] in the last word with end bit
    # [1, 5, 5] (padding) → (1<<10)|(5<<5)|(5) = 0x04A5 | 0x8000 = 0x84A5
    result = zscii.unpack_string(zm, [0x14C2, 0x84A5])
    assert isinstance(result, str)
    # should contain chr(65) = 'A'
    assert "A" in result
