

class ParseError(Exception):
    def __init__(self, line_number: int, msg: str) -> None:
        self.line_number = line_number
        self.msg = msg
        super().__init__(f"{line_number}: {msg}")
