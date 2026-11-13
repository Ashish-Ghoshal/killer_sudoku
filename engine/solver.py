"""Deterministic human-logic solver: applies the simplest available deduction, one step at a time."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from engine.techniques import DEFAULT_TECHNIQUES, Technique
from models.board import BoardState, ContradictionError, DeductionEvent


@dataclass
class SolveResult:
    steps: List[DeductionEvent] = field(default_factory=list)
    solved: bool = False
    stuck: bool = False
    max_tier: int = 0
    final_state: Optional[BoardState] = None


class HumanSolver:
    def __init__(self, techniques: Optional[Sequence[Technique]] = None):
        # stable sort: lowest tier first, list order breaks ties
        self.techniques = sorted(techniques or DEFAULT_TECHNIQUES, key=lambda t: t.tier)

    def next_step(self, state: BoardState) -> Optional[DeductionEvent]:
        """Simplest deduction available right now, or None."""
        for tech in self.techniques:
            events = tech.find(state)
            if events:
                return events[0]
        return None

    def available_deductions(self, state: BoardState) -> List[DeductionEvent]:
        """Every deduction currently available (feeds telemetry blind-spot analysis)."""
        return [e for t in self.techniques for e in t.find(state)]

    def solve(self, state: BoardState, max_steps: int = 5000) -> SolveResult:
        s = state.copy()
        res = SolveResult(final_state=s)
        while not s.is_solved() and len(res.steps) < max_steps:
            ev = self.next_step(s)
            if ev is None:
                res.stuck = True
                break
            s.apply(ev)
            res.steps.append(ev)
            res.max_tier = max(res.max_tier, ev.tier)
        res.solved = s.is_solved()
        return res
