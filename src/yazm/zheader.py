from dataclasses import dataclass
from .enums import StatusLineType
from .zdata import ZData


@dataclass
class Flag1:
    # v1-3 flags
    status_line_type: StatusLineType = StatusLineType.score
    status_line: bool = False
    tandy_bit: bool = False
    screen_splitting: bool = False
    variable_pitch_default: bool = False
    # v4+ flags
    colors_available: bool = False
    multi_discs: bool = False
    picture_displaying: bool = False
    bold: bool = False
    sound: bool = False
    italic: bool = False
    fixed_pitch: bool = False
    timed_keyboard_input: bool = False


@dataclass
class Flag2:
    transcripting_on: bool = False
    force_fixed_pitch: bool = False
    request_redraw: bool = False
    use_pictures: bool = False
    use_undo: bool = False
    use_mouse: bool = False
    use_colors: bool = False
    use_sound_effects: bool = False
    use_menus: bool = False


class Header(object):
    """Z Header Class. Stores information about the current Z Story file and status."""
    def __init__(self, zdata: ZData):
        self.version = zdata[0x0]
        self.release = zdata.u16(0x2)
        self.high_memory_addr = zdata.u16(0x4)
        self.pc = zdata.u16(0x6)
        self.dict_addr = zdata.u16(0x8)
        self.obj_table_addr = zdata.u16(0xA) + (31 if self.version <= 3 else 63) * 2  # CHANGE!
        self.global_variable_addr = zdata.u16(0xC)
        self.static_memory_addr = zdata.u16(0xE)
        self.serial_number = zdata[0x12:0x18]
        self.abbrev_addr = zdata.u16(0x18)
        self.file_length = zdata.u16(0x1A)
        self.checksum = zdata.u16(0x1C)
        # begin version > 3 header portion
        self.routine_offset = zdata.u16(0x28) 
        self.string_offset = zdata.u16(0x2A)

        self.term_chars_addr = zdata.u16(0x2E)
        self.alpha_tab_addr = zdata.u16(0x34)
        self.hdr_ext_tab_addr = zdata.u16(0x36)

        self.unicode_tab_addr = 0
        self.hdr_ext_tab_length = 0
        if self.hdr_ext_tab_addr:
            self.hdr_ext_tab_length = zdata.u16(self.hdr_ext_tab_addr)
            if self.hdr_ext_tab_length >= 3:
                self.unicode_tab_addr = zdata.u16(self.hdr_ext_tab_addr + 3)
        self._flag1 = zdata[0x1]
        self._flag2 = zdata.u16(0x10)

    @property
    def flag1(self):
        if self.version <= 3:
            return Flag1(
                status_line_type=self._flag1 &       0b00000010,
                multi_discs=self._flag1 &            0b00000100,
                tandy_bit=self._flag1 &              0b00001000,
                status_line=self._flag1 &            0b00010000,
                screen_splitting=self._flag1 &       0b00100000,
                variable_pitch_default=self._flag1 & 0b01000000,
            )
        else:
            return Flag1(
                colors_available=self._flag1 &       0b00000001,
                picture_displaying=self._flag1 &     0b00000010,
                bold=self._flag1 &                   0b00000100,
                italic=self._flag1 &                 0b00001000,
                fixed_pitch=self._flag1 &            0b00010000,
                sound=self._flag1 &                  0b00100000,
                variable_pitch_default=self._flag1 & 0b01000000,
                timed_keyboard_input=self._flag1 &   0b10000000,
            )

    @property
    def flag2(self):
        return Flag2(
            transcripting_on=self._flag2 &  0b000000001,
            force_fixed_pitch=self._flag2 & 0b000000010,
            request_redraw=self._flag2 &    0b000000100,
            use_pictures=self._flag2 &      0b000001000,
            use_undo=self._flag2 &          0b000010000,
            use_mouse=self._flag2 &         0b000100000,
            use_colors=self._flag2 &        0b001000000,
            use_sound=self._flag2 &         0b010000000,
            use_menus=self._flag2 &         0b100000000,
        )
