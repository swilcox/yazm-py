"""Opcode handlers and dispatch table for the Z-machine."""
from __future__ import annotations
from typing import TYPE_CHECKING, List

from .enums import Opcode
from .utils import from_u16_to_i16
from .zinstruction import Instruction

if TYPE_CHECKING:
    from .zmachine import ZMachine


def u16(value: int) -> int:
    """Ensure value fits in unsigned 16 bits."""
    return value & 0xFFFF


# --- Control Flow ---

def op_call(zm: ZMachine, instr: Instruction, args: List[int]):
    """call routine with args"""
    if not args:
        zm.process_result(instr, 0)
        return
    zm.do_call(instr, args[0], args[1:])


def op_ret(zm: ZMachine, instr: Instruction, args: List[int]):
    """return value from routine"""
    zm.return_from_routine(args[0])


def op_rtrue(zm: ZMachine, instr: Instruction, args: List[int]):
    """return true (1)"""
    zm.return_from_routine(1)


def op_rfalse(zm: ZMachine, instr: Instruction, args: List[int]):
    """return false (0)"""
    zm.return_from_routine(0)


def op_ret_popped(zm: ZMachine, instr: Instruction, args: List[int]):
    """return top of stack"""
    zm.return_from_routine(zm.stack_pop())


def op_jump(zm: ZMachine, instr: Instruction, args: List[int]):
    """unconditional jump"""
    offset = from_u16_to_i16(args[0])
    zm.pc = instr.next_ + offset - 2


def op_quit(zm: ZMachine, instr: Instruction, args: List[int]):
    """quit the game"""
    zm.running = False


def op_nop(zm: ZMachine, instr: Instruction, args: List[int]):
    """no operation"""
    zm.pc = instr.next_


# --- Branch ---

def op_je(zm: ZMachine, instr: Instruction, args: List[int]):
    """jump if equal (first arg equals any subsequent)"""
    result = args[0] in args[1:]
    zm.process_branch(instr.branch, instr.next_, result)


def op_jz(zm: ZMachine, instr: Instruction, args: List[int]):
    """jump if zero"""
    result = args[0] == 0
    zm.process_branch(instr.branch, instr.next_, result)


def op_jl(zm: ZMachine, instr: Instruction, args: List[int]):
    """jump if less than (signed)"""
    result = from_u16_to_i16(args[0]) < from_u16_to_i16(args[1])
    zm.process_branch(instr.branch, instr.next_, result)


def op_jg(zm: ZMachine, instr: Instruction, args: List[int]):
    """jump if greater than (signed)"""
    result = from_u16_to_i16(args[0]) > from_u16_to_i16(args[1])
    zm.process_branch(instr.branch, instr.next_, result)


def op_jin(zm: ZMachine, instr: Instruction, args: List[int]):
    """jump if parent of obj1 is obj2"""
    result = zm.get_parent(args[0]) == args[1]
    zm.process_branch(instr.branch, instr.next_, result)


def op_test(zm: ZMachine, instr: Instruction, args: List[int]):
    """jump if all flags in bitmap are set"""
    result = (args[0] & args[1]) == args[1]
    zm.process_branch(instr.branch, instr.next_, result)


def op_test_attr(zm: ZMachine, instr: Instruction, args: List[int]):
    """jump if object has attribute"""
    result = zm.test_attr(args[0], args[1]) != 0
    zm.process_branch(instr.branch, instr.next_, result)


# --- Memory ---

def op_loadw(zm: ZMachine, instr: Instruction, args: List[int]):
    """load word from array"""
    addr = u16(args[0] + 2 * from_u16_to_i16(args[1]))
    value = zm.memory.u16(addr)
    zm.process_result(instr, value)


def op_loadb(zm: ZMachine, instr: Instruction, args: List[int]):
    """load byte from array"""
    addr = u16(args[0] + from_u16_to_i16(args[1]))
    value = zm.memory.u8(addr)
    zm.process_result(instr, value)


def op_storew(zm: ZMachine, instr: Instruction, args: List[int]):
    """store word to array"""
    addr = u16(args[0] + 2 * from_u16_to_i16(args[1]))
    zm.memory.write_u16(addr, args[2])
    zm.pc = instr.next_


def op_storeb(zm: ZMachine, instr: Instruction, args: List[int]):
    """store byte to array"""
    addr = u16(args[0] + from_u16_to_i16(args[1]))
    zm.memory.write_u8(addr, args[2] & 0xFF)
    zm.pc = instr.next_


def op_store(zm: ZMachine, instr: Instruction, args: List[int]):
    """store value to variable (indirect)"""
    zm.write_indirect_variable(args[0], args[1])
    zm.pc = instr.next_


