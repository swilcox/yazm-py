class ZUIStd:
    def __init__(self):
        self._something = True

    def zoutput(self, text: str):
        print(text)

    def zinput(self) -> str:
        return input('> ')
