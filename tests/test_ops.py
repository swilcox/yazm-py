"""Tests for opcode handler functions in ops.py."""

import pytest

from yazm.enums import Opcode
from yazm.frame import Frame
from yazm.zinstruction import Branch, Instruction
from yazm.zmachine import ZMachine

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

from yazm.ops import op_add, op_div, op_mod, op_mul, op_sub


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


# =============================================================================
# Additional coverage tests
# =============================================================================

import os


class _CapUI:
    """Minimal UI mock: captures output, provides canned input."""

    def __init__(self, input_text="north", filename=""):
        self.output = []
        self.input_text = input_text
        self.filename = filename

    def zoutput(self, text: str):
        self.output.append(text)

    def zoutput_object(self, text: str, highlight: bool = False, is_location: bool = False):
        self.output.append(text)

    def set_status_bar(self, left: str, right: str):
        pass

    def zinput(self) -> str:
        return self.input_text

    def zinput_filename(self, prompt: str) -> str:
        return self.filename


def make_zm_cap(input_text="north", filename=""):
    """ZMachine with captured UI and a pre-pushed working frame."""
    zm = ZMachine(ZSAMPLE_DATA)
    zm.ui = _CapUI(input_text=input_text, filename=filename)
    zm.frames.append(Frame(resume=0, store=None, locals_=[0, 0, 0, 0, 0], arguments=[]))
    return zm


# --- op_call edge case ---

from yazm.ops import op_call


def test_call_empty_args():
    """op_call with no args stores 0 (addr=0 path)."""
    zm = make_zm()
    instr = make_instr(opcode=Opcode.VAR_224, store=1)
    op_call(zm, instr, [])
    assert zm.read_variable(1) == 0


# --- op_jin ---

from yazm.ops import op_jin


def test_jin_true():
    zm = make_zm()
    total = zm.get_total_object_count()
    obj_a, obj_b = total - 1, total - 2
    zm.remove_obj(obj_a)
    zm.insert_obj(obj_a, obj_b)
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(opcode=Opcode.OP2_6, branch=branch, next_=0x100)
    op_jin(zm, instr, [obj_a, obj_b])
    assert zm.pc == 0x300


def test_jin_false():
    zm = make_zm()
    total = zm.get_total_object_count()
    obj_a, obj_b = total - 1, total - 2
    zm.remove_obj(obj_a)
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(opcode=Opcode.OP2_6, branch=branch, next_=0x100)
    op_jin(zm, instr, [obj_a, obj_b])
    assert zm.pc == 0x100


# --- op_test_attr ---

from yazm.ops import op_test_attr


def test_test_attr_true_op():
    zm = make_zm()
    total = zm.get_total_object_count()
    obj = total - 1
    zm.set_attr(obj, 3)
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(opcode=Opcode.OP2_10, branch=branch, next_=0x100)
    op_test_attr(zm, instr, [obj, 3])
    assert zm.pc == 0x300


def test_test_attr_false_op():
    zm = make_zm()
    total = zm.get_total_object_count()
    obj = total - 1
    zm.clear_attr(obj, 3)
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(opcode=Opcode.OP2_10, branch=branch, next_=0x100)
    op_test_attr(zm, instr, [obj, 3])
    assert zm.pc == 0x100


# --- op_sound_effect ---

from yazm.ops import op_sound_effect


def test_sound_effect():
    zm = make_zm()
    instr = make_instr(next_=0x100)
    op_sound_effect(zm, instr, [])
    assert zm.pc == 0x100


# --- Print ops ---

from yazm.ops import op_new_line, op_print, op_print_addr, op_print_char
from yazm.ops import op_print_num, op_print_obj, op_print_paddr, op_print_ret


def test_print_op():
    zm = make_zm_cap()
    instr = Instruction(addr=0x50, opcode=Opcode.OP0_178, name="print", next_=0x100, text="Hello")
    op_print(zm, instr, [])
    assert zm.ui.output == ["Hello"]
    assert zm.pc == 0x100


