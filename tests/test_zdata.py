from yazm.zdata import ZData


def test_zdata_reads():
    bs = bytearray([1, 2])
    zdata = ZData(bs)
    assert(zdata[0] == 1)
    assert(zdata[1] == 2)
    assert(zdata.u8(0) == zdata[0])
    assert(zdata.u8(1) == zdata[1])
    assert(zdata.u16(0) == 258)


def test_zdata_writes():
    bs = bytearray([1,2])
    zdata = ZData(bs)
    assert(zdata.u16(0) == 258)
    zdata.write_u16(0, 42042)
    assert(zdata.u16(0) == 42042)
    assert(zdata.u8(0) == 164)
    assert(zdata.u8(1) == 58)
