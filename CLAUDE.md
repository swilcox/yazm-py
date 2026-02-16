# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

yazm-py (Yet Another Z-Machine) is a Z-machine interpreter in Python 3.12+ that runs Infocom interactive fiction games. Currently targets version 3 story files (.z3).

## Commands

```bash
# Install dependencies (uses uv)
uv sync

# Run a game
yazm minizork.z3
yazm --no-highlight lurkinghorror.z3

# Run directly without install
python -m yazm.main minizork.z3

# Run all tests
pytest

# Run a single test file
pytest tests/test_zdata.py

# Lint and format
ruff check src/ tests/
ruff format src/ tests/
```

## Architecture

The interpreter follows a fetch-decode-execute VM pattern:

- **`zmachine.py`** — Core `ZMachine` class: memory management, object system (tree with parent/child/sibling), instruction execution loop, dictionary/tokenization, string unpacking
- **`zinstruction.py`** — Decodes variable-length bytecode instructions (4 forms: LONG, SHORT, VAR, EXT) into `Instruction` dataclasses with opcode, operands, store target, branch info
- **`ops.py`** — All opcode handler functions (~50), dispatched via `DISPATCH_TABLE` dict mapping `Opcode` enum → handler. Categories: control flow, branches, memory, arithmetic, objects, properties, I/O
- **`zdata.py`** — `ZData(bytearray)` providing big-endian u8/u16 reads and writes, with Reader/Writer classes for sequential memory access
- **`zheader.py`** — Parses the 64-byte story file header (version, memory layout addresses, flags)
- **`frame.py`** — Call stack `Frame` dataclass: resume address, local variables, evaluation stack, argument count
- **`zscii.py`** — ZSCII text encoding: 5-bit packed characters, 3 alphabet tables, abbreviation expansion
- **`zui_std.py`** — Terminal UI with ANSI escape codes: status bar, text output, optional object/location highlighting
- **`zdebug.py`** — Interactive debugger (`$tree`, `$dict`, `$room`, `$find`, etc.) — many commands still stubbed
- **`enums.py`** — `Opcode` IntEnum with all ~100 opcodes, operand type enums, opcode name mappings
- **`options.py`** — `Options` dataclass for runtime config (save dir, logging, RNG seed, highlighting)

## Conventions

- One major class per file, pure Python with no runtime dependencies
- Dataclasses for data structures (`Frame`, `Options`, `Flag1`, `Flag2`, `Branch`, `ZObjectProperty`)
- Type annotations throughout with `from __future__ import annotations` for forward refs
- `TYPE_CHECKING` blocks to avoid circular imports
- Z-machine memory is big-endian; `ZData` handles byte order

## Incomplete Features

Save/restore, undo/redo, most debugger commands, and sound are stubbed out.
