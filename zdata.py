class ZData(bytearray):
    """ZData Class."""
   
    def u16(self, index: int) -> int:
        return self[index] << 8 | self[index + 1]
    
    def u8(self, index: int) -> int:
        return self[index]

    def write_u16(self, index: int, value: int):
        self[index] = (value & 0xFF00) >> 8
        self[index + 1] = value & 0x00FF
    
    def write_u8(self, index: int, value: int):
        self[index] = value
