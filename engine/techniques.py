"""Human-logic techniques. Each technique inspects a BoardState and returns ALL deductions currently
available (never mutating the state). Pluggable: add a class, add it to DEFAULT_TECHNIQUES."""
from __future__ import annotations

from typing import Dict, List

from engine.combos import analyze_cage
from models.board import (BOXES, COLS, HOUSES, ROWS, BoardState, Cage, Coord,
                          DeductionEvent, cell_name)


def _names(cells) -> str:
    return ", ".join(cell_name(c) for c in cells)


def _digits(ds) -> str:
    return "{" + ", ".join(str(d) for d in sorted(ds)) + "}"


class Technique:
    tier: int = 0
    name: str = ""
    category: str = "Spatial"

    def find(self, state: BoardState) -> List[DeductionEvent]:  # pragma: no cover
        raise NotImplementedError


# ---------------------------------------------------------------- Tier 1
class NakedSingle(Technique):
    tier, name, category = 1, "Naked Single", "Spatial"

    def find(self, state):
        out = []
        for r in range(9):
            for c in range(9):
                cell = (r, c)
                if not state.is_placed(cell) and len(state.cands(cell)) == 1:
                    v = next(iter(state.cands(cell)))
                    out.append(DeductionEvent(
                        self.tier, self.name, self.category, [cell], placements={cell: v},
                        explanation=f"{cell_name(cell)} has only one candidate left: {v}."))
        return out


class HiddenSingle(Technique):
    tier, name, category = 1, "Hidden Single", "Spatial"

    def find(self, state):
        out, seen = [], set()
        for house_name, cells in HOUSES:
            for d in range(1, 10):
                if any(state.values[r][c] == d for r, c in cells):
                    continue
                spots = [c for c in cells if not state.is_placed(c) and d in state.cands(c)]
                if len(spots) == 1 and (spots[0], d) not in seen:
                    seen.add((spots[0], d))
                    out.append(DeductionEvent(
                        self.tier, self.name, self.category, spots, placements={spots[0]: d},
                        explanation=f"In {house_name}, {d} can only go in {cell_name(spots[0])}."))
        return out


def _cage_prune_events(state: BoardState, single_combo: bool, tier: int, name: str) -> List[DeductionEvent]:
    out = []
    for cg in state.cages:
        res = analyze_cage([state.cands(c) for c in cg.cells], cg.target_sum)
        if res is None:
            continue
        combos, per_cell = res
        if not combos or (len(combos) == 1) != single_combo:
            continue
        elim: Dict[Coord, List[int]] = {}
        for cell, ok in zip(cg.cells, per_cell):
            if state.is_placed(cell):
                continue
            gone = sorted(state.cands(cell) - set(ok))
            if gone:
                elim[cell] = gone
        if not elim:
            continue
        if single_combo:
            why = (f"{cg.label()} can only be made with the digits {_digits(combos[0])}, "
                   f"so other digits are impossible there.")
        else:
            why = (f"{cg.label()} has {len(combos)} possible digit sets; some digits fit no valid "
                   f"arrangement in these cells and can be removed.")
        out.append(DeductionEvent(tier, name, "Arithmetic", list(cg.cells), eliminations=elim,
                                  explanation=why))
    return out


class UniquePartition(Technique):
    tier, name, category = 1, "Unique Sum Partition", "Arithmetic"

    def find(self, state):
        return _cage_prune_events(state, True, self.tier, self.name)


# ---------------------------------------------------------------- Tier 2
class CombinationPruning(Technique):
    """Min/max boundary pruning generalised: keep a digit only if some full valid assignment uses it."""
    tier, name, category = 2, "Cage Min/Max Pruning", "Arithmetic"

    def find(self, state):
        return _cage_prune_events(state, False, self.tier, self.name)


