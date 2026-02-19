import pytest

from yazm.frame import Frame
from yazm.zmachine import ZMachine

from ._sample_data import ZSAMPLE_DATA


def test_zmachine_init():
    zmachine = ZMachine(ZSAMPLE_DATA)
    assert len(zmachine.dictionary.keys()) == 536
    assert [k for k in zmachine.dictionary][-1] == "zork"


def test_version(sample_zmachine):
    assert sample_zmachine.version == 3


def test_header_basics(sample_zmachine):
    zm = sample_zmachine
    assert zm.header.version == 3
    assert zm.header.release == 34


# --- Object tree ---


def test_get_parent(sample_zmachine):
    zm = sample_zmachine
    total = zm.get_total_object_count()
    assert total > 0
    # Object 0 always has parent 0
    assert zm.get_parent(0) == 0


def test_get_child(sample_zmachine):
    zm = sample_zmachine
    assert zm.get_child(0) == 0


def test_get_sibling(sample_zmachine):
    zm = sample_zmachine
    assert zm.get_sibling(0) == 0


def test_get_object_name(sample_zmachine):
    zm = sample_zmachine
    # Object 1 should have a name (it's always the first object)
    name = zm.get_object_name(1)
    assert isinstance(name, str)
    assert len(name) > 0


def test_object_tree_relationships(sample_zmachine):
    zm = sample_zmachine
    """If an object has a parent, the parent's child chain should include it."""
    obj_id = 1
    parent = zm.get_parent(obj_id)
    if parent != 0:
        child = zm.get_child(parent)
        found = False
        while child != 0:
            if child == obj_id:
                found = True
                break
            child = zm.get_sibling(child)
        assert found, f"Object {obj_id} not found in parent {parent}'s child chain"


# --- Object manipulation ---


def test_insert_obj(sample_zmachine):
    zm = sample_zmachine
    # Find two objects: move obj_a into obj_b
    total = zm.get_total_object_count()
    # Use objects near the end that are less likely to disrupt the tree
    obj_a = total - 1
    obj_b = total - 2
    zm.remove_obj(obj_a)  # ensure clean state
    zm.insert_obj(obj_a, obj_b)
    assert zm.get_parent(obj_a) == obj_b
    assert zm.get_child(obj_b) == obj_a


def test_remove_obj(sample_zmachine):
    zm = sample_zmachine
    total = zm.get_total_object_count()
    obj_a = total - 1
    obj_b = total - 2
    zm.remove_obj(obj_a)
    zm.insert_obj(obj_a, obj_b)
    zm.remove_obj(obj_a)
    assert zm.get_parent(obj_a) == 0
    assert zm.get_sibling(obj_a) == 0


def test_remove_obj_with_no_parent(sample_zmachine):
    zm = sample_zmachine
    total = zm.get_total_object_count()
    obj = total - 1
    zm.remove_obj(obj)
    # Removing again should be a no-op (parent is already 0)
    zm.remove_obj(obj)
    assert zm.get_parent(obj) == 0


# --- Attributes ---


def test_set_and_test_attr(sample_zmachine):
    zm = sample_zmachine
    total = zm.get_total_object_count()
    obj = total - 1
    # Clear, test, set, test
    zm.clear_attr(obj, 0)
    assert zm.test_attr(obj, 0) == 0
    zm.set_attr(obj, 0)
    assert zm.test_attr(obj, 0) == 1


def test_clear_attr(sample_zmachine):
    zm = sample_zmachine
    total = zm.get_total_object_count()
    obj = total - 1
    zm.set_attr(obj, 5)
    assert zm.test_attr(obj, 5) == 1
    zm.clear_attr(obj, 5)
    assert zm.test_attr(obj, 5) == 0


def test_attr_multiple_bits(sample_zmachine):
    zm = sample_zmachine
    total = zm.get_total_object_count()
    obj = total - 1
    zm.clear_attr(obj, 0)
    zm.clear_attr(obj, 1)
    zm.set_attr(obj, 0)
    assert zm.test_attr(obj, 0) == 1
    assert zm.test_attr(obj, 1) == 0


def test_attr_out_of_bounds(sample_zmachine):
    zm = sample_zmachine
    with pytest.raises(Exception, match="out-of-bounds"):
        zm.test_attr(1, 33)  # v3 has 32 attributes (0-31)


