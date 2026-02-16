"""Tests for opcode handler functions in ops.py."""

import pytest

from yazm.enums import Opcode
from yazm.frame import Frame
from yazm.zmachine import ZMachine
from yazm.zinstruction import Branch, Instruction

from ._sample_data import ZSAMPLE_DATA


def make_zm():
    """Create a ZMachine with a frame that has locals and stack space."""
    zm = ZMachine(ZSAMPLE_DATA)
    # Set up a frame with 5 locals for variable tests
    zm.frames.append(Frame(resume=0, store=None, locals_=[0, 0, 0, 0, 0], arguments=[]))
    return zm


def make_instr(opcode=Opcode.OP2_20, store=0, next_=0x100, branch=None):
    """Create a minimal Instruction for testing."""
    return Instruction(addr=0x50, opcode=opcode, name="test", store=store, next_=next_, branch=branch)


# --- Arithmetic ---

from yazm.ops import op_add, op_sub, op_mul, op_div, op_mod


def test_add_basic():
    zm = make_zm()
    instr = make_instr(store=1)
    op_add(zm, instr, [3, 5])
    assert zm.read_variable(1) == 8


def test_add_overflow():
    zm = make_zm()
    instr = make_instr(store=1)
    op_add(zm, instr, [0x7FFF, 1])  # 32767 + 1 = -32768 as signed
    assert zm.read_variable(1) == 0x8000


def test_add_negative():
    zm = make_zm()
    instr = make_instr(store=1)
    # -1 + -1 = -2 → 0xFFFE
    op_add(zm, instr, [0xFFFF, 0xFFFF])
    assert zm.read_variable(1) == 0xFFFE


def test_sub_basic():
    zm = make_zm()
    instr = make_instr(store=1)
    op_sub(zm, instr, [10, 3])
    assert zm.read_variable(1) == 7


def test_sub_negative_result():
    zm = make_zm()
    instr = make_instr(store=1)
    op_sub(zm, instr, [3, 10])  # 3 - 10 = -7
    result = zm.read_variable(1)
    from yazm.utils import from_u16_to_i16

    assert from_u16_to_i16(result) == -7


def test_mul_basic():
    zm = make_zm()
    instr = make_instr(store=1)
    op_mul(zm, instr, [6, 7])
    assert zm.read_variable(1) == 42


def test_mul_negative():
    zm = make_zm()
    instr = make_instr(store=1)
    # -3 * 4 = -12
    op_mul(zm, instr, [0xFFFD, 4])
    from yazm.utils import from_u16_to_i16

    assert from_u16_to_i16(zm.read_variable(1)) == -12


def test_div_basic():
    zm = make_zm()
    instr = make_instr(store=1)
    op_div(zm, instr, [10, 3])
    assert zm.read_variable(1) == 3  # truncated toward zero


def test_div_negative_truncates_toward_zero():
    zm = make_zm()
    instr = make_instr(store=1)
    # -7 / 2 = -3 (truncated toward zero, not -4)
    op_div(zm, instr, [0xFFF9, 2])  # -7 as u16
    from yazm.utils import from_u16_to_i16

    assert from_u16_to_i16(zm.read_variable(1)) == -3


def test_div_by_zero():
    zm = make_zm()
    instr = make_instr(store=1)
    with pytest.raises(Exception, match="Division by zero"):
        op_div(zm, instr, [10, 0])


def test_mod_basic():
    zm = make_zm()
    instr = make_instr(store=1)
    op_mod(zm, instr, [10, 3])
    assert zm.read_variable(1) == 1


def test_mod_sign_follows_dividend():
    zm = make_zm()
    instr = make_instr(store=1)
    # -7 mod 2 = -1 (sign follows dividend)
    op_mod(zm, instr, [0xFFF9, 2])
    from yazm.utils import from_u16_to_i16

    assert from_u16_to_i16(zm.read_variable(1)) == -1


def test_mod_by_zero():
    zm = make_zm()
    instr = make_instr(store=1)
    with pytest.raises(Exception, match="Division by zero"):
        op_mod(zm, instr, [10, 0])


# --- Logical ---

from yazm.ops import op_and, op_not, op_or


def test_and():
    zm = make_zm()
    instr = make_instr(store=1)
    op_and(zm, instr, [0xFF00, 0x0FF0])
    assert zm.read_variable(1) == 0x0F00


def test_or():
    zm = make_zm()
    instr = make_instr(store=1)
    op_or(zm, instr, [0xFF00, 0x00FF])
    assert zm.read_variable(1) == 0xFFFF


def test_not():
    zm = make_zm()
    instr = make_instr(store=1)
    op_not(zm, instr, [0x00FF])
    assert zm.read_variable(1) == 0xFF00


# --- Control Flow ---

from yazm.ops import op_jump, op_nop, op_quit, op_ret, op_ret_popped, op_rfalse, op_rtrue