class InnieOutieSingle(Technique):
    """Rule of 45 for one house, leaving exactly one cell sticking in (innie) or out (outie)."""
    tier, name, category = 2, "Rule of 45 (Innie/Outie)", "Arithmetic"

    def find(self, state):
        out = []
        for house_name, cells in HOUSES:
            hs = set(cells)
            inside = [cg for cg in state.cages if set(cg.cells) <= hs]
            covered = {c for cg in inside for c in cg.cells}
            rest = [c for c in cells if c not in covered]
            if len(rest) == 1 and inside:
                v = 45 - sum(cg.target_sum for cg in inside)
                cell = rest[0]
                if not state.is_placed(cell) and v in state.cands(cell):
                    out.append(DeductionEvent(
                        self.tier, self.name, self.category, [cell], placements={cell: v},
                        explanation=(f"{house_name} sums to 45. The cages fully inside it add up to "
                                     f"{45 - v}, so the one leftover cell {cell_name(cell)} (an innie) is {v}.")))
            touching = [cg for cg in state.cages if set(cg.cells) & hs]
            outside = {c for cg in touching for c in cg.cells} - hs
            if len(outside) == 1 and len(touching) > 1:
                cell = next(iter(outside))
                v = sum(cg.target_sum for cg in touching) - 45
                if not state.is_placed(cell) and v in state.cands(cell):
                    out.append(DeductionEvent(
                        self.tier, self.name, self.category, [cell], placements={cell: v},
                        explanation=(f"The cages touching {house_name} total {v + 45}, but the house "
                                     f"only holds 45, so the one cell sticking out ({cell_name(cell)}, an outie) is {v}.")))
        return out


# ---------------------------------------------------------------- Tier 3
class CageLockedCandidates(Technique):
    """Killer pointing: a digit required by every valid combination, in a cage inside one house."""
    tier, name, category = 3, "Cage-Locked Candidate", "Arithmetic"

    def find(self, state):
        out = []
        for cg in state.cages:
            if len(cg.cells) < 2:
                continue
            res = analyze_cage([state.cands(c) for c in cg.cells], cg.target_sum)
            if res is None or not res[0]:
                continue
            required = set.intersection(*(set(s) for s in res[0]))
            if not required:
                continue
            cs = set(cg.cells)
            for house_name, cells in HOUSES:
                if not cs <= set(cells):
                    continue
                elim = {}
                for cell in cells:
                    if cell in cs or state.is_placed(cell):
                        continue
                    gone = sorted(required & state.cands(cell))
                    if gone:
                        elim[cell] = gone
                if elim:
                    out.append(DeductionEvent(
                        self.tier, self.name, self.category, list(cg.cells), eliminations=elim,
                        explanation=(f"Every valid combination for {cg.label()} contains {_digits(required)}, "
                                     f"and the cage sits inside {house_name}, so those digits can't appear "
                                     f"elsewhere in {house_name}.")))
        return out


class NakedPair(Technique):
    tier, name, category = 3, "Naked Pair", "Spatial"

    def find(self, state):
        out = []
        for house_name, cells in HOUSES:
            free = [c for c in cells if not state.is_placed(c)]
            pairs = [c for c in free if len(state.cands(c)) == 2]
            for i, a in enumerate(pairs):
                for b in pairs[i + 1:]:
                    if state.cands(a) == state.cands(b):
                        ds = state.cands(a)
                        elim = {c: sorted(ds & state.cands(c)) for c in free
                                if c not in (a, b) and ds & state.cands(c)}
                        if elim:
                            out.append(DeductionEvent(
                                self.tier, self.name, self.category, [a, b], eliminations=elim,
                                explanation=(f"{cell_name(a)} and {cell_name(b)} both hold only {_digits(ds)}, "
                                             f"so those digits can be removed from the rest of {house_name}.")))
        return out


class PointingPair(Technique):
    """Pointing pairs/triples and box-line reduction in one rule."""
    tier, name, category = 3, "Pointing Pair/Triple", "Spatial"

    def find(self, state):
        out = []
        lines = [(n, cl) for n, cl in HOUSES]
        for h_name, h_cells in HOUSES:
            for d in range(1, 10):
                if any(state.values[r][c] == d for r, c in h_cells):
                    continue
                spots = [c for c in h_cells if not state.is_placed(c) and d in state.cands(c)]
                if len(spots) < 2:
                    continue
                for g_name, g_cells in lines:
                    if g_name == h_name or not set(spots) <= set(g_cells):
                        continue
                    if h_name.startswith("Box") == g_name.startswith("Box"):
                        continue  # must be box <-> line
                    elim = {c: [d] for c in g_cells
                            if c not in h_cells and not state.is_placed(c) and d in state.cands(c)}
                    if elim:
                        out.append(DeductionEvent(
                            self.tier, self.name, self.category, spots, eliminations=elim,
                            explanation=(f"In {h_name}, {d} must lie in {_names(spots)}, all in {g_name}; "
                                         f"so {d} is removed from the rest of {g_name}.")))
        return out


DEFAULT_TECHNIQUES: List[Technique] = [
    UniquePartition(), NakedSingle(), HiddenSingle(),
    InnieOutieSingle(), CombinationPruning(),
    CageLockedCandidates(), NakedPair(), PointingPair(),
]