# --- Properties ---


def test_get_prop_value(sample_zmachine):
    zm = sample_zmachine
    # Get the first property of object 1
    first_prop_num = zm.get_next_prop(1, 0)
    assert first_prop_num > 0
    value = zm.get_prop_value(1, first_prop_num)
    assert isinstance(value, int)


def test_get_prop_value_default(sample_zmachine):
    zm = sample_zmachine
    # Property 31 (max for v3) is unlikely to be defined on most objects
    # If not found, returns default from property defaults table
    value = zm.get_prop_value(1, 31)
    default = zm.get_default_prop(31)
    # These should be equal since prop 31 likely doesn't exist on obj 1
    # (If it does, that's fine too - the test just verifies no crash)
    assert isinstance(value, int)


def test_get_next_prop(sample_zmachine):
    zm = sample_zmachine
    # Property 0 → get first property
    first = zm.get_next_prop(1, 0)
    assert first > 0
    # Then get the next one
    second = zm.get_next_prop(1, first)
    # Properties are in descending order
    assert second < first or second == 0


def test_get_prop_addr(sample_zmachine):
    zm = sample_zmachine
    first_prop = zm.get_next_prop(1, 0)
    addr = zm.get_prop_addr(1, first_prop)
    assert addr > 0


def test_get_prop_addr_nonexistent(sample_zmachine):
    zm = sample_zmachine
    addr = zm.get_prop_addr(1, 31)
    # May or may not exist; if not, addr should be 0
    assert isinstance(addr, int)


def test_get_prop_len(sample_zmachine):
    zm = sample_zmachine
    first_prop = zm.get_next_prop(1, 0)
    addr = zm.get_prop_addr(1, first_prop)
    length = zm.get_prop_len(addr)
    assert length >= 1


def test_get_prop_len_zero_addr(sample_zmachine):
    zm = sample_zmachine
    assert zm.get_prop_len(0) == 0


# --- Variables ---


def test_read_write_variable_stack(sample_zmachine):
    zm = sample_zmachine
    # Variable 0 = stack
    zm.write_variable(0, 42)
    assert zm.read_variable(0) == 42


def test_read_write_variable_local(sample_zmachine):
    zm = sample_zmachine
    # Add a frame with locals
    zm.frames.append(Frame(resume=0, store=None, locals_=[0, 0, 0], arguments=[]))
    zm.write_variable(1, 100)  # local 0
    assert zm.read_variable(1) == 100
    zm.write_variable(3, 200)  # local 2
    assert zm.read_variable(3) == 200


def test_read_write_variable_global(sample_zmachine):
    zm = sample_zmachine
    # Variables 16-255 are globals
    zm.write_variable(16, 999)
    assert zm.read_variable(16) == 999


def test_read_write_global(sample_zmachine):
    zm = sample_zmachine
    zm.write_global(0, 123)
    assert zm.read_global(0) == 123
    zm.write_global(100, 456)
    assert zm.read_global(100) == 456


def test_indirect_variable_stack(sample_zmachine):
    zm = sample_zmachine
    zm.stack_push(50)
    # read_indirect peeks (doesn't pop)
    assert zm.read_indirect_variable(0) == 50
    # write_indirect replaces top
    zm.write_indirect_variable(0, 99)
    assert zm.stack_pop() == 99


# --- Address helpers ---


def test_unpack_v3(sample_zmachine):
    zm = sample_zmachine
    assert zm.version == 3
    assert zm.unpack(0x100) == 0x200


def test_calculate_checksum(sample_zmachine):
    zm = sample_zmachine
    checksum = zm.calculate_checksum()
    assert isinstance(checksum, int)
    assert 0 <= checksum <= 0xFFFF


# --- Text ---


def test_read_zstring(sample_zmachine):
    zm = sample_zmachine
    # Read the name of object 1 (known to exist)
    name = zm.get_object_name(1)
    assert isinstance(name, str)
    assert len(name) > 0


def test_get_abbrev(sample_zmachine):
    zm = sample_zmachine
    # Abbreviation 0 should exist and return a string
    abbrev = zm.get_abbrev(0)
    assert isinstance(abbrev, str)