def op_load(zm: ZMachine, instr: Instruction, args: List[int]):
    """load value from variable (indirect)"""
    value = zm.read_indirect_variable(args[0])
    zm.process_result(instr, value)


# --- Arithmetic ---

def op_add(zm: ZMachine, instr: Instruction, args: List[int]):
    """signed addition"""
    result = from_u16_to_i16(args[0]) + from_u16_to_i16(args[1])
    zm.process_result(instr, u16(result))


def op_sub(zm: ZMachine, instr: Instruction, args: List[int]):
    """signed subtraction"""
    result = from_u16_to_i16(args[0]) - from_u16_to_i16(args[1])
    zm.process_result(instr, u16(result))


def op_mul(zm: ZMachine, instr: Instruction, args: List[int]):
    """signed multiplication"""
    result = from_u16_to_i16(args[0]) * from_u16_to_i16(args[1])
    zm.process_result(instr, u16(result))


def op_div(zm: ZMachine, instr: Instruction, args: List[int]):
    """signed division"""
    a = from_u16_to_i16(args[0])
    b = from_u16_to_i16(args[1])
    if b == 0:
        raise Exception("Division by zero")
    result = int(a / b)  # truncate toward zero
    zm.process_result(instr, u16(result))


def op_mod(zm: ZMachine, instr: Instruction, args: List[int]):
    """signed modulo"""
    a = from_u16_to_i16(args[0])
    b = from_u16_to_i16(args[1])
    if b == 0:
        raise Exception("Division by zero")
    # Z-machine mod: sign follows dividend
    result = a - int(a / b) * b
    zm.process_result(instr, u16(result))


# --- Logical ---

def op_and(zm: ZMachine, instr: Instruction, args: List[int]):
    """bitwise AND"""
    zm.process_result(instr, args[0] & args[1])


def op_or(zm: ZMachine, instr: Instruction, args: List[int]):
    """bitwise OR"""
    zm.process_result(instr, args[0] | args[1])


def op_not(zm: ZMachine, instr: Instruction, args: List[int]):
    """bitwise NOT"""
    zm.process_result(instr, u16(~args[0]))


# --- Stack ---

def op_push(zm: ZMachine, instr: Instruction, args: List[int]):
    """push value onto stack"""
    zm.stack_push(args[0])
    zm.pc = instr.next_


def op_pull(zm: ZMachine, instr: Instruction, args: List[int]):
    """pull value from stack into variable"""
    value = zm.stack_pop()
    zm.write_indirect_variable(args[0], value)
    zm.pc = instr.next_


def op_sound_effect(zm: ZMachine, instr: Instruction, args: List[int]):
    """sound_effect — silently ignored (sound not supported)"""
    zm.pc = instr.next_


# --- Print ---

def op_print(zm: ZMachine, instr: Instruction, args: List[int]):
    """print inline string"""
    zm.ui.zoutput(instr.text)
    zm.pc = instr.next_


def op_print_ret(zm: ZMachine, instr: Instruction, args: List[int]):
    """print inline string, newline, then return true"""
    zm.ui.zoutput(instr.text + "\n")
    zm.return_from_routine(1)


def op_new_line(zm: ZMachine, instr: Instruction, args: List[int]):
    """print newline"""
    zm.ui.zoutput("\n")
    zm.pc = instr.next_


def op_print_num(zm: ZMachine, instr: Instruction, args: List[int]):
    """print signed number"""
    zm.ui.zoutput(str(from_u16_to_i16(args[0])))
    zm.pc = instr.next_


def op_print_char(zm: ZMachine, instr: Instruction, args: List[int]):
    """print ZSCII character"""
    from . import zscii
    zm.ui.zoutput(zscii.zscii_to_ascii(zm, [args[0]]))
    zm.pc = instr.next_


def op_print_obj(zm: ZMachine, instr: Instruction, args: List[int]):
    """print object name"""
    name = zm.get_object_name(args[0])
    is_location = (args[0] == zm.read_global(0))
    zm.ui.zoutput_object(name, zm.options.highlight_objects, is_location)
    zm.pc = instr.next_


def op_print_addr(zm: ZMachine, instr: Instruction, args: List[int]):
    """print string at byte address"""
    zm.ui.zoutput(zm.read_zstring(args[0]))
    zm.pc = instr.next_


def op_print_paddr(zm: ZMachine, instr: Instruction, args: List[int]):
    """print string at packed address"""
    addr = zm.unpack_print_paddr(args[0])
    zm.ui.zoutput(zm.read_zstring(addr))
    zm.pc = instr.next_


# --- Variables ---

def op_inc(zm: ZMachine, instr: Instruction, args: List[int]):
    """increment variable"""
    value = from_u16_to_i16(zm.read_indirect_variable(args[0]))
    zm.write_indirect_variable(args[0], u16(value + 1))
    zm.pc = instr.next_


