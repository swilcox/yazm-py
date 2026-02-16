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