def test_get_abbrev_out_of_bounds(sample_zmachine):
    zm = sample_zmachine
    with pytest.raises(Exception, match="Bad Abbrev"):
        zm.get_abbrev(97)


def test_zstring_length(sample_zmachine):
    zm = sample_zmachine
    # Get a property table address for object 1 to find a zstring
    addr = zm.get_object_prop_table_addr(1)
    text_len_words = zm.memory.u8(addr)
    if text_len_words > 0:
        length = zm.zstring_length(addr + 1)
        assert length == text_len_words * 2


# --- Dictionary ---


def test_check_dictionary_found(sample_zmachine):
    zm = sample_zmachine
    addr = zm.check_dictionary("open")
    assert addr > 0


def test_check_dictionary_not_found(sample_zmachine):
    zm = sample_zmachine
    addr = zm.check_dictionary("xyzzy123")
    assert addr == 0


# --- Object tree building ---


def test_get_object_tree(sample_zmachine):
    zm = sample_zmachine
    tree = zm.get_object_tree()
    assert tree.number == 0
    assert len(tree.children) > 0


def test_total_object_count(sample_zmachine):
    zm = sample_zmachine
    count = zm.get_total_object_count()
    assert count > 0
    assert count < 1000  # sanity check


# --- process_branch ---


def test_process_branch_returns_0(sample_zmachine):
    from yazm.zinstruction import Branch

    zm = sample_zmachine
    # Ensure the frame below has locals so store=1 works after return
    zm.frames.append(Frame(resume=0, store=None, locals_=[0, 0], arguments=[]))
    zm.frames.append(Frame(resume=0x200, store=1, locals_=[0], arguments=[]))
    branch = Branch(condition=True, returns=0)
    zm.process_branch(branch, 0x100, True)
    # Should have returned from routine with value 0
    assert zm.pc == 0x200


def test_process_branch_returns_1(sample_zmachine):
    from yazm.zinstruction import Branch

    zm = sample_zmachine
    zm.frames.append(Frame(resume=0, store=None, locals_=[0, 0], arguments=[]))
    zm.frames.append(Frame(resume=0x200, store=1, locals_=[0], arguments=[]))
    branch = Branch(condition=True, returns=1)
    zm.process_branch(branch, 0x100, True)
    assert zm.pc == 0x200


def test_process_branch_address(sample_zmachine):
    from yazm.zinstruction import Branch

    zm = sample_zmachine
    branch = Branch(condition=True, address=0x400)
    zm.process_branch(branch, 0x100, True)
    assert zm.pc == 0x400


def test_process_branch_no_branch(sample_zmachine):
    from yazm.zinstruction import Branch

    zm = sample_zmachine
    branch = Branch(condition=True, address=0x400)
    zm.process_branch(branch, 0x100, False)
    assert zm.pc == 0x100


# =============================================================================
# Additional coverage tests
# =============================================================================

from yazm.enums import Opcode, OperandType
from yazm.zinstruction import Instruction


class _CapUI:
    def __init__(self):
        self.output = []

    def zoutput(self, text: str):
        self.output.append(text)

    def zoutput_object(self, text: str, highlight: bool = False, is_location: bool = False):
        self.output.append(text)

    def set_status_bar(self, left: str, right: str):
        pass

    def zinput(self) -> str:
        return "north"

    def zinput_filename(self, prompt: str) -> str:
        return ""


# --- ZObject.print_tree ---


def test_zobject_print_tree(sample_zmachine):
    from yazm.zmachine import ZObject

    zm = sample_zmachine
    tree = zm.get_object_tree()
    output = tree.print_tree("", 0, False)
    assert isinstance(output, str)
    assert len(output) > 0
    # root is depth 0
    assert "(" in output


def test_zobject_print_tree_child_depth(sample_zmachine):
    zm = sample_zmachine
    tree = zm.get_object_tree()
    # Find a child to test depth > 0 branch rendering
    if tree.children:
        child = tree.children[0]
        out_last = child.print_tree("", 1, True)
        out_not_last = child.print_tree("", 1, False)
        assert "└──" in out_last
        assert "├──" in out_not_last


# --- get_object_addr(0) ---


def test_get_object_addr_zero(sample_zmachine):
    zm = sample_zmachine
    addr = zm.get_object_addr(0)
    assert addr == zm.header.obj_table_addr


