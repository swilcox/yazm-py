class ZUIStd:
    def __init__(self):
        pass

    def zoutput(self, text: str):
        print(text, end='', flush=True)

    def zinput(self) -> str:
        try:
            return input()
        except (EOFError, KeyboardInterrupt):
            raise SystemExit(0)

    def set_status_bar(self, left: str, right: str):
        pass

    def clear(self):
        pass

    def reset(self):
        pass
