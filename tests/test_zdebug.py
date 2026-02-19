"""Tests for ZDebugger."""

import pytest

from yazm.zmachine import ZMachine

from ._sample_data import ZSAMPLE_DATA


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


@pytest.fixture
def zm():
    z = ZMachine(ZSAMPLE_DATA)
    z.ui = _CapUI()
    return z


def test_debug():
    pass


def test_is_debug_command_known(zm):
    assert zm.debugger.is_debug_command("$help") is True
    assert zm.debugger.is_debug_command("$dict") is True
    assert zm.debugger.is_debug_command("$tree") is True


def test_is_debug_command_unknown(zm):
    assert zm.debugger.is_debug_command("north") is False
    assert zm.debugger.is_debug_command("") is False


def test_handle_debug_command_help(zm):
    result = zm.debugger.handle_debug_command("$help")
    assert result is False  # command found, should_ask_again=False
    assert len(zm.ui.output) > 0


def test_handle_debug_command_dict(zm):
    result = zm.debugger.handle_debug_command("$dict")
    assert result is False
    assert len(zm.ui.output) > 0
    output_text = " ".join(zm.ui.output)
    assert len(output_text) > 0


def test_handle_debug_command_tree(zm):
    result = zm.debugger.handle_debug_command("$tree")
    assert result is False
    assert len(zm.ui.output) > 0


def test_handle_debug_command_unknown(zm):
    """Unknown command returns should_ask_again=True."""
    result = zm.debugger.handle_debug_command("$notacommand")
    assert result is True


def test_debug_undo_empty(zm):
    zm.debugger.debug_undo()
    output = " ".join(zm.ui.output)
    assert "Nothing to undo" in output


def test_debug_redo_empty(zm):
    zm.debugger.debug_redo()
    output = " ".join(zm.ui.output)
    assert "Nothing to redo" in output


def test_debug_undo_after_save(zm):
    state = zm.make_save_state(zm.pc)
    zm.undos.append(state)
    zm.debugger.debug_undo()
    output = " ".join(zm.ui.output)
    assert "Undo successful" in output


def test_debug_redo_after_undo(zm):
    state = zm.make_save_state(zm.pc)
    zm.undos.append(state)
    zm.undo()
    zm.debugger.debug_redo()
    output = " ".join(zm.ui.output)
    assert "Redo successful" in output


def test_debug_dictionary_output(zm):
    zm.debugger.debug_dictionary()
    assert len(zm.ui.output) > 0
    text = zm.ui.output[0]
    assert len(text) > 0


def test_debug_object_tree_output(zm):
    zm.debugger.debug_object_tree()
    assert len(zm.ui.output) > 0


def test_debug_header_noop(zm):
    zm.debugger.debug_header()  # currently a pass/no-op


def test_debug_dump_noop(zm):
    zm.debugger.debug_dump()


def test_debug_room_noop(zm):
    zm.debugger.debug_room()


def test_debug_yourself_noop(zm):
    zm.debugger.debug_yourself()


def test_debug_history_noop(zm):
    zm.debugger.debug_history()


def test_debug_object_simple_noop(zm):
    zm.debugger.debug_object_simple("1")


def test_debug_object_noop(zm):
    zm.debugger.debug_object("1")


def test_debug_object_properties_noop(zm):
    zm.debugger.debug_object_properties("1")


def test_debug_object_attributes_noop(zm):
    zm.debugger.debug_object_attributes("1")


def test_debug_object_details_noop(zm):
    zm.debugger.debug_object_details("1")


def test_debug_have_attributes_noop(zm):
    zm.debugger.debug_have_attributes("lit")


def test_debug_have_property_noop(zm):
    zm.debugger.debug_have_property("1")


def test_debug_parent_noop(zm):
    zm.debugger.debug_parent("1")


def test_debug_find_object_noop(zm):
    zm.debugger.debug_find_object("mailbox")


def test_debug_teleport_noop(zm):
    zm.debugger.debug_teleport("1")


def test_debug_steal_noop(zm):
    zm.debugger.debug_steal("1")


def test_debug_routine_noop(zm):
    zm.debugger.debug_routine()
