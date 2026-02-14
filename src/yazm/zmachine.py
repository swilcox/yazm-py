from __future__ import annotations
from dataclasses import dataclass
from random import Random
from typing import List
import sys

from .enums import StatusLineType, OperandType
from .frame import Frame
from .options import Options
from .zdata import ZData
from .zheader import Header
from .zinstruction import Branch, Instruction
from .zdebug import ZDebugger
from .zui_std import ZUIStd
from . import zscii


class ZObject(object):
    def __init__(self, number, zm: ZMachine):
        self.number = number
        self.name = zm.get_object_name(number) if number else "(Null Object)"
        if not self.name:
            self.name = "(No Name)"
        self.children = []

    def print_tree(self, indent: str, depth: int, is_last: bool) -> str:
        """print out a tree representation of the object and its children"""
        next_ = indent
        out = ""
        if depth == 0:
            out += f"{self.name} ({self.number})\n"
        else:
            _tree_chr = "└" if is_last else "├"
            out += f"{indent}{_tree_chr}── {self.name} ({self.number})\n"
            next_ += "    " if is_last else "|   "
        depth += 1
        for (i, child) in enumerate(self.children):
            is_last_child = i == len(self.children) - 1
            out += child.print_tree(next_, depth, is_last_child)
        return out


@dataclass
class ZObjectProperty:
    number: int = 0
    length: int = 0
    addr: int = 0
    next_: int = 0


