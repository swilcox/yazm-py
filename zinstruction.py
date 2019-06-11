from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from enums import Opcode, Operand, OperandType
if TYPE_CHECKING:
    from zmachine import ZMachine


def _btm_4(num: int) -> int:
    return num & 0b0000_1111


def _btm_5(num: int) -> int:
    return num & 0b0001_1111


def _get_types(bytes_: bytes) -> List[OperandType]:
    # TODO: more complex stuff here !!!!
    return [OperandType(b) for b in bytes_]


def _get_opcode(code: int, offset: int) -> Opcode:
    num = code + offset
    # TODO: verify it's a real opcode?
    return Opcode(num)


@dataclass
class Branch:
    condition: int
    address: int = None
    returns: int = None


class Instruction:
    """The Instruction Class for decoding and analyzing a ZMachine instruction."""

    def __init__(self, addr: int, opcode: int = 0, name: str = None, operands: List[int] = None, store: str = None, branch: Branch = None, text: str = None, next_: int = 0):
        self.addr = addr
        self.opcode = opcode
        self._opcode = '' #lookup Opcode
        self.name = name
        self.store = store
        self.branch = branch
        self.text = text
        self.next_ = next_        

    @classmethod
    def decode(cls, zm: ZMachine, addr: int) -> Instruction:
        read = zm.memory.get_reader(addr)
        first = read.byte()
        if first == 0xBE:
            opcode, optypes = (_get_opcode(read.byte(), 1000), _get_types([read.byte()]))
        elif 0x00 <= first <= 0x1F:
            opcode, optypes = (_get_opcode(_btm_5(first), 0), [OperandType.SMALL, OperandType.SMALL])
        elif 0x20 <= first <= 0x3F:
            opcode, optypes = (_get_opcode(_btm_5(first), 0), [OperandType.SMALL, OperandType.VARIABLE])
        elif 0x40 <= first <= 0x5F:
            opcode, optypes = (_get_opcode(_btm_5(first), 0), [OperandType.VARIABLE, OperandType.SMALL])
        elif 0x60 <= first <= 0x7F:
            opcode, optypes = (_get_opcode(_btm_5(first), 0), [OperandType.VARIABLE, OperandType.VARIABLE])
        elif 0x80 <= first <= 0x8F:
            opcode, optypes = (_get_opcode(_btm_4(first), 128), [OperandType.LARGE])
        elif 0x90 <= first <= 0x9F:
            opcode, optypes = (_get_opcode(_btm_4(first), 128), [OperandType.SMALL])
        elif 0xA0 <= first <= 0xAF:
            opcode, optypes = (_get_opcode(_btm_4(first), 128), [OperandType.VARIABLE])
        elif 0xB0 <= first <= 0xBF:
            opcode, optypes = (_get_opcode(_btm_4(first), 176), [])
        elif 0xC0 <= first <= 0xDF:
            opcode, optypes = (_get_opcode(_btm_5(first), 0), _get_types([read.byte()]))
        elif 0xE0 <= first <= 0xFF:
            opcode = _get_opcode(_btm_5(first), 224)
            if opcode in [Opcode.VAR_236, Opcode.VAR_250]:
                optypes = _get_types([read.byte(), read.bytes()])
            else:
                optypes = _get_types([read.byte()])
        else:
            raise Exception('unknown opcode: ' + str(opcode))

        operands = [read.word() if ot == OperandType.LARGE else read.byte() for ot in optypes]
        store = read.byte() if cls.does_store(opcode) else None
        if cls.does_branch(opcode, zm.version):
            b = read.byte()
            condition = b & 0b1000_0000 != 0
            offset = b & 0b0011_1111 if b & 0b0100_0000 != 0 else ((b & 0b0011_1111) << 8) + read.byte()
            address = (read.position() + offset - 16384 - 2) if offset > (16384 / 2) else (read.position() + offset - 2)
            if offset == 0:
                branch = Branch(condition, None, 0)
            elif offset == 1:
                branch = Branch(condition, None, 1)
            else:
                branch = Branch(condition, address, None)
        else:
            branch = None
        
        text = zm.read_zstring(read.position) if cls.does_text(opcode) else None
        text_length = zm.zstring_length(read.position) if text else 0

        name = cls.get_name(opcode, zm.version)
        next_ = read.position + text_length

        return cls(
            addr,
            opcode,
            name,
            operands,
            store,
            branch,
            text,
            next_
        )

    @classmethod
    def does_store(cls, opcode: Opcode) -> bool:
        return opcode in (
            Opcode.OP2_8, Opcode.OP2_9, Opcode.OP2_15, Opcode.OP2_16
        )

    @classmethod
    def does_branch(cls, opcode: Opcode, version: int) -> bool:
        if opcode in (Opcode.OP2_1, Opcode.OP2_2, Opcode.OP2_3, Opcode.OP2_4, Opcode.OP2_5, Opcode.OP2_6, Opcode.OP2_7, Opcode.OP2_10, Opcode.OP1_128, Opcode.OP1_129, Opcode.OP1_130, Opcode.OP0_189, Opcode.OP0_191, Opcode.VAR_247, Opcode.VAR_255, Opcode.EXT_1006, Opcode.EXT_1024, Opcode.EXT_1027):
            return True
        elif opcode == Opcode.OP0_181 and version < 4:
            return True
        elif opcode == Opcode.OP0_182 and version < 4:
            return True
        return False

    @classmethod
    def does_text(cls, opcode: Opcode) -> bool:
        return opcode in (Opcode.OP0_178, Opcode.OP0_179)

    @classmethod
    def get_name(self, opcode: Opcode, version: int) -> str:
        return ''

    @property
    def advances(self) -> bool:
        return False

    @property    
    def does_call(self, version: int) -> bool:
        return False

    @property
    def should_advance(self, version: int) -> bool:
        return False

    def __hash__(self):
        return 0
    
    def __eq__(self, other) -> bool:
        return self.addr == other.addr
    
    #TODO: __repr__ and/or __str__
