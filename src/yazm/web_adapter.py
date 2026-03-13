"""Web adapter that wraps the Z-machine in a request/response interface.

Conforms to zorkdemo's AdventureInstance protocol (execute, admin_save,
admin_load) so it can be used as a drop-in replacement for the toy
Adventure engine.
"""

from __future__ import annotations

import contextlib

from .zmachine import ZMachine
from .zui_web import InputRequested, ZUIWeb


class ZorkWebAdapter:
    def __init__(self, story_data: bytes):
        self._story_data = story_data
        self._ui = ZUIWeb()
        self._zm = ZMachine(story_data)
        self._zm.ui = self._ui
        self._intro_collected = False

    def _run_until_input(self):
        """Run the Z-machine until it requests input or the game ends."""
        with contextlib.suppress(InputRequested):
            self._zm.run()

    def get_intro(self) -> str:
        """Run from the start to the first zinput() and return the intro text."""
        if not self._intro_collected:
            self._run_until_input()
            self._intro_collected = True
        return self._ui.get_output()

    def execute(self, tokens: list[str]) -> str:
        """Run a command and return the game's text output."""
        command = " ".join(tokens)
        self._ui.set_input(command)
        self._run_until_input()
        return self._ui.get_output()

    def admin_save(self) -> bytes:
        """Serialize the full Z-machine state to bytes."""
        return self._zm.freeze().encode("utf-8")

    def admin_load(self, input_bytes: bytes) -> None:
        """Restore Z-machine state from bytes produced by admin_save."""
        self._zm = ZMachine(self._story_data)
        self._zm.ui = self._ui
        self._zm.thaw(input_bytes.decode("utf-8"))
        self._intro_collected = True