def op_dec(zm: ZMachine, instr: Instruction, args: List[int]):
    """decrement variable"""
    value = from_u16_to_i16(zm.read_indirect_variable(args[0]))
    zm.write_indirect_variable(args[0], u16(value - 1))
    zm.pc = instr.next_


def op_inc_chk(zm: ZMachine, instr: Instruction, args: List[int]):
    """increment variable and branch if > value"""
    value = from_u16_to_i16(zm.read_indirect_variable(args[0]))
    value += 1
    zm.write_indirect_variable(args[0], u16(value))
    result = value > from_u16_to_i16(args[1])
    zm.process_branch(instr.branch, instr.next_, result)


def op_dec_chk(zm: ZMachine, instr: Instruction, args: List[int]):
    """decrement variable and branch if < value"""
    value = from_u16_to_i16(zm.read_indirect_variable(args[0]))
    value -= 1
    zm.write_indirect_variable(args[0], u16(value))
    result = value < from_u16_to_i16(args[1])
    zm.process_branch(instr.branch, instr.next_, result)


# --- Objects ---

def op_set_attr(zm: ZMachine, instr: Instruction, args: List[int]):
    """set object attribute"""
    zm.set_attr(args[0], args[1])
    zm.pc = instr.next_


def op_clear_attr(zm: ZMachine, instr: Instruction, args: List[int]):
    """clear object attribute"""
    zm.clear_attr(args[0], args[1])
    zm.pc = instr.next_


def op_insert_obj(zm: ZMachine, instr: Instruction, args: List[int]):
    """insert object into destination"""
    zm.insert_obj(args[0], args[1])
    zm.pc = instr.next_


def op_remove_obj(zm: ZMachine, instr: Instruction, args: List[int]):
    """remove object from parent"""
    zm.remove_obj(args[0])
    zm.pc = instr.next_


def op_get_child(zm: ZMachine, instr: Instruction, args: List[int]):
    """get first child of object (store + branch)"""
    child = zm.get_child(args[0])
    zm.write_variable(instr.store, child)
    zm.process_branch(instr.branch, instr.next_, child != 0)


def op_get_sibling(zm: ZMachine, instr: Instruction, args: List[int]):
    """get sibling of object (store + branch)"""
    sibling = zm.get_sibling(args[0])
    zm.write_variable(instr.store, sibling)
    zm.process_branch(instr.branch, instr.next_, sibling != 0)


def op_get_parent(zm: ZMachine, instr: Instruction, args: List[int]):
    """get parent of object"""
    zm.process_result(instr, zm.get_parent(args[0]))


# --- Properties ---

def op_get_prop(zm: ZMachine, instr: Instruction, args: List[int]):
    """get property value"""
    zm.process_result(instr, zm.get_prop_value(args[0], args[1]))


def op_get_prop_addr(zm: ZMachine, instr: Instruction, args: List[int]):
    """get property data address"""
    zm.process_result(instr, zm.get_prop_addr(args[0], args[1]))


def op_get_next_prop(zm: ZMachine, instr: Instruction, args: List[int]):
    """get next property number"""
    zm.process_result(instr, zm.get_next_prop(args[0], args[1]))


def op_get_prop_len(zm: ZMachine, instr: Instruction, args: List[int]):
    """get property data length"""
    zm.process_result(instr, zm.get_prop_len(args[0]))


def op_put_prop(zm: ZMachine, instr: Instruction, args: List[int]):
    """put property value"""
    zm.put_prop(args[0], args[1], args[2])
    zm.pc = instr.next_


# --- Input ---

def op_sread(zm: ZMachine, instr: Instruction, args: List[int]):
    """read input, tokenise"""
    zm.update_status_bar()
    text_addr = args[0]
    parse_addr = args[1]
    max_len = zm.memory.u8(text_addr)
    input_str = zm.ui.zinput()
    input_str = input_str.lower()[:max_len]
    # Write text to buffer (v1-4 format: starts at byte 1, terminated by 0)
    for i, ch in enumerate(input_str):
        zm.memory.write_u8(text_addr + 1 + i, ord(ch))
    zm.memory.write_u8(text_addr + 1 + len(input_str), 0)
    zm.tokenise(input_str, parse_addr)
    zm.pc = instr.next_


def op_show_status(zm: ZMachine, instr: Instruction, args: List[int]):
    """show status bar"""
    zm.update_status_bar()
    zm.pc = instr.next_


# --- Misc ---

def op_random(zm: ZMachine, instr: Instruction, args: List[int]):
    """random number"""
    range_val = from_u16_to_i16(args[0])
    if range_val <= 0:
        zm.rng.seed(abs(range_val))
        zm.process_result(instr, 0)
    else:
        zm.process_result(instr, zm.rng.randint(1, range_val))


