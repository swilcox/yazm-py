import pytest

from yazm.frame import Frame


def test_init_basic():
    frame = Frame(resume=0x1234, store=5, locals_=[10, 20, 30], arguments=[100, 200])
    assert frame.resume == 0x1234
    assert frame.store == 5
    assert frame.arg_count == 2
    # arguments override first N locals
    assert frame.locals == [100, 200, 30]


def test_init_no_arguments():
    frame = Frame(resume=0, store=None, locals_=[1, 2, 3], arguments=[])
    assert frame.arg_count == 0
    assert frame.locals == [1, 2, 3]


def test_init_more_args_than_locals():
    frame = Frame(resume=0, store=0, locals_=[0, 0], arguments=[10, 20, 30])
    assert frame.arg_count == 3
    assert frame.locals == [10, 20]


def test_stack_push_pop():
    frame = Frame(resume=0, store=None, locals_=[], arguments=[])
    frame.stack_push(42)
    frame.stack_push(99)
    assert frame.stack_pop() == 99
    assert frame.stack_pop() == 42


def test_stack_peek():
    frame = Frame(resume=0, store=None, locals_=[], arguments=[])
    frame.stack_push(7)
    frame.stack_push(13)
    assert frame.stack_peek() == 13
    assert frame.stack_peek() == 13  # doesn't consume
    assert frame.stack_pop() == 13


def test_stack_pop_empty_raises():
    frame = Frame(resume=0, store=None, locals_=[], arguments=[])
    with pytest.raises(IndexError):
        frame.stack_pop()


def test_read_write_local():
    frame = Frame(resume=0, store=None, locals_=[10, 20, 30], arguments=[])
    assert frame.read_local(0) == 10
    assert frame.read_local(2) == 30
    frame.write_local(1, 999)
    assert frame.read_local(1) == 999


def test_empty():
    frame = Frame(resume=0x1234, store=5, locals_=[10, 20], arguments=[1])
    frame.stack_push(42)
    frame.empty()
    assert frame.stack == []
    assert frame.locals == []
    assert frame.arg_count == 0
    assert frame.resume == 0
    assert frame.store is None


def test_to_list_from_bytes_roundtrip():
    frame = Frame(resume=0x012345, store=7, locals_=[100, 200, 300], arguments=[100, 200])
    frame.stack_push(1000)
    frame.stack_push(2000)
    serialized = frame.to_list()
    restored = Frame.from_bytes(bytearray(serialized))
    assert restored.resume == frame.resume
    assert restored.arg_count == frame.arg_count
    assert restored.locals == frame.locals
    assert restored.stack == frame.stack


def test_from_bytes_no_store():
    frame = Frame(resume=0x100, store=None, locals_=[50], arguments=[])
    serialized = frame.to_list()
    restored = Frame.from_bytes(bytearray(serialized))
    assert restored.resume == 0x100
    assert restored.store is None
    assert restored.locals == [50]


def test_to_list_empty_frame():
    frame = Frame(resume=0, store=None, locals_=[], arguments=[])
    serialized = frame.to_list()
    restored = Frame.from_bytes(bytearray(serialized))
    assert restored.resume == 0
    assert restored.locals == []
    assert restored.stack == []
    assert restored.arg_count == 0
