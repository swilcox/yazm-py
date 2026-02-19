from yazm.enums import Opcode, OperandCount, OperandType, OpForm
from yazm.zinstruction import Instruction

# --- _get_opcode_form ---


def test_opcode_form_long():
    # Bytes 0x00-0x7F are LONG form (top 2 bits = 00 or 01)
    assert Instruction._get_opcode_form(0x01) == OpForm.LONG
    assert Instruction._get_opcode_form(0x3F) == OpForm.LONG
    assert Instruction._get_opcode_form(0x7F) == OpForm.LONG


def test_opcode_form_short():
    # Bytes 0x80-0xBF are SHORT form (top 2 bits = 10)
    assert Instruction._get_opcode_form(0x80) == OpForm.SHORT
    assert Instruction._get_opcode_form(0xAF) == OpForm.SHORT
    assert Instruction._get_opcode_form(0xBF) == OpForm.SHORT


def test_opcode_form_var():
    # Bytes 0xC0-0xFF are VAR form (top 2 bits = 11), except 0xBE
    assert Instruction._get_opcode_form(0xC0) == OpForm.VAR
    assert Instruction._get_opcode_form(0xE0) == OpForm.VAR
    assert Instruction._get_opcode_form(0xFF) == OpForm.VAR


def test_opcode_form_ext():
    assert Instruction._get_opcode_form(0xBE) == OpForm.EXT


# --- _get_operand_count ---


def test_operand_count_long():
    # LONG form is always TWO
    assert Instruction._get_operand_count(0x01, OpForm.LONG) == OperandCount.TWO


def test_operand_count_short_one():
    # SHORT form: bits 4-5 != 11 → ONE
    assert Instruction._get_operand_count(0x80, OpForm.SHORT) == OperandCount.ONE  # 0b10_00_xxxx
    assert Instruction._get_operand_count(0x90, OpForm.SHORT) == OperandCount.ONE  # 0b10_01_xxxx
    assert Instruction._get_operand_count(0xA0, OpForm.SHORT) == OperandCount.ONE  # 0b10_10_xxxx


def test_operand_count_short_zero():
    # SHORT form: bits 4-5 == 11 → ZERO
    assert Instruction._get_operand_count(0xB0, OpForm.SHORT) == OperandCount.ZERO  # 0b10_11_xxxx
    assert Instruction._get_operand_count(0xBF, OpForm.SHORT) == OperandCount.ZERO


def test_operand_count_var_two():
    # VAR form: bit 5 == 0 → TWO (encoded as VAR but 2OP opcode)
    assert Instruction._get_operand_count(0xC0, OpForm.VAR) == OperandCount.TWO  # 0b110_0_xxxx


def test_operand_count_var_var():
    # VAR form: bit 5 == 1 → VAR
    assert Instruction._get_operand_count(0xE0, OpForm.VAR) == OperandCount.VAR  # 0b111_0_xxxx


def test_operand_count_ext():
    # EXT is always VAR
    assert Instruction._get_operand_count(0xBE, OpForm.EXT) == OperandCount.VAR


# --- OperandType.from_byte ---


def test_operand_type_from_byte_all_large():
    # 0b00_00_00_11 = three LARGE operands, last pair is OMITTED
    result = OperandType.from_byte(0b00_00_00_11)
    assert result == [OperandType.LARGE, OperandType.LARGE, OperandType.LARGE]


def test_operand_type_from_byte_mixed():
    # 0b00_01_10_11 = LARGE, SMALL, VARIABLE, stop
    result = OperandType.from_byte(0b00_01_10_11)
    assert result == [OperandType.LARGE, OperandType.SMALL, OperandType.VARIABLE]


def test_operand_type_from_byte_single():
    # 0b01_11_xx_xx = SMALL, stop
    result = OperandType.from_byte(0b01_11_00_00)
    assert result == [OperandType.SMALL]


def test_operand_type_from_byte_all_omitted():
    # 0b11_xx_xx_xx = stop immediately
    result = OperandType.from_byte(0xFF)
    assert result == []


def test_operand_type_from_byte_four():
    # 0b00_01_10_00 = LARGE, SMALL, VARIABLE, LARGE
    result = OperandType.from_byte(0b00_01_10_00)
    assert result == [OperandType.LARGE, OperandType.SMALL, OperandType.VARIABLE, OperandType.LARGE]


# --- does_store / does_branch / does_text ---


def test_does_store():
    assert Instruction.does_store(Opcode.OP2_20) is True  # add
    assert Instruction.does_store(Opcode.OP2_21) is True  # sub
    assert Instruction.does_store(Opcode.VAR_224) is True  # call
    assert Instruction.does_store(Opcode.OP1_131) is True  # get_parent
    assert Instruction.does_store(Opcode.OP0_176) is False  # rtrue
    assert Instruction.does_store(Opcode.OP2_1) is False  # je (branch only)


