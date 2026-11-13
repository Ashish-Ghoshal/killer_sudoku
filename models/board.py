"""Core data contracts: Cage, DeductionEvent, BoardState. No UI imports allowed here."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

Coord = Tuple[int, int]

ROWS: List[List[Coord]] = [[(r, c) for c in range(9)] for r in range(9)]
COLS: List[List[Coord]] = [[(r, c) for r in range(9)] for c in range(9)]
BOXES: List[List[Coord]] = [
    [(br * 3 + i, bc * 3 + j) for i in range(3) for j in range(3)]
    for br in range(3) for bc in range(3)
]
HOUSES: List[Tuple[str, List[Coord]]] = (
    [(f"Row {chr(65 + i)}", ROWS[i]) for i in range(9)]
    + [(f"Column {i + 1}", COLS[i]) for i in range(9)]
    + [(f"Box {i + 1}", BOXES[i]) for i in range(9)]
)


def cell_name(cell: Coord) -> str:
    """Human-friendly cell label: row letter A-I + column number 1-9 (e.g. (0,0) -> 'A1')."""
    return f"{chr(65 + cell[0])}{cell[1] + 1}"


def box_index(cell: Coord) -> int:
    """Index 0-8 of the 3x3 box containing the cell."""
    return (cell[0] // 3) * 3 + cell[1] // 3


class ContradictionError(ValueError):
    """Raised when a board state becomes impossible (empty candidate set)."""


@dataclass(frozen=True)
class Cage:
    """A killer cage: distinct digits in `cells` must sum to `target_sum`."""
    cage_id: int
    target_sum: int
    cells: Tuple[Coord, ...]

    def label(self) -> str:
        return f"cage {self.cage_id} (sum {self.target_sum}: {', '.join(cell_name(c) for c in self.cells)})"


@dataclass
class DeductionEvent:
    """One explainable logical step. Serialisable for telemetry and the LLM coach."""
    tier: int
    technique: str
    category: str  # "Arithmetic" or "Spatial"
    target_cells: List[Coord]
    eliminations: Dict[Coord, List[int]] = field(default_factory=dict)
    placements: Dict[Coord, int] = field(default_factory=dict)
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "tier": self.tier,
            "technique": self.technique,
            "category": self.category,
            "target_cells": [list(c) for c in self.target_cells],
            "deduced_eliminations": {str(list(k)): v for k, v in self.eliminations.items()},
            "placements": {str(list(k)): v for k, v in self.placements.items()},
            "explanation": self.explanation,
        }


@dataclass
class BoardState:
    """Grid values + per-cell candidate sets + cage structure."""
    cages: List[Cage]
    values: List[List[Optional[int]]]
    candidates: List[List[Set[int]]]
    cage_of: Dict[Coord, int]

    @classmethod
    def new(cls, cages: List[Cage]) -> "BoardState":
        cage_of = {cell: cg.cage_id for cg in cages for cell in cg.cells}
        return cls(
            cages=list(cages),
            values=[[None] * 9 for _ in range(9)],
            candidates=[[set(range(1, 10)) for _ in range(9)] for _ in range(9)],
            cage_of=cage_of,
        )

    def copy(self) -> "BoardState":
        return BoardState(
            cages=self.cages,
            values=[row[:] for row in self.values],
            candidates=[[set(s) for s in row] for row in self.candidates],
            cage_of=self.cage_of,
        )

    def cage(self, cage_id: int) -> Cage:
        return next(cg for cg in self.cages if cg.cage_id == cage_id)

    def is_placed(self, cell: Coord) -> bool:
        return self.values[cell[0]][cell[1]] is not None

    def cands(self, cell: Coord) -> Set[int]:
        return self.candidates[cell[0]][cell[1]]

    def is_solved(self) -> bool:
        return all(v is not None for row in self.values for v in row)

    def peers(self, cell: Coord) -> Set[Coord]:
        r, c = cell
        out = set(ROWS[r]) | set(COLS[c]) | set(BOXES[box_index(cell)])
        out |= set(self.cage(self.cage_of[cell]).cells)
        out.discard(cell)
        return out

    def eliminate(self, cell: Coord, digits) -> None:
        cs = self.cands(cell)
        cs.difference_update(digits)
        if not cs:
            raise ContradictionError(f"{cell_name(cell)} has no candidates left")

    def place(self, cell: Coord, value: int) -> None:
        if value not in self.cands(cell):
            raise ContradictionError(f"{value} is not a candidate for {cell_name(cell)}")
        self.values[cell[0]][cell[1]] = value
        self.candidates[cell[0]][cell[1]] = {value}
        for p in self.peers(cell):
            if value in self.cands(p):
                self.eliminate(p, {value})

    def apply(self, event: DeductionEvent) -> None:
        """Apply a DeductionEvent (eliminations first, then placements)."""
        for cell, digits in event.eliminations.items():
            if not self.is_placed(cell):
                self.eliminate(cell, set(digits))
        for cell, value in event.placements.items():
            if not self.is_placed(cell):
                self.place(cell, value)
