from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .enums import Opcode, OperandCount, OperandType, OpForm

if TYPE_CHECKING:
    from .zmachine import ZMachine


@dataclass
class Branch:
    condition: bool
    address: int | None = None
    returns: int | None = None


class Instruction:
    """The Instruction Class for decoding and analyzing a ZMachine instruction."""

    def __init__(
        self,
        addr: int,
        opcode: int = 0,
        name: str | None = None,
        operands: list[int] | None = None,
        store: int | None = None,
        branch: Branch | None = None,
        text: str | None = None,
        next_: int = 0,
        optypes: list[OperandType] | None = None,
    ):
        self.addr = addr
        self.opcode = opcode
        self.name = name
        self.store = store
        self.branch = branch
        self.text = text
        self.next_ = next_
        self.operands = operands or []
        self.optypes = optypes or []

    @staticmethod
    def _get_opcode_form(opcode: int) -> OpForm:
        if opcode == 0xBE:
            return OpForm.EXT
        sel = (opcode & 0xC0) >> 6
        if sel == 0b11:
            return OpForm.VAR
        elif sel == 0b10:
            return OpForm.SHORT
        return OpForm.LONG

    @staticmethod
    def _get_operand_count(opcode: int, form: OpForm) -> OperandCount:
        if form == OpForm.VAR:
            if (opcode >> 5) & 1:
                return OperandCount.VAR
            return OperandCount.TWO
        if form == OpForm.SHORT:
            if (opcode >> 4) & 3 == 3:
                return OperandCount.ZERO
            return OperandCount.ONE
        if form == OpForm.EXT:
            return OperandCount.VAR
        return OperandCount.TWO  # LONG

    @classmethod
    def decode(cls, zm: ZMachine, addr: int) -> Instruction:
        raw_code = zm.memory.u8(addr)
        form = cls._get_opcode_form(raw_code)
        count = cls._get_operand_count(raw_code, form)
        optypes = []
        op_pointer = addr + 1

        # Derive opcode number based on form
        if form == OpForm.LONG:
            opcode_num = raw_code & 0x1F  # 2OP range: 0-31
            op_pointer = addr + 1
            optypes = []
            for offset in (6, 5):
                if (raw_code >> offset) & 1:
                    optypes.append(OperandType.VARIABLE)
                else:
                    optypes.append(OperandType.SMALL)
        elif form == OpForm.SHORT:
            if count == OperandCount.ZERO:
                opcode_num = (raw_code & 0x0F) + 176  # 0OP range
            else:
                opcode_num = (raw_code & 0x0F) + 128  # 1OP range
            szbyte = ((raw_code >> 4) & 3) << 6 | 0x3F
            op_pointer = addr + 1
            optypes = OperandType.from_byte(szbyte)
        elif form == OpForm.VAR:
            if count == OperandCount.TWO:
                opcode_num = raw_code & 0x1F  # 2OP range (VAR-encoded)
            else:
                opcode_num = (raw_code & 0x1F) + 224  # VAR range
            szbyte = zm.memory.u8(addr + 1)
            op_pointer = addr + 2
            optypes = OperandType.from_byte(szbyte)
            if raw_code in (0xEC, 0xFA):  # call_vs2, call_vn2
                szbyte2 = zm.memory.u8(addr + 2)
                optypes += OperandType.from_byte(szbyte2)
                op_pointer = addr + 3
        elif form == OpForm.EXT:
            opcode_num = zm.memory.u8(addr + 1) + 1000  # EXT range
            szbyte = zm.memory.u8(addr + 2)
            op_pointer = addr + 3
            optypes = OperandType.from_byte(szbyte)

        opcode = Opcode(opcode_num)

        # Read operands
        read = zm.memory.get_reader(op_pointer)
        operands = []
        for ot in optypes:
            if ot == OperandType.LARGE:
                operands.append(read.word())
            elif ot == OperandType.SMALL or ot == OperandType.VARIABLE:
                operands.append(read.byte())

        # Read store variable
        store = read.byte() if cls.does_store(opcode) else None

        # Read branch data
        if cls.does_branch(opcode, zm.version):
            b = read.byte()
            condition = (b & 0b1000_0000) != 0
            if b & 0b0100_0000:
                # single-byte offset
                offset = b & 0b0011_1111
            else:
                # two-byte offset (14-bit signed)
                offset = ((b & 0b0011_1111) << 8) | read.byte()
                if offset >= 0x2000:
                    offset -= 0x4000

            if offset == 0:
                branch = Branch(condition, None, 0)
            elif offset == 1:
                branch = Branch(condition, None, 1)
            else:
                branch = Branch(condition, read.position + offset - 2, None)
        else:
            branch = None

        # Read inline text
        text = zm.read_zstring(read.position) if cls.does_text(opcode) else None
        text_length = zm.zstring_length(read.position) if text else 0

        name = opcode.zop
        next_ = read.position + text_length

        return cls(
            addr,
            opcode,
            name,
            operands,
            store,
            branch,
            text,
            next_,
            optypes,
        )

    @classmethod
    def does_store(cls, opcode: Opcode) -> bool:
        return opcode in (
            # 2OP
            Opcode.OP2_8,  # or
            Opcode.OP2_9,  # and
            Opcode.OP2_15,  # loadw
            Opcode.OP2_16,  # loadb
            Opcode.OP2_17,  # get_prop
            Opcode.OP2_18,  # get_prop_addr
            Opcode.OP2_19,  # get_next_prop
            Opcode.OP2_20,  # add
            Opcode.OP2_21,  # sub
            Opcode.OP2_22,  # mul
            Opcode.OP2_23,  # div
            Opcode.OP2_24,  # mod
            Opcode.OP2_25,  # call_2s
            # 1OP
            Opcode.OP1_129,  # get_sibling (store + branch)
            Opcode.OP1_130,  # get_child (store + branch)
            Opcode.OP1_131,  # get_parent
            Opcode.OP1_132,  # get_prop_len
            Opcode.OP1_136,  # call_1s
            Opcode.OP1_142,  # load
            Opcode.OP1_143,  # not (v1-4) / call_1n (v5+)
            # VAR
            Opcode.VAR_224,  # call / call_vs
            Opcode.VAR_231,  # random
            Opcode.VAR_236,  # call_vs2
            Opcode.VAR_246,  # read_char
            Opcode.VAR_248,  # not (v5)
            # EXT
            Opcode.EXT_1000,  # save (v5+)
            Opcode.EXT_1001,  # restore (v5+)
            Opcode.EXT_1002,  # log_shift
            Opcode.EXT_1003,  # art_shift
            Opcode.EXT_1004,  # set_font
            Opcode.EXT_1009,  # save_undo
            Opcode.EXT_1010,  # restore_undo
        )

    @classmethod
    def does_branch(cls, opcode: Opcode, version: int) -> bool:
        if opcode in (
            Opcode.OP2_1,  # je
            Opcode.OP2_2,  # jl
            Opcode.OP2_3,  # jg
            Opcode.OP2_4,  # dec_chk
            Opcode.OP2_5,  # inc_chk
            Opcode.OP2_6,  # jin
            Opcode.OP2_7,  # test
            Opcode.OP2_10,  # test_attr
            Opcode.OP1_128,  # jz
            Opcode.OP1_129,  # get_sibling (store + branch)
            Opcode.OP1_130,  # get_child (store + branch)
            Opcode.OP0_189,  # verify
            Opcode.OP0_191,  # piracy
            Opcode.VAR_247,  # scan_table
            Opcode.VAR_255,  # check_arg_count
            Opcode.EXT_1006,  # picture_data
            Opcode.EXT_1024,  # push_stack
            Opcode.EXT_1027,  # make_menu
        ):
            return True
        if opcode == Opcode.OP0_181 and version < 4:  # save (v1-3)
            return True
        return opcode == Opcode.OP0_182 and version < 4  # restore (v1-3)

    @classmethod
    def does_text(cls, opcode: Opcode) -> bool:
        return opcode in (Opcode.OP0_178, Opcode.OP0_179)

    def __repr__(self):
        return (
            f"Instruction(addr=0x{self.addr:x}, opcode={self.name}({self.opcode}), "
            f"operands={self.operands}, optypes={self.optypes}, "
            f"store={self.store}, branch={self.branch}, "
            f"text={self.text!r}, next=0x{self.next_:x})"
        )