def test_rtrue():
    zm = make_zm()
    # Add another frame on top so rtrue pops it and stores into the frame with locals
    zm.frames.append(Frame(resume=0x200, store=1, locals_=[], arguments=[]))
    initial_frame_count = len(zm.frames)
    op_rtrue(zm, make_instr(), [])
    assert len(zm.frames) == initial_frame_count - 1
    assert zm.pc == 0x200
    assert zm.read_variable(1) == 1  # rtrue stores 1


def test_rfalse():
    zm = make_zm()
    zm.frames.append(Frame(resume=0x200, store=1, locals_=[], arguments=[]))
    initial_frame_count = len(zm.frames)
    op_rfalse(zm, make_instr(), [])
    assert len(zm.frames) == initial_frame_count - 1
    assert zm.pc == 0x200
    assert zm.read_variable(1) == 0  # rfalse stores 0


def test_ret():
    zm = make_zm()
    zm.frames.append(Frame(resume=0x200, store=1, locals_=[], arguments=[]))
    op_ret(zm, make_instr(), [42])
    assert zm.read_variable(1) == 42
    assert zm.pc == 0x200


def test_ret_popped():
    zm = make_zm()
    # Add a frame whose stack has a value, then ret_popped pops it as return value
    zm.frames.append(Frame(resume=0x300, store=2, locals_=[], arguments=[]))
    zm.stack_push(77)
    op_ret_popped(zm, make_instr(), [])
    # The frame was popped and 77 was returned, stored into var 2 of the frame below
    assert zm.read_variable(2) == 77


def test_jump_forward():
    zm = make_zm()
    instr = make_instr(next_=0x100)
    op_jump(zm, instr, [5])  # offset 5
    assert zm.pc == 0x100 + 5 - 2


def test_jump_backward():
    zm = make_zm()
    instr = make_instr(next_=0x100)
    # -3 as u16 = 0xFFFD
    op_jump(zm, instr, [0xFFFD])
    assert zm.pc == 0x100 - 3 - 2


def test_quit():
    zm = make_zm()
    op_quit(zm, make_instr(), [])
    assert zm.running is False


def test_nop():
    zm = make_zm()
    instr = make_instr(next_=0x200)
    op_nop(zm, instr, [])
    assert zm.pc == 0x200


# --- Branch ---

from yazm.ops import op_je, op_jg, op_jl, op_jz, op_test


def test_jz_true():
    zm = make_zm()
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(branch=branch, next_=0x100)
    op_jz(zm, instr, [0])
    assert zm.pc == 0x300


def test_jz_false():
    zm = make_zm()
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(branch=branch, next_=0x100)
    op_jz(zm, instr, [5])
    assert zm.pc == 0x100


def test_je_match():
    zm = make_zm()
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(branch=branch, next_=0x100)
    op_je(zm, instr, [5, 3, 5, 7])
    assert zm.pc == 0x300


def test_je_no_match():
    zm = make_zm()
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(branch=branch, next_=0x100)
    op_je(zm, instr, [5, 3, 4, 7])
    assert zm.pc == 0x100


def test_jl_true():
    zm = make_zm()
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(branch=branch, next_=0x100)
    # 3 < 10
    op_jl(zm, instr, [3, 10])
    assert zm.pc == 0x300


def test_jl_signed():
    zm = make_zm()
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(branch=branch, next_=0x100)
    # -1 (0xFFFF) < 1
    op_jl(zm, instr, [0xFFFF, 1])
    assert zm.pc == 0x300


def test_jg_true():
    zm = make_zm()
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(branch=branch, next_=0x100)
    op_jg(zm, instr, [10, 3])
    assert zm.pc == 0x300


def test_test_all_bits_set():
    zm = make_zm()
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(branch=branch, next_=0x100)
    op_test(zm, instr, [0xFF, 0x0F])
    assert zm.pc == 0x300


def test_test_not_all_bits():
    zm = make_zm()
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(branch=branch, next_=0x100)
    op_test(zm, instr, [0xF0, 0x0F])
    assert zm.pc == 0x100


def test_branch_inverted_condition():
    """Branch when condition is False and result is False."""
    zm = make_zm()
    branch = Branch(condition=False, address=0x300)
    instr = make_instr(branch=branch, next_=0x100)
    op_jz(zm, instr, [5])  # 5 != 0, result is False
    # condition=False, result=False → do_branch = True
    assert zm.pc == 0x300


# --- Stack ops ---

from yazm.ops import op_pull, op_push


def test_push():
    zm = make_zm()
    instr = make_instr(next_=0x100)
    op_push(zm, instr, [42])
    assert zm.stack_peek() == 42
    assert zm.pc == 0x100


def test_pull():
    zm = make_zm()
    zm.stack_push(99)
    instr = make_instr(next_=0x100)
    # pull into variable 1 (local 0)
    op_pull(zm, instr, [1])
    assert zm.read_variable(1) == 99
    assert zm.pc == 0x100


# --- Variable ops ---