def test_print_ret_op():
    zm = make_zm_cap()
    zm.frames.append(Frame(resume=0x200, store=1, locals_=[0], arguments=[]))
    instr = Instruction(addr=0x50, opcode=Opcode.OP0_179, name="print_ret", next_=0x100, text="Bye")
    op_print_ret(zm, instr, [])
    assert any("Bye" in t for t in zm.ui.output)
    assert zm.pc == 0x200


def test_new_line_op():
    zm = make_zm_cap()
    instr = make_instr(next_=0x100)
    op_new_line(zm, instr, [])
    assert zm.ui.output[0] == "\n"
    assert zm.pc == 0x100


def test_print_num_positive():
    zm = make_zm_cap()
    instr = make_instr(next_=0x100)
    op_print_num(zm, instr, [42])
    assert zm.ui.output == ["42"]


def test_print_num_negative():
    zm = make_zm_cap()
    instr = make_instr(next_=0x100)
    op_print_num(zm, instr, [0xFFFF])  # -1 as signed u16
    assert zm.ui.output == ["-1"]


def test_print_char_op():
    zm = make_zm_cap()
    instr = make_instr(next_=0x100)
    op_print_char(zm, instr, [65])  # ZSCII 65 = 'A'
    assert zm.ui.output[0] == "A"
    assert zm.pc == 0x100


def test_print_obj_op():
    zm = make_zm_cap()
    instr = make_instr(next_=0x100)
    op_print_obj(zm, instr, [1])
    assert len(zm.ui.output) > 0
    assert zm.pc == 0x100


def test_print_addr_op():
    zm = make_zm_cap()
    addr = zm.get_object_prop_table_addr(1) + 1  # object 1's name zstring
    instr = make_instr(next_=0x100)
    op_print_addr(zm, instr, [addr])
    assert zm.pc == 0x100


def test_print_paddr_op():
    zm = make_zm_cap()
    prop_addr = zm.get_object_prop_table_addr(1) + 1
    packed = prop_addr // 2  # v3: packed = byte_addr / 2
    instr = make_instr(next_=0x100)
    op_print_paddr(zm, instr, [packed])
    assert zm.pc == 0x100


# --- Object ops ---

from yazm.ops import (
    op_clear_attr,
    op_get_child,
    op_get_parent,
    op_get_sibling,
    op_insert_obj,
    op_remove_obj,
    op_set_attr,
)


def test_set_attr_op():
    zm = make_zm()
    total = zm.get_total_object_count()
    obj = total - 1
    zm.clear_attr(obj, 2)
    instr = make_instr(next_=0x100)
    op_set_attr(zm, instr, [obj, 2])
    assert zm.test_attr(obj, 2) == 1
    assert zm.pc == 0x100


def test_clear_attr_op():
    zm = make_zm()
    total = zm.get_total_object_count()
    obj = total - 1
    zm.set_attr(obj, 2)
    instr = make_instr(next_=0x100)
    op_clear_attr(zm, instr, [obj, 2])
    assert zm.test_attr(obj, 2) == 0
    assert zm.pc == 0x100


def test_insert_obj_op():
    zm = make_zm()
    total = zm.get_total_object_count()
    obj_a, obj_b = total - 1, total - 2
    zm.remove_obj(obj_a)
    instr = make_instr(next_=0x100)
    op_insert_obj(zm, instr, [obj_a, obj_b])
    assert zm.get_parent(obj_a) == obj_b
    assert zm.pc == 0x100


def test_remove_obj_op():
    zm = make_zm()
    total = zm.get_total_object_count()
    obj_a, obj_b = total - 1, total - 2
    zm.remove_obj(obj_a)
    zm.insert_obj(obj_a, obj_b)
    instr = make_instr(next_=0x100)
    op_remove_obj(zm, instr, [obj_a])
    assert zm.get_parent(obj_a) == 0
    assert zm.pc == 0x100


def test_get_child_with_child():
    zm = make_zm()
    total = zm.get_total_object_count()
    obj_a, obj_b = total - 1, total - 2
    zm.remove_obj(obj_a)
    zm.insert_obj(obj_a, obj_b)
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(store=1, branch=branch, next_=0x100)
    op_get_child(zm, instr, [obj_b])
    assert zm.read_variable(1) == obj_a
    assert zm.pc == 0x300