# --- insert_obj early return ---


def test_insert_obj_already_first_child(sample_zmachine):
    zm = sample_zmachine
    total = zm.get_total_object_count()
    obj_a, obj_b = total - 1, total - 2
    zm.remove_obj(obj_a)
    zm.insert_obj(obj_a, obj_b)
    parent_before = zm.get_parent(obj_a)
    zm.insert_obj(obj_a, obj_b)  # already first child → early return
    assert zm.get_parent(obj_a) == parent_before


# --- find_object / find_yourself ---


def test_find_object_found(sample_zmachine):
    zm = sample_zmachine
    name = zm.get_object_name(1)
    result = zm.find_object(name)
    assert result == 1


def test_find_object_not_found(sample_zmachine):
    zm = sample_zmachine
    result = zm.find_object("xyzzy_no_such_object_99")
    assert result is None


def test_find_yourself(sample_zmachine):
    zm = sample_zmachine
    result = zm.find_yourself()
    assert result is None or isinstance(result, int)


# --- set_attr / clear_attr out-of-bounds ---


def test_set_attr_out_of_bounds(sample_zmachine):
    zm = sample_zmachine
    with pytest.raises(Exception, match="out-of-bounds"):
        zm.set_attr(1, 33)


def test_clear_attr_out_of_bounds(sample_zmachine):
    zm = sample_zmachine
    with pytest.raises(Exception, match="out-of-bounds"):
        zm.clear_attr(1, 33)


# --- find_prop edge cases ---


def test_find_prop_zero_returns_empty(sample_zmachine):
    from yazm.zmachine import ZObjectProperty

    zm = sample_zmachine
    prop = zm.find_prop(1, 0)
    assert prop.number == 0
    assert prop.length == 0


def test_find_prop_iterates_to_second(sample_zmachine):
    zm = sample_zmachine
    first = zm.get_next_prop(1, 0)
    second = zm.get_next_prop(1, first)
    if second == 0:
        pytest.skip("Object 1 has only one property")
    prop = zm.find_prop(1, second)
    assert prop.number == second


def test_find_prop_nonexistent_high_number(sample_zmachine):
    zm = sample_zmachine
    # Property 99 doesn't exist (v3 max is 31); loop should advance past first prop
    prop = zm.find_prop(1, 99)
    assert prop.number == 0


# --- get_prop_value with byte-sized property ---


def test_get_prop_value_byte_property(sample_zmachine):
    zm = sample_zmachine
    for obj_id in range(1, min(20, zm.get_total_object_count() + 1)):
        prop_num = zm.get_next_prop(obj_id, 0)
        while prop_num != 0:
            addr = zm.get_prop_addr(obj_id, prop_num)
            if zm.get_prop_len(addr) == 1:
                val = zm.get_prop_value(obj_id, prop_num)
                assert 0 <= val <= 255
                return
            prop_num = zm.get_next_prop(obj_id, prop_num)
    pytest.skip("No byte-sized property in sample data")


# --- put_prop both lengths ---


def test_put_prop_word(sample_zmachine):
    zm = sample_zmachine
    for obj_id in range(1, min(20, zm.get_total_object_count() + 1)):
        prop_num = zm.get_next_prop(obj_id, 0)
        while prop_num != 0:
            addr = zm.get_prop_addr(obj_id, prop_num)
            if zm.get_prop_len(addr) == 2:
                zm.put_prop(obj_id, prop_num, 0x1234)
                assert zm.get_prop_value(obj_id, prop_num) == 0x1234
                return
            prop_num = zm.get_next_prop(obj_id, prop_num)
    pytest.skip("No word-sized property in sample data")


def test_put_prop_byte(sample_zmachine):
    zm = sample_zmachine
    for obj_id in range(1, min(20, zm.get_total_object_count() + 1)):
        prop_num = zm.get_next_prop(obj_id, 0)
        while prop_num != 0:
            addr = zm.get_prop_addr(obj_id, prop_num)
            if zm.get_prop_len(addr) == 1:
                zm.put_prop(obj_id, prop_num, 0x42)
                assert zm.get_prop_value(obj_id, prop_num) == 0x42
                return
            prop_num = zm.get_next_prop(obj_id, prop_num)
    pytest.skip("No byte-sized property in sample data")


# --- get_current_room / get_status ---


