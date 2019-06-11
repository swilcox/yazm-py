from __future__ import annotations
from enum import Enum, IntFlag, IntEnum
from typing import List


class OpForm(Enum):
    EXT = 1
    VAR = 2
    SHORT = 3
    LONG = 4


class OperandCount(Enum):
    ZERO = 0
    ONE = 1
    TWO = 2
    VAR = 3


class OperandType(IntFlag):
    SMALL = 0
    LARGE = 1
    VARIABLE = 2
    OMITTED = 4

    @classmethod
    def from_bytes(cls, bytes_: bytes) -> List[OperandType]:
        return []


class Operand(IntFlag):
    LARGE = 0b00
    SMALL = 0b01
    VARIABLE = 0b10


# class OpSize(Enum):
#     WORD = 0b00
#     BYTE = 0b01
#     VAR = 0b10


class StatusLineType(IntFlag):
    score = 0
    time_based = 1


BASE_OPCODE_NAMES = {
    'OP2_1': 'je',
    'OP2_2': 'jl',
    'OP2_3': 'jg',
    'OP2_4': 'dec_chk',
    'OP2_5': 'inc_chk',
    'OP2_6': 'jin',
    'OP2_7': 'test',
    'OP2_8': 'or',
    'OP2_9': 'and',
    'OP2_10': 'test_attr',
    'OP2_11': 'set_attr',
    'OP2_12': 'clear_attr',
    'OP2_13': 'store',
    'OP2_14': 'insert_obj',
    'OP2_15': 'loadw',
    'OP2_16': 'loadb',
    'OP2_17': 'get_prop',
    'OP2_18': 'get_prop_addr',
    'OP2_19': 'get_next_prop',
    'OP2_20': 'add',
    'OP2_21': 'sub',
    'OP2_22': 'mul',
    'OP2_23': 'dev',
    'OP2_24': 'mod',
    'OP2_25': 'call_2s',
    'OP2_26': 'call_2n',
    'OP2_27': 'set_colour',
    'OP2_28': 'throw',
    'OP1_128': 'jz',
    'OP1_130': 'get_sibling',
    'OP1_131': 'get_parent',
    'OP1_132': 'get_prop_len',
    'OP1_133': 'inc',
    'OP1_134': 'dec',
    'OP1_135': 'print_addr',
    'OP1_136': 'call_1s',
    'OP1_137': 'remove_obj',
    'OP1_138': 'print_obj',
    'OP1_139': 'ret',
    'OP1_140': 'jump',
    'OP1_141': 'print_paddr',
    'OP1_142': 'load',
    'OP1_143': 'not',
    'OP0_176': 'rtrue',
    'OP0_177': 'rfalse',
    'OP0_178': 'print',
    'OP0_179': 'print_ret',
    'OP0_180': 'nop',
    'OP0_181': 'save',
    'OP0_182': 'restore',
    'OP0_183': 'restart',
    'OP0_184': 'ret_popped',
    'OP0_185': 'pop',
    'OP0_186': 'quit',
    'OP0_187': 'new_line',
    'OP0_188': 'show_status',
    'OP0_189': 'verify',
    'OP0_191': 'piracy',
    'VAR_224': 'call',
    'VAR_225': 'storew',
    'VAR_226': 'storeb',
    'VAR_227': 'put_prop',
    'VAR_228': 'sread',
    'VAR_229': 'print_char',
    'VAR_230': 'print_num',
    'VAR_231': 'random',
    'VAR_232': 'push',
    'VAR_233': 'pull',
    'VAR_234': 'split_window',
    'VAR_235': 'set_window',
    'VAR_236': 'call_vs2',
    'VAR_237': 'erase_window',
    'VAR_238': 'erase_line',
    'VAR_239': 'set_cursor',
    'VAR_240': 'get_cursor',
    'VAR_241': 'set_text_style',
    'VAR_242': 'buffer_mode',
    'VAR_243': 'output_stream',
    'VAR_244': 'input_stream',
    'VAR_245': 'sound_effect',
    'VAR_246': 'read_char',
    'VAR_247': 'scan_table',
    'VAR_248': 'not',
    'VAR_249': 'call_vn',
    'VAR_250': 'call_vn2',
    'VAR_251': 'tokenise',
    'VAR_252': 'encode_text',
    'VAR_253': 'copy_table',
    'VAR_254': 'print_table',
    'VAR_255': 'check_arg_count',
    'EXT_1000': 'save',
    'EXT_1001': 'restore',
    'EXT_1002': 'log_shift',
    'EXT_1003': 'art_shift',
    'EXT_1004': 'set_font',
    'EXT_1005': 'draw_picture',
    'EXT_1006': 'picture_data',
    'EXT_1007': 'erase_picture',
    'EXT_1008': 'set_margins',
    'EXT_1009': 'save_undo',
    'EXT_1010': 'restore_undo',
    'EXT_1011': 'print_unicode',
    'EXT_1012': 'check_unicode',
    'EXT_1013': 'set_true_color',
    'EXT_1016': 'move_window',
    'EXT_1017': 'window_size',
    'EXT_1018': 'window_style',
    'EXT_1019': 'get_wind_prop',
    'EXT_1020': 'scroll_window',
    'EXT_1021': 'pop_stack',
    'EXT_1022': 'read_mouse',
    'EXT_1023': 'mouse_window',
    'EXT_1024': 'push_stack',
    'EXT_1025': 'put_wind_prop',
    'EXT_1026': 'print_form',
    'EXT_1027': 'make_menu',
    'EXT_1028': 'picture_table',
    'EXT_1029': 'buffer_screen'
}


