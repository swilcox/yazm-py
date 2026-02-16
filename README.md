# yazm-py

Yet Another Z-Machine in Python — an interpreter for Infocom interactive fiction games.

Currently targets **version 3** story files (`.z3`), such as the original Zork trilogy, Hitchhiker's Guide, and other classic Infocom titles.

## Features

- Fetch-decode-execute VM for Z-machine v3 bytecode
- Full object system with tree traversal (parent/child/sibling)
- ZSCII text decoding with alphabet tables, abbreviations, and Unicode extensions
- Dictionary tokenization and input parsing
- Terminal UI with ANSI status bar and optional object highlighting
- Plain output mode (`--plain`) for clean piped/diffable output
- Interactive debugger with commands like `$tree`, `$dict`, `$room`, `$find`
- Pure Python 3.12+ with no runtime dependencies

## Installation

Requires [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

## Usage

```bash
# Run a game
yazm minizork.z3

# Disable object name highlighting
yazm --no-highlight lurkinghorror.z3

# Plain mode (no ANSI codes, suitable for piping)
yazm --plain czech.z3

# Run directly without installing
python -m yazm.main minizork.z3
```

## Development

```bash
# Run all tests
pytest

# Run a single test file
pytest tests/test_zdata.py

# Lint and format
ruff check src/ tests/
ruff format src/ tests/

# Type check
uvx ty check
```

## Architecture

The interpreter follows a fetch-decode-execute VM pattern:

| File | Role |
|------|------|
| `zmachine.py` | Core `ZMachine` class: memory, object system, instruction loop, dictionary/tokenization |
| `zinstruction.py` | Decodes variable-length bytecode (LONG, SHORT, VAR, EXT forms) into `Instruction` dataclasses |
| `ops.py` | ~50 opcode handlers dispatched via `DISPATCH_TABLE` (control flow, arithmetic, objects, I/O, etc.) |
| `zdata.py` | `ZData(bytearray)` with big-endian u8/u16 reads/writes and sequential Reader/Writer helpers |
| `zheader.py` | Parses the 64-byte story file header (version, memory layout, flags) |
| `frame.py` | Call stack `Frame`: resume address, local variables, evaluation stack, argument count |
| `zscii.py` | ZSCII text encoding: 5-bit packed characters, 3 alphabet tables, abbreviation expansion |
| `zui_std.py` | Terminal UI: ANSI status bar, styled output, plain mode |
| `zdebug.py` | Interactive debugger (`$tree`, `$dict`, `$room`, `$find`, etc.) |
| `enums.py` | `Opcode` IntEnum (~100 opcodes), operand type enums, opcode name mappings |
| `options.py` | `Options` dataclass for runtime config (save dir, RNG seed, highlighting) |
