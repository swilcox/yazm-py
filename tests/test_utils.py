from yazm.utils import from_u16_to_i16


def test_from_u16_to_i16():
    assert from_u16_to_i16(1) == 1
    assert from_u16_to_i16(0) == 0
    assert from_u16_to_i16(32768) == -32768
    assert from_u16_to_i16(32767) == 32767
    assert from_u16_to_i16(34000) == -31536
    assert from_u16_to_i16(65535) == -1
