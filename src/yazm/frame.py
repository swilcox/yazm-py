from __future__ import annotations


class Frame:
    def __init__(self, resume: int, store: int, locals_: list, arguments: list):
        self.stack = []
        self.locals = []
        for i in range(len(locals_)):
            self.locals.append(locals_[i])
            if len(arguments) > i:
                self.locals[i] = arguments[i]
        self.arg_count = len(arguments)
        self.resume = resume
        self.store = store               

    def empty(self):
        self.stack = []
        self.locals = []
        self.arg_count = 0
        self.resume = 0
        self.store = None
    
    @classmethod
    def from_bytes(cls, bytes_: bytearray) -> Frame:
        resume = 0
        resume += (bytes_[0] << 16)
        resume += (bytes_[1] << 8)
        resume += bytes_[2]
        flags = bytes_[3]
        has_store = (flags & 0b0001_0000) == 0
        num_locals = flags & 0b0000_1111
        store = bytes_[4] if has_store else None
        mask = bytes_[5]
        arg_count = 0
        for bit in range(7):
            if (mask & (1 << bit)) != 0:
                arg_count += 1
        stack_length = 0
        stack_length += bytes_[6] << 8
        stack_length += bytes_[7]
        locals_ = []
        stack = []
        index = 8
        for offset in range(num_locals):
            word = 0
            word += bytes_[index + offset * 2] << 8
            word += bytes_[index + offset * 2 + 1] 
            locals_.append(word)
        
        index += num_locals * 2
        for offset in range(stack_length):
            word = 0
            word += bytes_[index + offset * 2] << 8
            word += bytes_[index + offset * 2 + 1] 
            stack.append(word)

        new_frame = cls(resume, store, locals_, [])
        new_frame.arg_count = arg_count
        return new_frame

    def read_local(self, index: int) -> int:
        return self.locals[index]

    def write_local(self, index: int, value: int):
        self.locals[index] = value
    
    def stack_push(self, value: int):
        self.stack.append(value)

    def stack_pop(self) -> int:
        return self.stack.pop()

    def stack_peek(self) -> int:
        return self.stack[-1]
    
    def to_string(self) -> str:
        return "--- to do ---"

    def to_list(self) -> list:
        bytes_ = []
        bytes_.append((self.resume & 0xFF_0000) >> 16)
        bytes_.append((self.resume & 0x00_FF00) >> 8)
        bytes_.append(self.resume & 0x00_00FF)
        flags = len(self.locals)
        if self.store:
            flags += 0b0001_0000
        args_supplied = 0
        for bit in range(self.arg_count):
            args_supplied |= 1 << bit
        bytes_.append(flags)
        bytes_.append(self.store or 0)
        bytes_.append(args_supplied)
        stack_length = len(self.stack)
        bytes_.append((stack_length & 0xFF00) >> 8)
        bytes_.append(stack_length & 0x00FF)
        for local in self.locals:
            bytes_.append((local & 0xFF00) >> 8)
            bytes_.append(local & 0x00FF)
        for var in self.stack:
            bytes_.append((var & 0xFF00) >> 8)
            bytes_.append(var & 0x00FF)
        return bytes_