from yazm.ops import op_dec, op_dec_chk, op_inc, op_inc_chk, op_load, op_store


def test_inc():
    zm = make_zm()
    zm.write_variable(1, 10)
    instr = make_instr(next_=0x100)
    op_inc(zm, instr, [1])
    assert zm.read_variable(1) == 11
    assert zm.pc == 0x100


def test_inc_wraps():
    zm = make_zm()
    zm.write_variable(1, 0x7FFF)  # 32767
    instr = make_instr(next_=0x100)
    op_inc(zm, instr, [1])
    assert zm.read_variable(1) == 0x8000  # -32768 as u16


def test_dec():
    zm = make_zm()
    zm.write_variable(1, 10)
    instr = make_instr(next_=0x100)
    op_dec(zm, instr, [1])
    assert zm.read_variable(1) == 9


def test_dec_wraps():
    zm = make_zm()
    zm.write_variable(1, 0)
    instr = make_instr(next_=0x100)
    op_dec(zm, instr, [1])
    assert zm.read_variable(1) == 0xFFFF  # -1 as u16


def test_inc_chk_branch():
    zm = make_zm()
    zm.write_variable(1, 5)
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(branch=branch, next_=0x100)
    # inc var 1 (→6), check if > 5 → True
    op_inc_chk(zm, instr, [1, 5])
    assert zm.read_variable(1) == 6
    assert zm.pc == 0x300


def test_inc_chk_no_branch():
    zm = make_zm()
    zm.write_variable(1, 3)
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(branch=branch, next_=0x100)
    # inc var 1 (→4), check if > 5 → False
    op_inc_chk(zm, instr, [1, 5])
    assert zm.read_variable(1) == 4
    assert zm.pc == 0x100


def test_dec_chk_branch():
    zm = make_zm()
    zm.write_variable(1, 5)
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(branch=branch, next_=0x100)
    # dec var 1 (→4), check if < 5 → True
    op_dec_chk(zm, instr, [1, 5])
    assert zm.read_variable(1) == 4
    assert zm.pc == 0x300


def test_dec_chk_no_branch():
    zm = make_zm()
    zm.write_variable(1, 10)
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(branch=branch, next_=0x100)
    # dec var 1 (→9), check if < 5 → False
    op_dec_chk(zm, instr, [1, 5])
    assert zm.read_variable(1) == 9
    assert zm.pc == 0x100


def test_store():
    zm = make_zm()
    zm.write_variable(1, 0)
    instr = make_instr(next_=0x100)
    op_store(zm, instr, [1, 42])
    assert zm.read_variable(1) == 42


def test_load():
    zm = make_zm()
    zm.write_variable(1, 77)
    instr = make_instr(store=2)
    op_load(zm, instr, [1])
    assert zm.read_variable(2) == 77


# --- Memory ops ---

from yazm.ops import op_loadb, op_loadw, op_storeb, op_storew


def test_loadw():
    zm = make_zm()
    # Write a known value to memory
    zm.memory.write_u16(0x100, 0xABCD)
    instr = make_instr(store=1)
    op_loadw(zm, instr, [0x100, 0])  # base 0x100, index 0
    assert zm.read_variable(1) == 0xABCD


def test_loadw_with_index():
    zm = make_zm()
    zm.memory.write_u16(0x104, 0x1234)
    instr = make_instr(store=1)
    op_loadw(zm, instr, [0x100, 2])  # base + 2*2 = 0x104
    assert zm.read_variable(1) == 0x1234


def test_loadb():
    zm = make_zm()
    zm.memory.write_u8(0x100, 0x42)
    instr = make_instr(store=1)
    op_loadb(zm, instr, [0x100, 0])
    assert zm.read_variable(1) == 0x42


def test_storew():
    zm = make_zm()
    instr = make_instr(next_=0x200)
    op_storew(zm, instr, [0x100, 0, 0xBEEF])
    assert zm.memory.u16(0x100) == 0xBEEF
    assert zm.pc == 0x200


def test_storeb():
    zm = make_zm()
    instr = make_instr(next_=0x200)
    op_storeb(zm, instr, [0x100, 0, 0x42])
    assert zm.memory.u8(0x100) == 0x42
    assert zm.pc == 0x200


# --- Dispatch table coverage ---

from yazm.ops import DISPATCH_TABLE


def test_dispatch_table_has_all_common_opcodes():
    """Verify key opcodes are mapped."""
    expected = [
        Opcode.OP2_1,  # je
        Opcode.OP2_20,  # add
        Opcode.OP2_21,  # sub
        Opcode.OP2_22,  # mul
        Opcode.OP2_23,  # div
        Opcode.OP0_176,  # rtrue
        Opcode.OP0_177,  # rfalse
        Opcode.VAR_224,  # call
        Opcode.VAR_232,  # push
        Opcode.VAR_233,  # pull
    ]
    for op in expected:
        assert op in DISPATCH_TABLE, f"{op} missing from DISPATCH_TABLE"
