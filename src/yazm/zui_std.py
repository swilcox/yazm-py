import os
import sys


class _Ansi:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    BOLD_CYAN = "\033[1;36m"
    BOLD_YELLOW = "\033[1;33m"
    REVERSE = "\033[7m"
    CLEAR = "\033[2J"
    HOME = "\033[H"
    SAVE_CUR = "\033[s"
    RESTORE_CUR = "\033[u"

    @staticmethod
    def move_to(row: int, col: int = 1) -> str:
        return f"\033[{row};{col}H"


def _get_terminal_width() -> int:
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80


class ZUIStd:
    def __init__(self, plain: bool = False):
        self._last_output = ""
        self.plain = plain

    def init(self):
        if self.plain:
            return
        w = sys.stdout.write
        w(_Ansi.CLEAR + _Ansi.HOME)
        # blank status bar on row 1
        width = _get_terminal_width()
        w(_Ansi.SAVE_CUR)
        w(_Ansi.move_to(1))
        w(_Ansi.REVERSE + " " * width + _Ansi.RESET)
        w(_Ansi.RESTORE_CUR)
        # move cursor to row 2
        w(_Ansi.move_to(2))
        sys.stdout.flush()

    def zoutput(self, text: str):
        print(text, end="", flush=True)
        if text:
            self._last_output = text

    def zoutput_object(self, text: str, highlight: bool = False, is_location: bool = False):
        if highlight:
            if is_location:
                print(_Ansi.BOLD_YELLOW + text + _Ansi.RESET, end="", flush=True)
            else:
                print(_Ansi.BOLD_CYAN + text + _Ansi.RESET, end="", flush=True)
        else:
            print(text, end="", flush=True)
        if text:
            self._last_output = text

    def zinput(self) -> str:
        try:
            if self.plain:
                result = input()
            elif self._last_output.rstrip().endswith(">"):
                # Suppress styled prompt if game already printed ">"
                result = input()
            else:
                result = input(_Ansi.BOLD + "> " + _Ansi.RESET)
            self._last_output = ""
            return result
        except (EOFError, KeyboardInterrupt):
            raise SystemExit(0) from None

    def zinput_filename(self, prompt: str) -> str:
        try:
            return input(prompt)
        except (EOFError, KeyboardInterrupt):
            return ""

    def set_status_bar(self, left: str, right: str):
        if self.plain:
            return
        width = _get_terminal_width()
        # Build bar content: left-justified location, right-justified score
        padding = width - len(left) - len(right)
        if padding < 1:
            padding = 1
        bar = " " + left + " " * (padding - 1) + right
        bar = bar[:width]

        w = sys.stdout.write
        w(_Ansi.SAVE_CUR)
        w(_Ansi.move_to(1))
        w(_Ansi.REVERSE + bar + _Ansi.RESET)
        w(_Ansi.RESTORE_CUR)
        sys.stdout.flush()

    def clear(self):
        if self.plain:
            return
        w = sys.stdout.write
        w(_Ansi.CLEAR + _Ansi.HOME)
        w(_Ansi.move_to(2))
        sys.stdout.flush()

    def reset(self):
        if self.plain:
            return
        sys.stdout.write(_Ansi.RESET)
        sys.stdout.flush()