def test_does_branch():
    assert Instruction.does_branch(Opcode.OP2_1, 3) is True  # je
    assert Instruction.does_branch(Opcode.OP1_128, 3) is True  # jz
    assert Instruction.does_branch(Opcode.OP2_7, 3) is True  # test
    assert Instruction.does_branch(Opcode.OP0_189, 3) is True  # verify
    assert Instruction.does_branch(Opcode.OP0_181, 3) is True  # save v3
    assert Instruction.does_branch(Opcode.OP0_181, 5) is False  # save v5 (no branch)
    assert Instruction.does_branch(Opcode.OP0_182, 3) is True  # restore v3
    assert Instruction.does_branch(Opcode.OP0_182, 5) is False  # restore v5
    assert Instruction.does_branch(Opcode.OP2_20, 3) is False  # add (no branch)


def test_does_text():
    assert Instruction.does_text(Opcode.OP0_178) is True  # print
    assert Instruction.does_text(Opcode.OP0_179) is True  # print_ret
    assert Instruction.does_text(Opcode.OP0_176) is False  # rtrue
    assert Instruction.does_text(Opcode.OP2_20) is False  # add


# --- decode with sample zmachine ---


def test_decode_long_form(sample_zmachine):
    """Test decoding a LONG form instruction (je small,small) in actual game data."""
    zm = sample_zmachine
    # Find the initial PC and decode the first instruction
    instr = Instruction.decode(zm, zm.pc)
    assert instr.addr == zm.pc
    assert instr.opcode is not None
    assert instr.name is not None


# =============================================================================
# Additional decode path coverage
# =============================================================================


def test_decode_long_form_both_small(sample_zmachine):
    """LONG form: both operands SMALL (raw_code bits 6,5 both 0)."""
    zm = sample_zmachine
    addr = 0x100
    # raw_code=0x01: LONG, je, both SMALL operands
    zm.memory.write_u8(addr, 0x01)
    zm.memory.write_u8(addr + 1, 5)    # small arg 0
    zm.memory.write_u8(addr + 2, 5)    # small arg 1
    # branch: condition=True, 1-byte, offset=4 → 0b1100_0100 = 0xC4
    zm.memory.write_u8(addr + 3, 0xC4)
    instr = Instruction.decode(zm, addr)
    assert instr.opcode == Opcode.OP2_1  # je
    assert instr.optypes[0] == OperandType.SMALL
    assert instr.optypes[1] == OperandType.SMALL
    assert instr.operands[0] == 5
    assert instr.operands[1] == 5
    assert instr.branch is not None
    assert instr.branch.condition is True


def test_decode_long_form_variable_operand(sample_zmachine):
    """LONG form: first operand VARIABLE (bit 6 set)."""
    zm = sample_zmachine
    addr = 0x100
    # raw_code=0x41: LONG, je, var+small (bit6=1, bit5=0)
    zm.memory.write_u8(addr, 0x41)
    zm.memory.write_u8(addr + 1, 1)    # variable index 1
    zm.memory.write_u8(addr + 2, 5)    # small arg
    zm.memory.write_u8(addr + 3, 0xC4)
    instr = Instruction.decode(zm, addr)
    assert instr.optypes[0] == OperandType.VARIABLE
    assert instr.optypes[1] == OperandType.SMALL


def test_decode_short_form_small_operand(sample_zmachine):
    """SHORT form 1OP with SMALL operand."""
    zm = sample_zmachine
    addr = 0x100
    # raw_code=0x90: SHORT, bits5-4=01 → SMALL, opcode=0+128=jz
    zm.memory.write_u8(addr, 0x90)
    zm.memory.write_u8(addr + 1, 0x05)   # small operand = 5
    # branch: condition=True, 1-byte, offset=2 → 0b1100_0010 = 0xC2
    zm.memory.write_u8(addr + 2, 0xC2)
    instr = Instruction.decode(zm, addr)
    assert instr.opcode == Opcode.OP1_128  # jz
    assert instr.optypes[0] == OperandType.SMALL
    assert instr.operands[0] == 5


def test_decode_short_form_large_operand(sample_zmachine):
    """SHORT form 1OP with LARGE operand."""
    zm = sample_zmachine
    addr = 0x100
    # raw_code=0x80: SHORT, bits5-4=00 → LARGE, opcode=0+128=jz
    zm.memory.write_u8(addr, 0x80)
    zm.memory.write_u16(addr + 1, 0x1234)  # large operand
    zm.memory.write_u8(addr + 3, 0xC3)     # branch byte
    instr = Instruction.decode(zm, addr)
    assert instr.opcode == Opcode.OP1_128
    assert instr.optypes[0] == OperandType.LARGE
    assert instr.operands[0] == 0x1234


def test_decode_short_form_zero_operands(sample_zmachine):
    """SHORT form 0OP (rtrue)."""
    zm = sample_zmachine
    addr = 0x100
    # raw_code=0xB0: SHORT, bits5-4=11 → ZERO ops, opcode=0+176=rtrue
    zm.memory.write_u8(addr, 0xB0)
    instr = Instruction.decode(zm, addr)
    assert instr.opcode == Opcode.OP0_176  # rtrue
    assert len(instr.operands) == 0


