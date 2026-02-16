"""JSON + base64 full-state serialization for web server use."""

from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING

from .frame import Frame

if TYPE_CHECKING:
    from .zmachine import ZMachine


def freeze(zm: ZMachine) -> str:
    """Serialize full ZMachine state to a JSON string."""
    return json.dumps({
        "memory": base64.b64encode(bytes(zm.memory)).decode("ascii"),
        "pc": zm.pc,
        "frames": [frame.to_list() for frame in zm.frames],
        "rng_state": zm.rng.getstate(),
    })


def thaw(zm: ZMachine, json_str: str):
    """Restore ZMachine state from a JSON string produced by freeze()."""
    state = json.loads(json_str)
    memory = base64.b64decode(state["memory"])
    zm.memory[0 : len(memory)] = memory
    zm.pc = state["pc"]
    zm.frames = [Frame.from_bytes(bytearray(f)) for f in state["frames"]]
    zm.rng.setstate(tuple(state["rng_state"]))
