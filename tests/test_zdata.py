from yazm.zdata import ZData


def test_zdata_reads():
    bs = bytearray([1, 2])
    zdata = ZData(bs)
    assert zdata[0] == 1
    assert zdata[1] == 2
    assert zdata.u8(0) == zdata[0]
    assert zdata.u8(1) == zdata[1]
    assert zdata.u16(0) == 258


def test_zdata_writes():
    bs = bytearray([1, 2])
    zdata = ZData(bs)
    assert zdata.u16(0) == 258
    zdata.write_u16(0, 42042)
    assert zdata.u16(0) == 42042
    assert zdata.u8(0) == 164
    assert zdata.u8(1) == 58


def test_get_reader():
    zdata = ZData(bytearray([0x00, 0x01, 0x02, 0x03, 0x04]))
    reader = zdata.get_reader(0)
    assert reader.position == 0
    assert reader.byte() == 0x00
    assert reader.position == 1
    assert reader.byte() == 0x01
    assert reader.position == 2


def test_reader_word():
    zdata = ZData(bytearray([0xAB, 0xCD, 0x12, 0x34]))
    reader = zdata.get_reader(0)
    assert reader.word() == 0xABCD
    assert reader.position == 2
    assert reader.word() == 0x1234
    assert reader.position == 4


def test_reader_mixed():
    zdata = ZData(bytearray([0xFF, 0x00, 0x80, 0x01, 0x42]))
    reader = zdata.get_reader(0)
    assert reader.byte() == 0xFF
    assert reader.word() == 0x0080
    assert reader.byte() == 0x01
    assert reader.byte() == 0x42
    assert reader.position == 5


def test_reader_from_offset():
    zdata = ZData(bytearray([0x00, 0x00, 0xAA, 0xBB]))
    reader = zdata.get_reader(2)
    assert reader.position == 2
    assert reader.byte() == 0xAA
    assert reader.byte() == 0xBB


def test_get_writer():
    zdata = ZData(bytearray(5))
    writer = zdata.get_writer(0)
    assert writer.position == 0
    writer.byte(0x42)
    assert writer.position == 1
    assert zdata.u8(0) == 0x42


def test_writer_word():
    zdata = ZData(bytearray(4))
    writer = zdata.get_writer(0)
    writer.word(0xABCD)
    assert writer.position == 2
    assert zdata.u16(0) == 0xABCD
    writer.word(0x1234)
    assert writer.position == 4
    assert zdata.u16(2) == 0x1234


def test_writer_mixed():
    zdata = ZData(bytearray(5))
    writer = zdata.get_writer(0)
    writer.byte(0xFF)
    writer.word(0x1234)
    writer.byte(0xAA)
    writer.byte(0xBB)
    assert zdata.u8(0) == 0xFF
    assert zdata.u16(1) == 0x1234
    assert zdata.u8(3) == 0xAA
    assert zdata.u8(4) == 0xBB


def test_writer_from_offset():
    zdata = ZData(bytearray(6))
    writer = zdata.get_writer(3)
    assert writer.position == 3
    writer.byte(0x99)
    assert zdata.u8(3) == 0x99
    assert zdata.u8(0) == 0x00  # untouched
