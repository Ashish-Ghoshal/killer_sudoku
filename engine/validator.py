"""Validation layer: structural checks, uniqueness (backtracking), and final-board verification.
Pure-Python on purpose so the MVP has no solver dependency; swap in PuLP/OR-Tools later if desired."""
from __future__ import annotations

from typing import List, Optional, Sequence

from engine.combos import max_sum, min_sum
from models.board import BOXES, COLS, ROWS, Cage, box_index, cell_name


def validate_cages(cages: Sequence[Cage]) -> List[str]:
    """Return a list of human-readable problems (empty list = structurally valid)."""
    errors: List[str] = []
    seen = {}
    for cg in cages:
        n = len(cg.cells)
        if n == 0 or n > 9:
            errors.append(f"Cage {cg.cage_id} has {n} cells.")
            continue
        if not min_sum(n) <= cg.target_sum <= max_sum(n):
            errors.append(f"Cage {cg.cage_id}: sum {cg.target_sum} is impossible for {n} cells "
                          f"(allowed {min_sum(n)}-{max_sum(n)}).")
        for cell in cg.cells:
            if cell in seen:
                errors.append(f"{cell_name(cell)} is in both cage {seen[cell]} and cage {cg.cage_id}.")
            seen[cell] = cg.cage_id
    missing = [(r, c) for r in range(9) for c in range(9) if (r, c) not in seen]
    if missing:
        errors.append(f"{len(missing)} cells are not in any cage (first: {cell_name(missing[0])}).")
    total = sum(cg.target_sum for cg in cages)
    if not missing and total != 405:
        errors.append(f"Cage sums total {total}, but a full grid must total 405.")
    return errors


def count_solutions(cages: Sequence[Cage], limit: int = 2) -> List[List[List[int]]]:
    """Backtracking search; returns up to `limit` distinct solutions (so len==1 means unique)."""
    cage_idx = {cell: i for i, cg in enumerate(cages) for cell in cg.cells}
    targets = [cg.target_sum for cg in cages]
    csum = [0] * len(cages)
    cused = [0] * len(cages)
    cleft = [len(cg.cells) for cg in cages]
    rows, cols, boxes = [0] * 9, [0] * 9, [0] * 9
    grid = [[0] * 9 for _ in range(9)]
    empties = {(r, c) for r in range(9) for c in range(9)}
    found: List[List[List[int]]] = []

    def options(r: int, c: int) -> List[int]:
        k = cage_idx[(r, c)]
        taken = rows[r] | cols[c] | boxes[box_index((r, c))] | cused[k]
        left = cleft[k] - 1
        res = []
        for d in range(1, 10):
            if taken >> d & 1:
                continue
            rem = targets[k] - csum[k] - d
            if (left == 0 and rem == 0) or (left > 0 and min_sum(left) <= rem <= max_sum(left)):
                res.append(d)
        return res

    def search() -> None:
        if len(found) >= limit:
            return
        if not empties:
            found.append([row[:] for row in grid])
            return
        best, best_opts = None, None
        for cell in empties:
            opts = options(*cell)
            if best_opts is None or len(opts) < len(best_opts):
                best, best_opts = cell, opts
                if len(opts) <= 1:
                    break
        if not best_opts:
            return
        r, c = best
        k, b = cage_idx[best], box_index(best)
        empties.discard(best)
        for d in best_opts:
            bit = 1 << d
            grid[r][c] = d
            rows[r] |= bit; cols[c] |= bit; boxes[b] |= bit; cused[k] |= bit
            csum[k] += d; cleft[k] -= 1
            search()
            rows[r] &= ~bit; cols[c] &= ~bit; boxes[b] &= ~bit; cused[k] &= ~bit
            csum[k] -= d; cleft[k] += 1
            grid[r][c] = 0
            if len(found) >= limit:
                break
        empties.add(best)

    search()
    return found


def verify_solution(grid: Sequence[Sequence[Optional[int]]], cages: Sequence[Cage]) -> List[str]:
    """Check a completed board against sudoku + cage rules."""
    errs: List[str] = []
    if any(v is None for row in grid for v in row):
        return ["Board is incomplete."]
    full = set(range(1, 10))
    for name, houses in (("Row", ROWS), ("Column", COLS), ("Box", BOXES)):
        for i, cells in enumerate(houses):
            if {grid[r][c] for r, c in cells} != full:
                errs.append(f"{name} {i + 1} does not contain 1-9 exactly once.")
    for cg in cages:
        vals = [grid[r][c] for r, c in cg.cells]
        if sum(vals) != cg.target_sum or len(set(vals)) != len(vals):
            errs.append(f"Cage {cg.cage_id} violates its sum or repeats a digit.")
    return errs
