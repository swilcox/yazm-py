"""Tests for snapshot.py (freeze/thaw JSON serialization)."""

import json

import pytest

from yazm.zmachine import ZMachine

from ._sample_data import ZSAMPLE_DATA


@pytest.fixture
def zm():
    return ZMachine(ZSAMPLE_DATA)


def test_freeze_produces_json(zm):
    frozen = zm.freeze()
    data = json.loads(frozen)
    assert "memory" in data
    assert "pc" in data
    assert "frames" in data
    assert "rng_state" in data


def test_freeze_pc_matches(zm):
    original_pc = zm.pc
    frozen = zm.freeze()
    data = json.loads(frozen)
    assert data["pc"] == original_pc


def test_thaw_restores_pc(zm):
    original_pc = zm.pc
    frozen = zm.freeze()
    zm.pc = 0xDEAD
    zm.thaw(frozen)
    assert zm.pc == original_pc


def test_freeze_thaw_roundtrip(zm):
    zm.write_global(5, 0x1234)
    frozen = zm.freeze()
    zm.write_global(5, 0)
    zm.thaw(frozen)
    assert zm.read_global(5) == 0x1234


def test_freeze_thaw_frame_count(zm):
    original_frame_count = len(zm.frames)
    frozen = zm.freeze()
    zm.thaw(frozen)
    assert len(zm.frames) == original_frame_count
