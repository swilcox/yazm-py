from __future__ import annotations


class ZData(bytearray):
    """ZData Class."""

    class ZDataWriter:
        def __init__(self, zd: ZData, addr: int):
            self.current_addr = addr
            self.zd = zd

        def byte(self, value: int):
            self.zd.write_u8(self.current_addr, value)
            self.current_addr += 1

        def word(self, value: int):
            self.zd.write_u16(self.current_addr, value)
            self.current_addr += 2

        @property
        def position(self) -> int:
            return self.current_addr

    class ZDataReader:
        def __init__(self, zd: ZData, addr: int):
            self.current_addr = addr
            self.zd = zd

        def byte(self) -> int:
            result = self.zd.u8(self.current_addr)
            self.current_addr += 1
            return result

        def word(self) -> int:
            result = self.zd.u16(self.current_addr)
            self.current_addr += 2
            return result

        @property
        def position(self) -> int:
            return self.current_addr

    def u16(self, index: int) -> int:
        return self[index] << 8 | self[index + 1]

    def u8(self, index: int) -> int:
        return self[index]

    def write_u16(self, index: int, value: int):
        self[index] = (value & 0xFF00) >> 8
        self[index + 1] = value & 0x00FF

    def write_u8(self, index: int, value: int):
        self[index] = value

    def get_writer(self, addr: int) -> ZData.ZDataWriter:
        return self.ZDataWriter(self, addr)

    def get_reader(self, addr: int) -> ZData.ZDataReader:
        return self.ZDataReader(self, addr)
