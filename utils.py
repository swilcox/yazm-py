def from_u16_to_i16(value: int) -> int:
    if value & 0b1000_0000_0000_0000:
        return -1 * (value & 0b0111_1111_1111_1111)
    else:
        return value
