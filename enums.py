from enum import Enum


class OpForm(Enum):
    EXT = 1
    VAR = 2
    SHORT = 3
    LONG = 4


class OperandCount(Enum):
    ZERO = 0
    ONE = 1
    TWO = 2
    VAR = 3


class OpSize(Enum):
    WORD = 0b00
    BYTE = 0b01
    VAR = 0b10


class StatusLineType(Enum):
    score = 0
    time_based = 1