def test_get_child_no_child():
    zm = make_zm()
    total = zm.get_total_object_count()
    obj_a = total - 1
    zm.remove_obj(obj_a)
    zm.set_child(obj_a, 0)  # ensure no children
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(store=1, branch=branch, next_=0x100)
    op_get_child(zm, instr, [obj_a])
    assert zm.read_variable(1) == 0
    assert zm.pc == 0x100


def test_get_sibling_op():
    zm = make_zm()
    total = zm.get_total_object_count()
    obj_a, obj_b, parent = total - 1, total - 2, total - 3
    zm.remove_obj(obj_a)
    zm.remove_obj(obj_b)
    zm.insert_obj(obj_a, parent)
    zm.insert_obj(obj_b, parent)  # obj_b is now first child, obj_a is sibling
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(store=1, branch=branch, next_=0x100)
    op_get_sibling(zm, instr, [obj_b])
    assert zm.read_variable(1) == obj_a
    assert zm.pc == 0x300


def test_get_parent_op():
    zm = make_zm()
    total = zm.get_total_object_count()
    obj_a, obj_b = total - 1, total - 2
    zm.remove_obj(obj_a)
    zm.insert_obj(obj_a, obj_b)
    instr = make_instr(store=1)
    op_get_parent(zm, instr, [obj_a])
    assert zm.read_variable(1) == obj_b


# --- Property ops ---

from yazm.ops import op_get_next_prop, op_get_prop, op_get_prop_addr, op_get_prop_len, op_put_prop


def test_get_prop_op():
    zm = make_zm()
    first_prop = zm.get_next_prop(1, 0)
    instr = make_instr(store=1)
    op_get_prop(zm, instr, [1, first_prop])
    assert isinstance(zm.read_variable(1), int)


def test_get_prop_addr_op():
    zm = make_zm()
    first_prop = zm.get_next_prop(1, 0)
    instr = make_instr(store=1)
    op_get_prop_addr(zm, instr, [1, first_prop])
    assert zm.read_variable(1) > 0


def test_get_next_prop_op():
    zm = make_zm()
    instr = make_instr(store=1)
    op_get_next_prop(zm, instr, [1, 0])
    assert zm.read_variable(1) > 0


def test_get_prop_len_op():
    zm = make_zm()
    first_prop = zm.get_next_prop(1, 0)
    addr = zm.get_prop_addr(1, first_prop)
    instr = make_instr(store=1)
    op_get_prop_len(zm, instr, [addr])
    assert zm.read_variable(1) >= 1


def test_put_prop_op():
    zm = make_zm()
    first_prop = zm.get_next_prop(1, 0)
    addr = zm.get_prop_addr(1, first_prop)
    length = zm.get_prop_len(addr)
    new_value = 0x1234 if length >= 2 else 0x42
    instr = make_instr(next_=0x100)
    op_put_prop(zm, instr, [1, first_prop, new_value])
    assert zm.get_prop_value(1, first_prop) == new_value
    assert zm.pc == 0x100


# --- Input / Status ---

from yazm.ops import op_show_status, op_sread


def test_sread_op():
    zm = make_zm_cap(input_text="north")
    text_addr = 0x200
    parse_addr = 0x220
    zm.memory.write_u8(text_addr, 10)  # max 10 chars
    instr = make_instr(next_=0x300)
    op_sread(zm, instr, [text_addr, parse_addr])
    assert zm.pc == 0x300
    assert zm.memory.u8(text_addr + 1) == ord("n")


def test_show_status_op():
    zm = make_zm_cap()
    instr = make_instr(next_=0x100)
    op_show_status(zm, instr, [])
    assert zm.pc == 0x100


# --- Random ---

from yazm.ops import op_random


def test_random_positive_range():
    zm = make_zm()
    instr = make_instr(store=1)
    op_random(zm, instr, [10])
    val = zm.read_variable(1)
    assert 1 <= val <= 10


