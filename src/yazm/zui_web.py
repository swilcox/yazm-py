"""Web-oriented UI driver for the Z-machine interpreter.

Buffers all output and raises InputRequested from zinput() to break
out of the synchronous zm.run() loop, enabling a request/response
cycle for web backends.
"""

from __future__ import annotations


class InputRequested(Exception):
    """Raised by zinput() to break out of zm.run() when input is needed."""


class ZUIWeb:
    def __init__(self):
        self._output_buffer: list[str] = []
        self._pending_input: str | None = None
        self._status_left: str = ""
        self._status_right: str = ""

    def set_input(self, text: str):
        """Queue input text to be returned by the next zinput() call."""
        self._pending_input = text

    def get_output(self) -> str:
        """Return and clear all buffered output."""
        result = "".join(self._output_buffer)
        self._output_buffer.clear()
        return result

    def get_status(self) -> tuple[str, str]:
        """Return the most recent status bar values (left, right)."""
        return (self._status_left, self._status_right)

    # --- Duck-typed UI methods (same interface as ZUIStd) ---

    def init(self):
        pass

    def zoutput(self, text: str):
        self._output_buffer.append(text)

    def zoutput_object(self, text: str, highlight: bool = False, is_location: bool = False):
        self._output_buffer.append(text)

    def zinput(self) -> str:
        if self._pending_input is not None:
            result = self._pending_input
            self._pending_input = None
            return result
        raise InputRequested()

    def zinput_filename(self, prompt: str) -> str:
        return ""

    def set_status_bar(self, left: str, right: str):
        self._status_left = left
        self._status_right = right

    def clear(self):
        pass

    def reset(self):
        pass