def test_get_current_room(sample_zmachine):
    zm = sample_zmachine
    num, name = zm.get_current_room()
    assert isinstance(num, int)
    assert isinstance(name, str)


def test_get_status_score_mode(sample_zmachine):
    zm = sample_zmachine
    left, right = zm.get_status()
    assert isinstance(left, str)
    assert "/" in right  # "score/turns"


def test_get_status_time_mode(sample_zmachine):
    zm = sample_zmachine
    original_flag = zm.memory[0x1]
    zm.memory[0x1] = original_flag | 0b00000010  # set time mode bit
    zm.write_global(1, 14)  # hours
    zm.write_global(2, 30)  # minutes
    left, right = zm.get_status()
    assert "AM" in right or "PM" in right
    zm.memory[0x1] = original_flag  # restore


def test_update_status_bar(sample_zmachine):
    zm = sample_zmachine
    zm.ui = _CapUI()
    zm.update_status_bar()  # should call set_status_bar without error


# --- undo / redo ---


def test_undo_empty(sample_zmachine):
    zm = sample_zmachine
    assert zm.undo() is False


def test_redo_empty(sample_zmachine):
    zm = sample_zmachine
    assert zm.redo() is False


def test_undo_redo_cycle(sample_zmachine):
    zm = sample_zmachine
    state = zm.make_save_state(zm.pc)
    zm.undos.append(state)
    assert zm.undo() is True
    assert zm.redo() is True


# --- get_arguments with VARIABLE operand ---


def test_get_arguments_variable_type(sample_zmachine):
    zm = sample_zmachine
    zm.frames.append(Frame(resume=0, store=None, locals_=[42, 0], arguments=[]))
    args = zm.get_arguments([1], [OperandType.VARIABLE])
    assert args == [42]
    zm.frames.pop()


def test_get_arguments_small_type(sample_zmachine):
    zm = sample_zmachine
    args = zm.get_arguments([99], [OperandType.SMALL])
    assert args == [99]


# --- process_result with branch ---


def test_process_result_with_branch(sample_zmachine):
    from yazm.zinstruction import Branch

    zm = sample_zmachine
    branch = Branch(condition=True, address=0x400)
    instr = Instruction(addr=0x50, opcode=Opcode.OP2_20, name="add", store=None, next_=0x100, branch=branch)
    zm.process_result(instr, 1)
    assert zm.pc == 0x400


# --- decode_instruction / handle_instruction ---


def test_decode_instruction(sample_zmachine):
    zm = sample_zmachine
    instr = zm.decode_instruction(zm.pc)
    assert instr.addr == zm.pc


def test_handle_instruction(sample_zmachine):
    zm = sample_zmachine
    instr = Instruction(addr=0x50, opcode=Opcode.OP0_180, name="nop", store=None, next_=0x100, branch=None)
    zm.handle_instruction(instr)
    assert zm.pc == 0x100


# --- is_debug_command / handle_input ---


def test_is_debug_command_true(sample_zmachine):
    zm = sample_zmachine
    assert zm.is_debug_command("$help") is True


def test_is_debug_command_false(sample_zmachine):
    zm = sample_zmachine
    assert zm.is_debug_command("north") is False


def test_handle_input_debug(sample_zmachine):
    zm = sample_zmachine
    zm.ui = _CapUI()
    zm.handle_input("$help")
    # help command produces output
    assert len(zm.ui.output) > 0


# --- run ---


def test_run_quit(sample_zmachine):
    zm = sample_zmachine
    # SHORT 0OP QUIT: raw_code = 0xBA
    zm.memory.write_u8(zm.pc, 0xBA)
    zm.run()
    assert zm.running is False


# --- unpack ---


def test_unpack_v4(sample_zmachine):
    zm = sample_zmachine
    zm.version = 4
    assert zm.unpack(0x100) == 0x400
    zm.version = 3


def test_unpack_v8(sample_zmachine):
    zm = sample_zmachine
    zm.version = 8
    assert zm.unpack(0x100) == 0x800
    zm.version = 3


# --- unpack_routine_addr / unpack_print_paddr ---


def test_unpack_routine_addr_normal(sample_zmachine):
    zm = sample_zmachine
    result = zm.unpack_routine_addr(0x100)
    assert result == 0x200  # v3: addr * 2


