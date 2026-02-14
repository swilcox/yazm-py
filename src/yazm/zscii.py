from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .zmachine import ZMachine

DEFAULT_A0 = 'abcdefghijklmnopqrstuvwxyz'
DEFAULT_A1 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
DEFAULT_A2 = """ \n0123456789.,!?_#'"/\\-:()"""
DEFAULT_A2_Z1 = """ 0123456789.,!?_#'"/\\<-:()"""

DEFAULT_UNICODE_TABLE = dict([
    (155, 0xe4), (156, 0xf6), (157, 0xfc),
    (158, 0xc4), (159, 0xd6), (160, 0xdc),
    (161, 0xdf), (162, 0xbb), (163, 0xab),
    (164, 0xeb), (165, 0xef), (166, 0xff),
    (167, 0xcb), (168, 0xcf),
    (169, 0xe1), (170, 0xe9), (171, 0xed), (172, 0xf3), (173, 0xfa), (174, 0xfd),
    (175, 0xc1), (176, 0xc9), (177, 0xcd), (178, 0xd3), (179, 0xda), (180, 0xdd),
    (181, 0xe0), (182, 0xe8), (183, 0xec), (184, 0xf2), (185, 0xf9),
    (186, 0xc0), (187, 0xc8), (188, 0xcc), (189, 0xd2), (190, 0xd9),
    (191, 0xe2), (192, 0xea), (193, 0xee), (194, 0xf4), (195, 0xfb),
    (196, 0xc2), (197, 0xca), (198, 0xce), (199, 0xd4), (200, 0xdb),
    (201, 0xe5), (202, 0xc5), (203, 0xf8), (204, 0xd8),
    (205, 0xe3), (206, 0xf1), (207, 0xf5),
    (208, 0xc3), (209, 0xd1), (210, 0xd5),
    (211, 0xe6), (212, 0xc6), (213, 0xe7), (214, 0xc7),
    (215, 0xfe), (216, 0xf0), (217, 0xde), (218, 0xd0),
    (219, 0xa3),
    (220, 0x153), (221, 0x152),
    (222, 0xa1), (223, 0xbf)
])


def zscii_to_ascii(zm: ZMachine, chrs: bytes) -> str:
    """convert zscii characters to an ascii string"""
    result = []
    for c in chrs:
        if c == 0:
            # 0 == no effect in zscii (S 3.8.2.1)
            continue
        if c == ord('\r'):
            result.append('\n')
        elif c >= 32 and c <= 126:
            result.append(chr(c))
        elif c >= 155 and c <= 251:
            if zm.header.unicode_tab_addr:
                unitable_len = zm.memory[zm.header.unicode_tab_addr]
                if (c - 155) < len(unitable_len):
                    result.append(chr(zm.memory.u16(zm.header.unicode_tab_addr + (c - 155))))
                else:
                    # TODO: note/log this as an error!
                    result.append('?')
            else:
                if c in DEFAULT_UNICODE_TABLE:
                    result.append(chr(DEFAULT_UNICODE_TABLE[c]))
                else:
                    # TODO: note/log this as an error!
                    result.append('?')
        elif (c >= 0 and c <= 12) or (c >= 14 and c <= 31) or (c >= 127 and c <= 154) or (c >= 252):
            # TODO: note/log this as an error!
            pass
    return ''.join(result)