def op_verify(zm: ZMachine, instr: Instruction, args: List[int]):
    """verify checksum"""
    result = zm.calculate_checksum() == zm.header.checksum
    zm.process_branch(instr.branch, instr.next_, result)


def op_piracy(zm: ZMachine, instr: Instruction, args: List[int]):
    """piracy check - always pass"""
    zm.process_branch(instr.branch, instr.next_, True)


def op_save(zm: ZMachine, instr: Instruction, args: List[int]):
    """save (v3 branch-based) - stub"""
    zm.process_branch(instr.branch, instr.next_, False)


def op_restore(zm: ZMachine, instr: Instruction, args: List[int]):
    """restore (v3 branch-based) - stub"""
    zm.process_branch(instr.branch, instr.next_, False)


def op_restart(zm: ZMachine, instr: Instruction, args: List[int]):
    """restart the game - stub"""
    zm.running = False


def op_pop(zm: ZMachine, instr: Instruction, args: List[int]):
    """pop/catch — pop stack in v1-4"""
    zm.stack_pop()
    zm.pc = instr.next_


# --- Dispatch Table ---

DISPATCH_TABLE = {
    # 2OP
    Opcode.OP2_1:  op_je,
    Opcode.OP2_2:  op_jl,
    Opcode.OP2_3:  op_jg,
    Opcode.OP2_4:  op_dec_chk,
    Opcode.OP2_5:  op_inc_chk,
    Opcode.OP2_6:  op_jin,
    Opcode.OP2_7:  op_test,
    Opcode.OP2_8:  op_or,
    Opcode.OP2_9:  op_and,
    Opcode.OP2_10: op_test_attr,
    Opcode.OP2_11: op_set_attr,
    Opcode.OP2_12: op_clear_attr,
    Opcode.OP2_13: op_store,
    Opcode.OP2_14: op_insert_obj,
    Opcode.OP2_15: op_loadw,
    Opcode.OP2_16: op_loadb,
    Opcode.OP2_17: op_get_prop,
    Opcode.OP2_18: op_get_prop_addr,
    Opcode.OP2_19: op_get_next_prop,
    Opcode.OP2_20: op_add,
    Opcode.OP2_21: op_sub,
    Opcode.OP2_22: op_mul,
    Opcode.OP2_23: op_div,
    Opcode.OP2_24: op_mod,
    # 1OP
    Opcode.OP1_128: op_jz,
    Opcode.OP1_129: op_get_sibling,
    Opcode.OP1_130: op_get_child,
    Opcode.OP1_131: op_get_parent,
    Opcode.OP1_132: op_get_prop_len,
    Opcode.OP1_133: op_inc,
    Opcode.OP1_134: op_dec,
    Opcode.OP1_135: op_print_addr,
    Opcode.OP1_137: op_remove_obj,
    Opcode.OP1_138: op_print_obj,
    Opcode.OP1_139: op_ret,
    Opcode.OP1_140: op_jump,
    Opcode.OP1_141: op_print_paddr,
    Opcode.OP1_142: op_load,
    Opcode.OP1_143: op_not,
    # 0OP
    Opcode.OP0_176: op_rtrue,
    Opcode.OP0_177: op_rfalse,
    Opcode.OP0_178: op_print,
    Opcode.OP0_179: op_print_ret,
    Opcode.OP0_180: op_nop,
    Opcode.OP0_181: op_save,
    Opcode.OP0_182: op_restore,
    Opcode.OP0_183: op_restart,
    Opcode.OP0_184: op_ret_popped,
    Opcode.OP0_185: op_pop,
    Opcode.OP0_186: op_quit,
    Opcode.OP0_187: op_new_line,
    Opcode.OP0_188: op_show_status,
    Opcode.OP0_189: op_verify,
    Opcode.OP0_191: op_piracy,
    # VAR
    Opcode.VAR_224: op_call,
    Opcode.VAR_225: op_storew,
    Opcode.VAR_226: op_storeb,
    Opcode.VAR_227: op_put_prop,
    Opcode.VAR_228: op_sread,
    Opcode.VAR_229: op_print_char,
    Opcode.VAR_230: op_print_num,
    Opcode.VAR_231: op_random,
    Opcode.VAR_232: op_push,
    Opcode.VAR_233: op_pull,
    Opcode.VAR_245: op_sound_effect,
}


def dispatch(zm: ZMachine, instr: Instruction, args: List[int]):
    """Dispatch an instruction to its handler."""
    handler = DISPATCH_TABLE.get(instr.opcode)
    if handler is None:
        raise Exception(f"Unimplemented opcode: {instr.name} ({instr.opcode}) at 0x{instr.addr:x}")
    handler(zm, instr, args)
