"""Puzzle input parsing — the only place that knows about text/JSON formats (UI-agnostic)."""
from __future__ import annotations

import json
import re
from typing import List

from models.board import Cage, Coord, cell_name


def parse_cell(token: str) -> Coord:
    """Parse 'A1'..'I9' (row letter, column digit) or 'r3c4' into a (row, col) tuple."""
    t = token.strip().upper()
    m = re.fullmatch(r"([A-I])([1-9])", t)
    if m:
        return ord(m.group(1)) - 65, int(m.group(2)) - 1
    m = re.fullmatch(r"R([1-9])C([1-9])", t)
    if m:
        return int(m.group(1)) - 1, int(m.group(2)) - 1
    raise ValueError(f"Bad cell reference: {token!r}")


def parse_cage_text(text: str) -> List[Cage]:
    """One cage per line, e.g. '17: A1 A2 B1'. Blank lines and '#' comments are ignored."""
    cages: List[Cage] = []
    for raw in text.splitlines():
        line = raw.split("#")[0].strip()
        if not line:
            continue
        m = re.fullmatch(r"(\d+)\s*[:;,]?\s*(.+)", line)
        if not m:
            raise ValueError(f"Cannot parse line: {raw!r}")
        cells = tuple(parse_cell(tok) for tok in re.split(r"[\s,]+", m.group(2).strip()) if tok)
        cages.append(Cage(len(cages) + 1, int(m.group(1)), cells))
    return cages


def cages_to_text(cages: List[Cage]) -> str:
    """Inverse of parse_cage_text."""
    return "\n".join(f"{cg.target_sum}: " + " ".join(cell_name(c) for c in cg.cells) for cg in cages)


def puzzle_from_json(raw: str) -> List[Cage]:
    """JSON: {"cages": [{"sum": 17, "cells": ["A1", "A2"]}, ...]}"""
    data = json.loads(raw)
    return [
        Cage(i + 1, int(item["sum"]), tuple(parse_cell(c) for c in item["cells"]))
        for i, item in enumerate(data["cages"])
    ]
