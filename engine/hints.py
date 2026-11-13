"""Progressive hint text from a DeductionEvent (deterministic; the Phase-3 LLM coach will rephrase this)."""
from __future__ import annotations

from models.board import DeductionEvent, cell_name


def hint_text(ev: DeductionEvent, level: int) -> str:
    """Level 1: where to look. Level 2: which technique. Level 3: full explanation."""
    if level <= 1:
        region = ", ".join(cell_name(c) for c in ev.target_cells)
        return f"Look closely at: {region}."
    if level == 2:
        return f"Try a **{ev.technique}** (Tier {ev.tier}, {ev.category.lower()} reasoning)."
    return ev.explanation
