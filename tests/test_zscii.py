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