def unpack_string(zm, packed_text):

    split_text = []
    for word in packed_text:
        split_text += [word >> 10 & 0x1f,
                       word >> 5 & 0x1f,
                       word & 0x1f]

    if zm.version >= 5 and zm.header.alpha_tab_addr:
        base = zm.header.alpha_tab_addr
        A0 = ''.join(map(chr, list(zm.memory[base + 0 * 26 : base + 1 * 26])))
        A1 = ''.join(map(chr, list(zm.memory[base + 1 * 26 : base + 2 * 26])))
        A2 = ''.join(map(chr, list(zm.memory[base + 2 * 26 : base + 3 * 26])))
    else:
        A0 = DEFAULT_A0
        A1 = DEFAULT_A1
        A2 = DEFAULT_A2

    if zm.version == 1:
        A2 = DEFAULT_A2_Z1

    shift_table = {
            2: {A0:A1, A1:A2, A2:A0},
            3: {A0:A2, A1:A0, A2:A1},
            4: {A0:A1, A1:A2, A2:A0},
            5: {A0:A2, A1:A0, A2:A1},
    }

    text = []
    current_alphabet = A0
    last_alphabet = A0
    temp_shift = 0
    abbrev_shift = 0
    current_10bit = 0
    mode = 'NONE'
    for char in split_text:
        if abbrev_shift > 0:
            table_addr = zm.header.abbrev_addr
            entry_addr = table_addr + 2 * (32 * (abbrev_shift - 1) + char)
            word_addr = zm.memory.u16(entry_addr)
            packed_string = zm.read_packed_string(word_addr*2)
            text += unpack_string(zm, packed_string)
            abbrev_shift = 0
        elif mode == '10BIT_HIGH':
            mode = '10BIT_LOW'
            current_10bit = char << 5
        elif mode == '10BIT_LOW':
            mode = 'NONE'
            current_10bit |= char
            text += zscii_to_ascii(zm, [current_10bit])
        elif char == 0:
            text.append(' ')
        elif char == 6 and current_alphabet == A2: # override any custom alpha with escape seq start
            mode = '10BIT_HIGH'
        elif zm.version > 1 and char == 7 and current_alphabet == A2: # override any custom alpha with newline
            text.append('\n')
        elif zm.version < 3:
            if char == 1:
                if zm.version == 1:
                    text.append('\n')
                else:
                    abbrev_shift = char
            elif char in [2, 3, 4, 5]:
                last_alphabet = current_alphabet
                current_alphabet = shift_table[char][current_alphabet]
                if char in [2, 3]:
                    temp_shift = 1
                else:
                    temp_shift = 0 # don't unshift when shift locking, even if preceded by temp_shift
            else:
                text.append(current_alphabet[char - 6])
        else:
            if char in [1, 2, 3]:
                abbrev_shift = char
            elif char == 4:
                current_alphabet = A1
                temp_shift = 1
            elif char == 5:
                current_alphabet = A2
                temp_shift = 1
            else:
                text.append(current_alphabet[char - 6])

        if temp_shift == 2:
            current_alphabet = last_alphabet if zm.version < 3 else A0
            temp_shift = 0
        elif temp_shift > 0:
            temp_shift += 1

    return ''.join(text)



# def make_dict_string(zm, text):

#     if zm.header.version >= 5 and zm.header.alpha_tab_base:
#         base = zm.header.alpha_tab_base
#         A0 = ''.join(map(chr, list(zm.memory[base+0*26:base+1*26])))
#         A1 = ''.join(map(chr, list(zm.memory[base+1*26:base+2*26])))
#         A2 = ''.join(map(chr, list(zm.memory[base+2*26:base+3*26])))
#     else:
#         A0 = Default_A0
#         A1 = Default_A1
#         A2 = Default_A2

#     if zm.header.version == 1:
#         A2 = Default_A2_for_z1

#     # TODO: S 3.7.1, which expects 4,5 for len-2 shift
#     # seqs (not full lock) and works this way only for
#     # dict lookups? Still unclear to me, can find no
#     # examples of this.

#     if zm.header.version <= 3:
#         KEY_LEN = 6
#     else:
#         KEY_LEN = 9
#     text = text[:KEY_LEN] # will truncate again later, but shortens the loop

#     ztext = []
#     for char in text:
#         if char in A0:
#             ztext.append(A0.index(char)+6)
#         elif char in A1:
#             # only can be custom alphabets, no version 1/2 code needed
#             ztext.append(4)
#             ztext.append(A1.index(char)+6)
#         elif char in A2 and A2.index(char) != 0 and (zm.header.version == 1 or A2.index(char) != 1):
#             if zm.header.version <= 2:
#                 ztext.append(3)
#             else:
#                 ztext.append(5)
#             ztext.append(A2.index(char)+6)
#         else:
#             # 10-bit ZSCII (only 8 bits ever used)
#             ztext.append(ord(char) >> 5) # top 3 bits
#             ztext.append(ord(char) & 0x1f) # bottom 5 bits

#     ztext = ztext[:KEY_LEN] # truncating multi-byte chars here
#     while len(ztext) < KEY_LEN:
#         ztext.append(5)

#     packed_text = []
#     for i in range(0, len(ztext), 3):
#         c, c1, c2 = ztext[i:i+3]
#         packed_text.append((c << 10) | (c1 << 5) | c2)
#     packed_text[-1] |= 0x8000
#     return packed_text

# def unpack_string(chars):
#     pass