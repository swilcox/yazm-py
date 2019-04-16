from __future__ import annotations
from dataclasses import dataclass
import sys

from zdata import ZData
from zheader import Header
from zdebug import ZDebugger
from zui_std import ZUIStd
import zscii


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
        self.undos = []
        self.redos = []
        self.separators = []
        self.dictionary = {}
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
                get_older(this, obj_id, next_)
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
        return 0
        #TODO: build!

    def set_attr(self, obj_id: int, attr: int):
        pass
        #TODO: build!

    def clear_attr(self, obj_id: int, attr: int):
        pass
        #TODO: build!

    def get_default_prop(self, property_number: int) -> int:
        pass
        #TODO: build!

    def read_object_prop(self, addr: int) -> ZObjectProperty:
        pass
        #TODO: build!

    def find_prop(self, obj_id: int, property_number: int) -> ZObjectProperty:
        pass
        #TODO: build!
    
    def get_prop_value(self, obj_id: int, property_number: int) -> int:
        pass
        #TODO: build!

    def get_prop_addr(self, obj_id: int, property_number: int) -> int:
        pass
        #TODO: build!

    def get_prop_len(self, obj_id: int, property_number: int) -> int:
        pass
        #TODO: build!

    def get_next_prop(self, obj_id: int, property_number: int) -> int:
        pass
        #TODO: build!

    def put_prop(self, obj_id: int, property_number: int, value: int):
        pass
        #TODO: build!

    def get_current_room(self) -> (int, str):
        pass
        #TODO: build!

    def get_status(self) -> (str, str):
        pass
        #TODO

    def make_save_state(self, pc: int) -> bytes:
        pass
        #TODO

    def restore_state(self, data: ZData):
        pass
        #TODO

    def undo(self) -> bool:
        pass
        #TODO

    def redo(self) -> bool:
        pass
        #TODO

    def get_arguments(self, operands: [int]) -> list:
        pass
        #TODO

    def return_from_routine(self, value: int):
        pass
        #TODO

    def process_branch(self, branch: Branch, next_: int, result: int):
        pass
        #TODO

    def process_result(self, instr: Instruction, value: int):
        pass
        #TODO

    def decode_instruction(self, addr: int) -> Instruction:
        pass
        #TODO

    def handle_instruction(self, instr: Instruction):
        pass
        #TODO

    def is_debug_command(self, input_: str) -> bool:
        return self.debugger.is_debug_command(input_)

    def run(self):
        pass
        #TODO

    def step(self) -> bool:
        #TODO
        pass

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
        if object == 0:
            return 0
        addr = self.get_object_addr(obj_id) + self.attr_width
        if self.version <= 3:
            return self.memory.u8(addr + 2)
        else:
            return self.memory.u16(addr + 4)

    def get_sibling(self, obj_id: int) -> int:
        if object == 0:
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
        # TODO: build out
        return 0

    def write_local(self, index: int, value: int):
        # TODO: build out
        pass

    def stack_push(self, value: int):
        # TODO: build out
        pass
    
    def stack_pop(self) -> int:
        # TODO: build out
        return 0

    def stack_peek(self) -> int:
        # TODO: build out
        return 0

    def read_variable(self, index: int) -> int:
        # TODO: build out
        return 0

    def read_indirect_variable(self, index: int) -> int:
        # TODO: build out
        return 0

    def write_variable(self, index: int, value: int):
        # TODO: build out
        pass

    def write_indirect_variable(self, index: int, value: int):
        # TODO: build out
        pass

    def get_abbrev(self, index: int) -> str:
        if index > 96:
            raise Exception(f'Bad Abbrev Index: {index}')
        offset = 2 * index
        word_addr = self.memory.u16(self.header.abbrev_addr + offset)
        addr = word_addr * 2
        self.read_zstring(addr)

    def zstring_length(self, addr: int) -> int:
        length = 0
        while self.memory.u16(addr + length) & 0x8000 == 0:
            length += 2
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

    
if __name__ == "__main__":
    with open(sys.argv[1], 'rb') as f:
        zdata = ZData(f.read())
    zmachine = ZMachine(zdata)

    zmachine.debugger.debug_object_tree()
    zmachine.debugger.debug_dictionary()
