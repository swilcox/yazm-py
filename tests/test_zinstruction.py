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