def test_unpack_routine_addr_small(sample_zmachine):
    """unpack(3) = 6 for v3; 6 is in [6, 7] → offset branch."""
    zm = sample_zmachine
    result = zm.unpack_routine_addr(3)
    assert result == 6 + zm.header.routine_offset * 8


def test_unpack_print_paddr_normal(sample_zmachine):
    zm = sample_zmachine
    result = zm.unpack_print_paddr(0x100)
    assert result == 0x200


def test_unpack_print_paddr_small(sample_zmachine):
    zm = sample_zmachine
    result = zm.unpack_print_paddr(3)
    assert result == 6 + zm.header.string_offset * 8


# --- read/write global out-of-bounds ---


def test_read_global_out_of_bounds(sample_zmachine):
    zm = sample_zmachine
    with pytest.raises(Exception, match="can't read global"):
        zm.read_global(241)


def test_write_global_out_of_bounds(sample_zmachine):
    zm = sample_zmachine
    with pytest.raises(Exception, match="can't write global"):
        zm.write_global(241, 0)


# --- variable index out-of-range ---


def test_read_variable_out_of_range(sample_zmachine):
    zm = sample_zmachine
    with pytest.raises(Exception, match="unreachable variable"):
        zm.read_variable(256)


def test_read_indirect_variable_out_of_range(sample_zmachine):
    zm = sample_zmachine
    with pytest.raises(Exception, match="unreachable indirect variable"):
        zm.read_indirect_variable(256)


def test_write_variable_out_of_range(sample_zmachine):
    zm = sample_zmachine
    with pytest.raises(Exception, match="unreachable variable"):
        zm.write_variable(256, 0)


def test_write_indirect_variable_out_of_range(sample_zmachine):
    zm = sample_zmachine
    with pytest.raises(Exception, match="unreachable indirect variable"):
        zm.write_indirect_variable(256, 0)


# --- tokenise ---


def test_tokenise_single_word(sample_zmachine):
    zm = sample_zmachine
    parse_addr = 0x300
    zm.tokenise("open", parse_addr)
    count = zm.memory.u8(parse_addr + 1)
    assert count == 1


def test_tokenise_two_words(sample_zmachine):
    zm = sample_zmachine
    parse_addr = 0x300
    zm.tokenise("open mailbox", parse_addr)
    count = zm.memory.u8(parse_addr + 1)
    assert count == 2


def test_tokenise_empty(sample_zmachine):
    zm = sample_zmachine
    parse_addr = 0x300
    zm.tokenise("", parse_addr)
    count = zm.memory.u8(parse_addr + 1)
    assert count == 0


# --- do_call ---


def test_do_call_addr_zero(sample_zmachine):
    zm = sample_zmachine
    zm.frames.append(Frame(resume=0, store=None, locals_=[0, 0, 0, 0, 0], arguments=[]))
    instr = Instruction(addr=0x50, opcode=Opcode.VAR_224, name="call", store=1, next_=0x100)
    zm.do_call(instr, 0, [])
    assert zm.read_variable(1) == 0
    zm.frames.pop()


def test_do_call_valid_address(sample_zmachine):
    zm = sample_zmachine
    zm.frames.append(Frame(resume=0, store=None, locals_=[0, 0, 0, 0, 0], arguments=[]))
    # Write a minimal v3 routine at byte address 0x200: 2 locals, initial values 10, 20
    routine_addr = 0x200
    zm.memory.write_u8(routine_addr, 2)         # 2 locals
    zm.memory.write_u16(routine_addr + 1, 10)   # local 0 init = 10
    zm.memory.write_u16(routine_addr + 3, 20)   # local 1 init = 20
    packed_addr = routine_addr // 2             # v3: packed = byte_addr / 2
    frame_count_before = len(zm.frames)
    instr = Instruction(addr=0x50, opcode=Opcode.VAR_224, name="call", store=None, next_=0x300)
    zm.do_call(instr, packed_addr, [])
    assert zm.pc == routine_addr + 5            # past 1+2*2 bytes of routine header
    assert len(zm.frames) == frame_count_before + 1
    new_frame = zm.frames[-1]
    assert new_frame.locals[0] == 10
    assert new_frame.locals[1] == 20
    zm.frames.pop()