def test_decode_var_form_2op(sample_zmachine):
    """VAR form encoding a 2OP (bit5=0)."""
    zm = sample_zmachine
    addr = 0x100
    # raw_code=0xC1: VAR, bit5=0 → 2OP, opcode=1=je
    # szbyte=0b0111_1111: SMALL(01), SMALL(01), OMIT(11) → 2 small args
    zm.memory.write_u8(addr, 0xC1)
    zm.memory.write_u8(addr + 1, 0b0101_1111)  # SMALL, SMALL, OMIT
    zm.memory.write_u8(addr + 2, 5)             # first arg
    zm.memory.write_u8(addr + 3, 5)             # second arg
    zm.memory.write_u8(addr + 4, 0xC4)          # branch
    instr = Instruction.decode(zm, addr)
    assert instr.opcode == Opcode.OP2_1  # je (2OP opcode 1)
    assert len(instr.operands) == 2


def test_decode_var_form_var_count(sample_zmachine):
    """VAR form encoding a VAR op (call)."""
    zm = sample_zmachine
    addr = 0x100
    # raw_code=0xE0: VAR, bit5=1 → VAR, opcode=0+224=call
    # szbyte=0b0011_1111: LARGE(00), OMIT(11) → 1 large arg
    zm.memory.write_u8(addr, 0xE0)
    zm.memory.write_u8(addr + 1, 0b0011_1111)
    zm.memory.write_u16(addr + 2, 0x0080)  # packed address
    zm.memory.write_u8(addr + 4, 1)        # store variable
    instr = Instruction.decode(zm, addr)
    assert instr.opcode == Opcode.VAR_224  # call
    assert instr.store == 1
    assert len(instr.operands) == 1


def test_decode_ext_form(sample_zmachine):
    """EXT form (save_undo = opcode 9)."""
    zm = sample_zmachine
    addr = 0x100
    zm.memory.write_u8(addr, 0xBE)      # EXT marker
    zm.memory.write_u8(addr + 1, 0x09)  # opcode 9 → EXT_1009 = save_undo
    zm.memory.write_u8(addr + 2, 0xFF)  # szbyte: all OMIT → 0 operands
    zm.memory.write_u8(addr + 3, 1)     # store variable (save_undo stores result)
    instr = Instruction.decode(zm, addr)
    assert instr.opcode == Opcode.EXT_1009  # save_undo
    assert instr.store == 1
    assert len(instr.operands) == 0


def test_decode_branch_returns_zero(sample_zmachine):
    """Branch with offset=0 → Branch(returns=0)."""
    zm = sample_zmachine
    addr = 0x100
    zm.memory.write_u8(addr, 0x80)      # SHORT jz with LARGE op
    zm.memory.write_u16(addr + 1, 1)    # operand
    zm.memory.write_u8(addr + 3, 0xC0)  # condition=True, 1-byte, offset=0 → returns 0
    instr = Instruction.decode(zm, addr)
    assert instr.branch is not None
    assert instr.branch.returns == 0


def test_decode_branch_returns_one(sample_zmachine):
    """Branch with offset=1 → Branch(returns=1)."""
    zm = sample_zmachine
    addr = 0x100
    zm.memory.write_u8(addr, 0x80)
    zm.memory.write_u16(addr + 1, 1)
    zm.memory.write_u8(addr + 3, 0xC1)  # offset=1 → returns 1
    instr = Instruction.decode(zm, addr)
    assert instr.branch is not None
    assert instr.branch.returns == 1


def test_decode_two_byte_branch(sample_zmachine):
    """Two-byte branch offset (bit6=0)."""
    zm = sample_zmachine
    addr = 0x100
    zm.memory.write_u8(addr, 0x80)
    zm.memory.write_u16(addr + 1, 1)    # operand
    # branch: condition=True, 2-byte offset → bit7=1, bit6=0, high bits=0
    zm.memory.write_u8(addr + 3, 0x80)  # condition=True, 2-byte, high 6 bits = 0
    zm.memory.write_u8(addr + 4, 0x10)  # low byte: offset = 16
    instr = Instruction.decode(zm, addr)
    assert instr.branch is not None
    assert instr.branch.address is not None


def test_decode_two_byte_branch_negative(sample_zmachine):
    """Two-byte branch with negative offset (>= 0x2000)."""
    zm = sample_zmachine
    addr = 0x100
    zm.memory.write_u8(addr, 0x80)
    zm.memory.write_u16(addr + 1, 1)
    # offset = 0x3FFD → >= 0x2000 → 0x3FFD - 0x4000 = -3
    zm.memory.write_u8(addr + 3, 0xBF)  # condition=True, 2-byte, high 6 bits = 0x3F
    zm.memory.write_u8(addr + 4, 0xFD)  # low byte → offset = 0x3FFD
    instr = Instruction.decode(zm, addr)
    assert instr.branch is not None
    # address should be negative offset applied from read.position
    assert instr.branch.address is not None


def test_instruction_repr():
    """__repr__ produces a useful string."""
    instr = Instruction(addr=0x50, opcode=Opcode.OP2_20, name="add", next_=0x100)
    r = repr(instr)
    assert "add" in r
    assert "0x50" in r
