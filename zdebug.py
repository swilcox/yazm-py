from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from zmachine import ZMachine


class ZDebugger:
    def __init__(self, zm: ZMachine):
        self.zm = zm
        self._debug_commands = {
            '$help': (self.print_command_help, "this command"),
            '$dump': (self.debug_dump, "list stack frames and PC"),
            '$dict': (self.debug_dictionary, "show dictionary"),
            '$tree': (self.debug_object_tree, "show current object tree"),
            '$room': (self.debug_room, "show current room's sub-tree"),
            '$you': (self.debug_yourself, "show your sub-tree"),
            '$find': (self.debug_find_object, "find object from name"),
            '$object': (self.debug_object, "show object's sub-tree"),
            '$parent': (self.debug_parent, "show object's parent sub-tree"),
            '$simple': (self.debug_object_simple, "object info, simple view"),
            '$attrs': (self.debug_object_attributes, "list object attributes"),
            '$props': (self.debug_object_properties, "list object properties"),
            '$header': (self.debug_header, "show header information"),
            '$history': (self.debug_history, "list saved states"),
            '$have_attr': (self.debug_have_attributes, "list objects that have given attribute enabled"),
            '$undo': (self.debug_undo, ""),
            '$redo': (self.debug_redo, ""),
            '$teleport': (self.debug_teleport, ""),
            '$steal': (self.debug_steal, ""),
        }

    def is_debug_command(self, input_: str) -> bool:
        return input_ in self._debug_commands

    def print_command_help(self, *args, **kwargs):
        self.zm.ui.zoutput('\n'.join([f"{c} ({self._debug_commands[c][1]})" for c in self._debug_commands]))

    def handle_debug_command(self, input: str) -> bool:
        should_ask_again = True
        i, *args = input.lower().split()
        if i in self._debug_commands:
            self._debug_commands[i][0](*args)
            should_ask_again = False
        return should_ask_again

    def debug_undo(self, *args, **kwargs):
        pass

    def debug_redo(self, *args, **kwargs):
        pass

    def debug_header(self, *args, **kwargs):
        pass
        #TODO
        #self.zm.header.debug_out

    def debug_dictionary(self, *args, **kwargs):
        self.zm.ui.zoutput(' '.join([k for k in self.zm.dictionary]) + '\n')

    def debug_dump(self, *args, **kwargs):
        pass
        #TODO

    def debug_object_simple(self, obj_id: int, *args, **kwargs):
        pass
        #TODO

    def debug_object(self, input: str, *args, **kwargs):
        pass
        #TODO

    def debug_object_tree(self, *args, **kwargs):
        tree = self.zm.get_object_tree()
        self.zm.ui.zoutput(tree.print_tree("", 0, False))

    def debug_object_properties(self, input: str, *args, **kwargs):
        pass
        #TODO

    def debug_object_attributes(self, input: str, *args, **kwargs):
        pass
        #TODO

    def debug_object_details(self, input: str, *args, **kwargs):
        pass
        #TODO

    def debug_have_attributes(self, attr_str: str, *args, **kwargs):
        pass
        #TODO

    def debug_have_property(self, prop_str: str, *args, **kwargs):
        pass
        #TODO

    def debug_room(self, *args, **kwargs):
        pass
        #TODO

    def debug_yourself(self, *args, **kwargs):
        pass
        #TODO

    def debug_parent(self, input: str, *args, **kwargs):
        pass
        #TODO
    
    def debug_find_object(self, name: str, *args, **kwargs):
        pass
        #TODO

    def debug_teleport(self, input: str, *args, **kwargs):
        pass
        #TODO

    def debug_steal(self, input: str, *args, **kwargs):
        pass
        #TODO

    def debug_history(self, *args, **kwargs):
        pass
        #TODO

    def debug_routine(self, *args, **kwargs):
        pass
        #TODO