def test_random_seed_zero():
    zm = make_zm()
    instr = make_instr(store=1)
    op_random(zm, instr, [0])  # 0 → seed to 0, returns 0
    assert zm.read_variable(1) == 0


def test_random_negative_seeds():
    zm = make_zm()
    instr = make_instr(store=1)
    op_random(zm, instr, [0xFFFE])  # -2 signed → abs=2 → seed, returns 0
    assert zm.read_variable(1) == 0


# --- Verify / Piracy ---

from yazm.ops import op_piracy, op_verify


def test_verify_op():
    zm = make_zm()
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(branch=branch, next_=0x100)
    op_verify(zm, instr, [])
    assert zm.pc in (0x100, 0x300)


def test_piracy_always_passes():
    zm = make_zm()
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(branch=branch, next_=0x100)
    op_piracy(zm, instr, [])
    assert zm.pc == 0x300


# --- Save / Restore ---

from yazm.ops import op_restore, op_save


def test_save_op_no_filename():
    zm = make_zm_cap(filename="")
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(branch=branch, next_=0x100)
    op_save(zm, instr, [])
    assert zm.pc == 0x100


def test_save_op_success(tmp_path):
    filename = str(tmp_path / "test.sav")
    zm = make_zm_cap(filename=filename)
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(branch=branch, next_=0x100)
    op_save(zm, instr, [])
    assert zm.pc == 0x300
    assert os.path.exists(filename)


def test_restore_op_no_filename():
    zm = make_zm_cap(filename="")
    branch = Branch(condition=True, address=0x300)
    instr = make_instr(branch=branch, next_=0x100)
    op_restore(zm, instr, [])
    assert zm.pc == 0x100


def test_restore_op_success(tmp_path):
    filename = str(tmp_path / "test.sav")
    zm = make_zm_cap(filename=filename)
    save_branch = Branch(condition=True, address=0x300)
    save_instr = make_instr(branch=save_branch, next_=0x100)
    op_save(zm, save_instr, [])
    assert os.path.exists(filename)
    restore_branch = Branch(condition=True, address=0x300)
    restore_instr = make_instr(branch=restore_branch, next_=0x100)
    op_restore(zm, restore_instr, [])
    assert zm.pc == 0x300  # saved PC was the branch address


# --- Save/Restore Undo ---

from yazm.ops import op_restore_undo, op_save_undo


def test_save_undo_op():
    zm = make_zm()
    instr = make_instr(store=1, next_=0x100)
    op_save_undo(zm, instr, [])
    assert len(zm.undos) == 1
    assert zm.read_variable(1) == 1


def test_restore_undo_empty():
    zm = make_zm()
    instr = make_instr(store=1)
    op_restore_undo(zm, instr, [])
    assert zm.read_variable(1) == 0


def test_restore_undo_op():
    zm = make_zm()
    instr = make_instr(store=1, next_=0x100)
    op_save_undo(zm, instr, [])
    assert len(zm.undos) == 1
    op_restore_undo(zm, instr, [])
    assert len(zm.undos) == 0


# --- Restart / Pop ---

from yazm.ops import op_pop, op_restart


def test_restart_op():
    zm = make_zm()
    original_pc = zm.initial_pc
    zm.pc = 0x1234
    instr = make_instr()
    op_restart(zm, instr, [])
    assert zm.pc == original_pc


def test_pop_op():
    zm = make_zm()
    zm.stack_push(77)
    instr = make_instr(next_=0x100)
    op_pop(zm, instr, [])
    assert zm.pc == 0x100


# --- Dispatch error ---

from yazm.ops import dispatch


def test_dispatch_unimplemented_opcode():
    zm = make_zm()
    # OP1_136 (call_1s) is in Opcode enum but not in DISPATCH_TABLE
    instr = Instruction(addr=0x50, opcode=Opcode.OP1_136, name="call_1s", store=None, next_=0x100)
    with pytest.raises(Exception, match="Unimplemented"):
        dispatch(zm, instr, [])