class ZMachine(object):
    """ZMachine Class"""

    def __init__(self, raw_data: bytes):
        self.memory = ZData(raw_data)
        self.initial_pc = self.header.pc
        self.pc = self.header.pc
        self.version = self.header.version
        self.obj_size = 9 if self.version <= 3 else 14
        self.attr_width = 4 if self.version <= 3 else 6
        self._prop_offset = 3 if self.version <= 3 else 6
        self.debugger = ZDebugger(self)
        self.ui = ZUIStd()
        self.current_state = None
        self.save_name = ''
        self.save_dir = ''
        self.original_dynamic = bytearray([])
        self.options = Options.default()
        self.undos = []
        self.redos = []
        self.frames = [Frame(0, None, [], [])]  # initial/main frame
        self.separators = []
        self.rng = Random()
        self.rng.seed(self.options.rand_seed)
        self.dictionary = {}
        self.running = False
        self.populate_dictionary()
        
    @property
    def header(self) -> Header:
        return Header(self.memory)

    def calculate_checksum(self):
        """calculates the checksum"""
        sum = 0
        for i in range(0x40, self.header.file_length):
            sum += self.memory.u8(i)
        return sum % 0x1_0000

    def get_object_addr(self, obj_id: int) -> int:
        """get the actual zmachine memory address for an object based on its id."""
        if obj_id:
            return self.header.obj_table_addr + ((obj_id - 1) * self.obj_size)
        else:
            return self.header.obj_table_addr
    
    def get_object_prop_table_addr(self, obj_id: int) -> int:
        """get the zmachine memory address for an object's properties"""
        return self.memory.u16(self.get_object_addr(obj_id) + self.attr_width + self._prop_offset)

    def get_object_name(self, obj_id: int) -> str:
        """get the name of an object"""
        addr = self.get_object_prop_table_addr(obj_id)
        text_length = self.memory.u8(addr)
        return self.read_zstring(addr + 1) if text_length else ""

    def get_total_object_count(self) -> int:
        """
        get the total number of objects
        NOTE: by convention, the property table for object #1 is located AFTER
        the last object in the object table:
        """
        obj_table_end = self.get_object_prop_table_addr(1)
        return (obj_table_end - self.header.obj_table_addr) // self.obj_size

    def remove_obj(self, obj_id: int):
        parent = self.get_parent(obj_id)
        if parent == 0:
            return
        
        parents_first_child = self.get_child(parent)
        younger_sibling = self.get_sibling(obj_id)

        def get_older(this: ZMachine, obj_id: int, prev: int):
            next_ = this.get_sibling(prev)
            if next_ == obj_id:
                return prev
            else:
                return get_older(this, obj_id, next_)
        if obj_id == parents_first_child:
            self.set_child(parent, younger_sibling)
        else:
            older_sibling = get_older(self, obj_id, parents_first_child)
            self.set_sibling(older_sibling, younger_sibling)
        self.set_parent(obj_id, 0)
        self.set_sibling(obj_id, 0)

    def insert_obj(self, obj_id: int, destination: int):
        parents_first_child = self.get_child(destination)
        if parents_first_child == obj_id:
            return
        self.remove_obj(obj_id)
        self.set_parent(obj_id, destination)
        self.set_child(destination, obj_id)
        self.set_sibling(obj_id, parents_first_child) 

    def find_object(self, name: str) -> int:
        for i in range(1, self.get_total_object_count() + 1):
            if self.get_object_name(i).lower() == name.lower():
                return i
        return None

    def find_yourself(self) -> int:
        return self.find_object('cretin') or self.find_object('you') or self.find_object('yourself')

    def test_attr(self, obj_id: int, attr: int) -> int:
        if attr > self.attr_width * 8:
            raise Exception(f"Can't test out-of-bounds attribute: {attr}")
        addr = self.get_object_addr(obj_id) + attr // 8
        byte = self.memory.u8(addr)
        bit = attr % 8
        return 1 if byte & (128 >> bit) != 0 else 0

    def set_attr(self, obj_id: int, attr: int):
        if attr > self.attr_width * 8:
            raise Exception(f"Can't set out-of-bounds attribute: {attr}")
        addr = self.get_object_addr(obj_id) + attr // 8
        byte = self.memory.u8(addr)
        bit = attr % 8
        self.memory.write_u8(addr, byte | (128 >> bit))

    def clear_attr(self, obj_id: int, attr: int):
        if attr > self.attr_width * 8:
            raise Exception(f"Can't set out-of-bounds attribute: {attr}")
        addr = self.get_object_addr(obj_id) + attr // 8
        byte = self.memory.u8(addr)
        bit = attr % 8
        self.memory.write_u8(addr, byte & ~(128 >> bit))

    def get_default_prop(self, property_number: int) -> int:
        word_index = (property_number - 1)
        addr = self.header.obj_table_addr - (31 if self.version <= 3 else 63) * 2 + word_index * 2
        return self.memory.u16(addr)

    def read_object_prop(self, addr: int) -> ZObjectProperty:
        header = self.memory.u8(addr)
        length = 0
        num = 0
        value_addr = 0
        if 1 <= self.version <= 3:
            num = header % 32
            length = header // 32 + 1
            value_addr = addr + 1
        else:
            num = header & 0b0011_1111
            if header & 0b1000_0000 != 0:
                length = self.memory.u8(addr + 1) & 0b0011_1111
                if length == 0:
                    length = 64
            else:
                length = 2 if header & 0b0100_0000 != 0 else 1
                value_addr = addr + 1
        
        return ZObjectProperty(
            number=num,
            length=length,
            addr=value_addr,
            next_=value_addr + length
        )

    def find_prop(self, obj_id: int, property_number: int) -> ZObjectProperty:
        if property_number == 0:
            return ZObjectProperty()
        
        addr = self.get_object_prop_table_addr(obj_id)
        str_length = self.memory.u8(addr) * 2
        first_addr = addr + str_length + 1
        prop = self.read_object_prop(first_addr)
        while prop.number != 0 and prop.number != property_number:
            if property_number > prop.number:
                return ZObjectProperty()
            prop = self.read_object_prop(prop.next_)
        return prop
    
    def get_prop_value(self, obj_id: int, property_number: int) -> int:
        prop = self.find_prop(obj_id, property_number)
        if prop.number == 0:
            return self.get_default_prop(property_number)
        elif prop.length == 1:
            return self.memory.u8(prop.addr)
        return self.memory.u16(prop.addr)

    def get_prop_addr(self, obj_id: int, property_number: int) -> int:
        prop = self.find_prop(obj_id, property_number)
        return prop.addr if prop.number != 0 else 0

    def get_prop_len(self, prop_data_addr: int) -> int:
        if prop_data_addr == 0:
            return 0
        prop_header = self.memory.u8(prop_data_addr - 1)
        if self.version <= 3:
            return prop_header // 32 + 1
        elif prop_header & 0b1000_0000 != 0:
            result = prop_header & 0b0011_1111
            return 64 if result == 0 else result
        elif prop_header & 0b0100_0000 != 0:
            return 2
        return 1

    def get_next_prop(self, obj_id: int, property_number: int) -> int:
        if property_number == 0:
            addr = self.get_object_prop_table_addr(obj_id)
            str_length = self.memory.u8(addr) * 2
            first_prop = addr + str_length + 1
            return self.read_object_prop(first_prop).number
        prop = self.find_prop(obj_id, property_number)
        return self.read_object_prop(prop.next_).number

    def put_prop(self, obj_id: int, property_number: int, value: int):
        prop = self.find_prop(obj_id, property_number)
        if prop.length == 1:
            self.memory.write_u8(prop.addr, value)
        else:
            self.memory.write_u16(prop.addr, value)

    # Encrusted Web UI Only... 
    def get_current_room(self) -> (int, str):
        num = self.read_global(0)
        name = self.get_object_name(num)
        return (num, name)

    def get_status(self) -> (str, str):
        num = self.read_global(0)
        left = self.get_object_name(num)
        if self.header.flag1.status_line_type == StatusLineType.score:
            score = self.read_global(1)
            turns = self.read_global(2)
            right = f"{score}/{turns}"
        else:
            hours = self.read_global(1)
            minutes = self.read_global(2)
            am_pm = "PM" if hours >= 12 else "AM"
            if hours > 12:
                hours -= 12
            right = f"{hours:02}:{minutes:02} {am_pm}"
        return (left, right)

    def update_status_bar(self):
        if self.version > 3:
            return
        left, right = self.get_status()
        self.ui.set_status_bar(left, right)

    def make_save_state(self, pc: int) -> bytes:
        dynamic = self.memory[0: self.header.static_memory_addr]
        # original = self.original_dynamic.as_slice()
        frames = self.frames
        chksum = self.header.checksum
        release = self.header.release
        serial = self.header.serial_number
        ## QuetzalSave::make(pc, dynamic, original, frames, chksum, relase, serial)
        # TODO: finish this!

    def restore_state(self, data: ZData):
        ## save = QuetzalSave::from_bytes(data, self.original_dynamic)
        #if save.checksum != self.header.checksum:
        #    raise Exception('Invalid Checksum!')
        #if self.static_memory_addr < len(save.memory):
        #    raise Exception('Invalid save, memory is too long!')
        #self.pc = save.pc
        #self.frames = save.frames
        #self.memory.write(0, save.memory.as_slice())
        ...
        #TODO: implement
        
    def undo(self) -> bool:
        ...
        return False        
        #TODO

    def redo(self) -> bool:
        ...
        return False
        #TODO

    def get_arguments(self, operands, optypes: List[OperandType]) -> list:
        arguments = []
        for i, op in enumerate(operands):
            if optypes[i] == OperandType.VARIABLE:
                arguments.append(self.read_variable(op))
            else:
                arguments.append(op)
        return arguments

    def return_from_routine(self, value: int):
        frame = self.frames.pop()
        self.pc = frame.resume
        if frame.store is not None:
            self.write_variable(frame.store, value)

    def process_branch(self, branch: Branch, next_: int, result: bool):
        do_branch = (result and branch.condition) or (not result and not branch.condition)
        if do_branch:
            if branch.returns is not None:
                self.return_from_routine(branch.returns)
            else:
                self.pc = branch.address
        else:
            self.pc = next_

    def process_result(self, instr: Instruction, value: int):
        if instr.store is not None:
            self.write_variable(instr.store, value & 0xFFFF)
        if instr.branch is not None:
            self.process_branch(instr.branch, instr.next_, bool(value))
        else:
            self.pc = instr.next_

    def decode_instruction(self, addr: int) -> Instruction:
        return Instruction.decode(self, addr)

    def handle_instruction(self, instr: Instruction):
        from .ops import dispatch
        args = self.get_arguments(instr.operands, instr.optypes)
        dispatch(self, instr, args)

    def is_debug_command(self, input_: str) -> bool:
        return self.debugger.is_debug_command(input_)

    def run(self):
        self.running = True
        while self.running:
            instr = self.decode_instruction(self.pc)
            self.handle_instruction(instr)

    def handle_input(self, input_: str):
        # TODO: if self.paused_instr...
        if self.is_debug_command(input_):
            if self.debugger.handle_debug_command(input_):
                self.ui.zoutput("\n")  # possibly another prompt...
            return
        # empty redos
        # check current state
        # move into undos
        # handle read
        # advance pc to next

    def restore(self, data: bytes):
        #TODO
        pass

    def load_savestate(self, data: str):
        #TODO
        pass

    def get_parent(self, obj_id: int) -> int:
        if obj_id == 0:
            return 0
        addr = self.get_object_addr(obj_id) + self.attr_width
        if self.version <= 3:
            return self.memory.u8(addr)
        else:
            return self.memory.u16(addr)

    def set_parent(self, obj_id: int, parent: int):
        addr = self.get_object_addr(obj_id) + self.attr_width
        if self.version <= 3:
            self.memory.write_u8(addr, parent)
        else:
            self.memory.write_u16(addr, parent)

    def get_child(self, obj_id: int) -> int:
        if obj_id == 0:
            return 0
        addr = self.get_object_addr(obj_id) + self.attr_width
        if self.version <= 3:
            return self.memory.u8(addr + 2)
        else:
            return self.memory.u16(addr + 4)

    def get_sibling(self, obj_id: int) -> int:
        if obj_id == 0:
            return 0
        addr = self.get_object_addr(obj_id) + self.attr_width
        if self.version <= 3:
            return self.memory.u8(addr + 1)
        return self.memory.u16(addr + 2)

    def set_sibling(self, obj_id: int, sibling_id: int):
        addr = self.get_object_addr(obj_id) + self.attr_width
        if self.version <= 3:
            self.memory.write_u8(addr + 1, sibling_id)
        else:
            self.memory.write_u16(addr + 2, sibling_id)

    def set_child(self, obj_id: int, child_id: int):
        addr = self.get_object_addr(obj_id) + self.attr_width
        if self.version <= 3:
            self.memory.write_u8(addr + 2, child_id)
        else:
            self.memory.write_u16(addr + 4, child_id)

    def add_object_children(self, parent: ZObject):
        next_ = self.get_child(parent.number)
        while next_ > 0:
            parent.children.append(ZObject(next_, self))
            next_ = self.get_sibling(next_)
        for child in parent.children:
            self.add_object_children(child)

    def get_object_tree(self) -> ZObject:
        root = ZObject(0, self)
        for i in range(1, self.get_total_object_count() + 1):
            if self.get_parent(i) == 0:
                root.children.append(ZObject(i, self))

        for zobject in root.children:
            self.add_object_children(zobject)       

        return root

    def read_packed_string(self, addr: int) -> list:
        packed_string = []
        while True:
            word = self.memory.u16(addr)
            packed_string.append(word)
            if word & 0x8000:
                break
            addr += 2
        return packed_string

    def read_zstring(self, addr: int) -> str:
        """get a zstring from a memory address"""
        packed_str = self.read_packed_string(addr)
        return zscii.unpack_string(self, packed_str)

    def unpack(self, addr: int) -> int:
        if self.version in [1, 2, 3]:
            return addr * 2
        elif self.version in [4, 5, 6, 7]:
            return addr * 4
        elif self.version == 8:
            return addr * 8
    
    def unpack_routine_addr(self, addr: int) -> int:
        x_addr = self.unpack(addr)
        if x_addr in [6, 7]:
            return x_addr + self.header.routine_offset * 8
        return x_addr

    def unpack_print_paddr(self, addr: int) -> int:
        x_addr = self.unpack(addr)
        if x_addr in [6, 7]:
            return x_addr + self.header.string_offset * 8
        return x_addr

    def read_global(self, index: int) -> int:
        if index > 240:
            raise Exception(f"can't read global {index}")
        addr = self.header.global_variable_addr + index * 2
        return self.memory.u16(addr)
        
    def write_global(self, index: int, value: int):
        if index > 240:
            raise Exception(f"can't write global {index}")
        addr = self.header.global_variable_addr + index * 2
        self.memory.write_u16(addr, value)

    def read_local(self, index: int) -> int:
        return self.frames[-1].read_local(index)

    def write_local(self, index: int, value: int):
        self.frames[-1].write_local(index, value)

    def stack_push(self, value: int):
        self.frames[-1].stack_push(value)
    
    def stack_pop(self) -> int:
        return self.frames[-1].stack_pop()

    def stack_peek(self) -> int:
        return self.frames[-1].stack_peek()

    def read_variable(self, index: int) -> int:
        if index == 0:
            return self.stack_pop()
        elif 1 <= index <= 15:
            return self.read_local(index - 1)
        elif 16 <= index <= 255:
            return self.read_global(index - 16)
        raise Exception('unreachable variable!')

    def read_indirect_variable(self, index: int) -> int:
        if index == 0:
            return self.stack_peek()
        elif 1 <= index <= 15:
            return self.read_local(index - 1)
        elif 16 <= index <= 255:
            return self.read_global(index - 16)
        raise Exception('unreachable indirect variable')

    def write_variable(self, index: int, value: int):
        if index == 0:
            self.stack_push(value)
        elif 1 <= index <= 15:
            self.write_local(index - 1, value)
        elif 16 <= index <= 255:
            self.write_global(index - 16, value)
        else:
            raise Exception('unreachable variable')

    def write_indirect_variable(self, index: int, value: int):
        if index == 0:
            self.stack_pop()
            self.stack_push(value)
        elif 1 <= index <= 15:
            self.write_local(index - 1, value)
        elif 16 <= index <= 255:
            self.write_global(index - 16, value)
        else:
            raise Exception('unreachable indirect variable')

    def get_abbrev(self, index: int) -> str:
        if index > 96:
            raise Exception(f'Bad Abbrev Index: {index}')
        offset = 2 * index
        word_addr = self.memory.u16(self.header.abbrev_addr + offset)
        addr = word_addr * 2
        return self.read_zstring(addr)

    def zstring_length(self, addr: int) -> int:
        length = 0
        while self.memory.u16(addr + length) & 0x8000 == 0:
            length += 2
        length += 2  # include the final word
        return length
 
    def populate_dictionary(self):
        addr = self.header.dict_addr
        separator_count = self.memory.u8(addr)
        for _ in range(0, separator_count):
            addr += 1
            self.separators.append(self.memory.u8(addr))
        addr += 1
        entry_length = self.memory.u8(addr)
        addr += 1
        entry_count = self.memory.u16(addr)
        addr += 2
        
        for n in range(0, entry_count):
            addr_ = addr + n * entry_length
            entry = self.read_zstring(addr_)
            self.dictionary[entry] = addr_

    def check_dictionary(self, word: str) -> int:
        length = 6 if self.version <= 3 else 9
        return self.dictionary.get(word[:length], 0)

    def tokenise(self, text: str, parse_addr: int):
        start = 1 if self.version <= 4 else 2
        input_str = text
        found = {}
        for sep in self.separators:
            input_str = input_str.replace(chr(sep), f"  ")
        token_list = [t for t in input_str.split() if len(t.strip())]
        tokens = []
        for token in token_list:
            offset = found.get(token, 0)
            position = text[offset:].find(token)
            dict_addr = self.check_dictionary(token)
            token_addr = offset + position + start
            found[token] = offset + position + len(token)
            tokens.append((dict_addr, len(token), token_addr))

        write = self.memory.get_writer(parse_addr + 1)
        write.byte(len(tokens))
        for token in tokens:
            d_addr, length, t_addr = token
            write.word(d_addr)
            write.byte(length)
            write.byte(t_addr)

    def do_call(self, instr: Instruction, addr: int, args: List[int]):
        if addr == 0:
            self.process_result(instr, 0)
            return
        routine_addr = self.unpack_routine_addr(addr)
        read = self.memory.get_reader(routine_addr)
        count = read.byte()
        locals_ = []
        for _ in range(count):
            if self.version <= 4:
                locals_.append(read.word())
            else:
                locals_.append(0)
        first_instr = read.position
        frame = Frame(instr.next_, instr.store, locals_, args)
        self.pc = first_instr
        self.frames.append(frame)


if __name__ == "__main__":
    with open(sys.argv[1], 'rb') as f:
        data = f.read()
    zmachine = ZMachine(data)
    zmachine.run()