V5_OVERRIDES = {
    'OP1_143': 'call_1n',
    'OP0_185': 'catch',
    'VAR_224': 'call_vs',
    'VAR_228': 'aread',
}


OPCODE_NAMES = BASE_OPCODE_NAMES
V5_OPCODE_NAMES = BASE_OPCODE_NAMES.copy()
V5_OPCODE_NAMES.update(V5_OVERRIDES)


class Opcode(IntEnum):
    # Two-operand opcodes (2OP)
    OP2_1  = 1
    OP2_2  = 2
    OP2_3  = 3
    OP2_4  = 4
    OP2_5  = 5
    OP2_6  = 6
    OP2_7  = 7
    OP2_8  = 8
    OP2_9  = 9
    OP2_10 = 10
    OP2_11 = 11
    OP2_12 = 12
    OP2_13 = 13
    OP2_14 = 14
    OP2_15 = 15
    OP2_16 = 16
    OP2_17 = 17
    OP2_18 = 18
    OP2_19 = 19
    OP2_20 = 20
    OP2_21 = 21
    OP2_22 = 22
    OP2_23 = 23
    OP2_24 = 24
    OP2_25 = 25
    OP2_26 = 26
    OP2_27 = 27
    OP2_28 = 28
    # One-operand opcodes (1OP)
    OP1_128 = 128
    OP1_129 = 129
    OP1_130 = 130
    OP1_131 = 131
    OP1_132 = 132
    OP1_133 = 133
    OP1_134 = 134
    OP1_135 = 135
    OP1_136 = 136
    OP1_137 = 137
    OP1_138 = 138
    OP1_139 = 139
    OP1_140 = 140
    OP1_141 = 141
    OP1_142 = 142
    OP1_143 = 143
    # Zero-operand opcodes (0OP)
    OP0_176 = 176
    OP0_177 = 177
    OP0_178 = 178
    OP0_179 = 179
    OP0_180 = 180
    OP0_181 = 181
    OP0_182 = 182
    OP0_183 = 183
    OP0_184 = 184
    OP0_185 = 185
    OP0_186 = 186
    OP0_187 = 187
    OP0_188 = 188
    OP0_189 = 189
    OP0_191 = 191
    # Variable-operand opcodes (VAR)
    VAR_224 = 224
    VAR_225 = 225
    VAR_226 = 226
    VAR_227 = 227
    VAR_228 = 228
    VAR_229 = 229
    VAR_230 = 230
    VAR_231 = 231
    VAR_232 = 232
    VAR_233 = 233
    VAR_234 = 234
    VAR_235 = 235
    VAR_236 = 236
    VAR_237 = 237
    VAR_238 = 238
    VAR_239 = 239
    VAR_240 = 240
    VAR_241 = 241
    VAR_242 = 242
    VAR_243 = 243
    VAR_244 = 244
    VAR_245 = 245
    VAR_246 = 246
    VAR_247 = 247
    VAR_248 = 248
    VAR_249 = 249
    VAR_250 = 250
    VAR_251 = 251
    VAR_252 = 252
    VAR_253 = 253
    VAR_254 = 254
    VAR_255 = 255
    # Extended opcodes (EXT)
    EXT_1000 = 1000
    EXT_1001 = 1001
    EXT_1002 = 1002
    EXT_1003 = 1003
    EXT_1004 = 1004
    EXT_1005 = 1005
    EXT_1006 = 1006
    EXT_1007 = 1007
    EXT_1008 = 1008
    EXT_1009 = 1009
    EXT_1010 = 1010
    EXT_1011 = 1011
    EXT_1012 = 1012
    EXT_1013 = 1013
    EXT_1016 = 1016
    EXT_1017 = 1017
    EXT_1018 = 1018
    EXT_1019 = 1019
    EXT_1020 = 1020
    EXT_1021 = 1021
    EXT_1022 = 1022
    EXT_1023 = 1023
    EXT_1024 = 1024
    EXT_1025 = 1025
    EXT_1026 = 1026
    EXT_1027 = 1027
    EXT_1028 = 1028
    EXT_1029 = 1029

    @property
    def zop(self):
        return OPCODE_NAMES[self.name]
