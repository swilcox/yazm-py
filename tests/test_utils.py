from yazm.utils import from_u16_to_i16


def test_from_u16_to_i16():
    assert 1 == from_u16_to_i16(1)
    assert 0 == from_u16_to_i16(0)
    assert -32768 == from_u16_to_i16(32768)
    assert 32767 == from_u16_to_i16(32767)
    assert -31536 == from_u16_to_i16(34000)
    assert -1 == from_u16_to_i16(65535)
