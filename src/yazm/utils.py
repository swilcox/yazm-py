def from_u16_to_i16(value: int) -> int:
    return value - 0x10000 if value >= 0x8000 else value
