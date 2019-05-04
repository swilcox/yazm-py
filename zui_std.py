class ZUIStd:
    def __init__(self):
        self._something = True

    def zoutput(self, text: str):
        print(text)

    def zinput(self) -> str:
        return input('> ')

    def set_status_bar(self, left: str, right: str):
        print(f'status bar --> {left} {right}')
