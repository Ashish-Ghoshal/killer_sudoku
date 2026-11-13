"""Board -> HTML. Pure string building (no Streamlit import) so it is unit-testable."""
from __future__ import annotations

from typing import Optional, Set

from models.board import BoardState, box_index

PALETTE = ["#fde2e4", "#e2ece9", "#dfe7fd", "#fff1e6", "#e8e0f5", "#f0efeb", "#d6f0f7", "#f6f2c8"]


def _cage_colors(state: BoardState) -> dict:
    """Greedy colouring so neighbouring cages get different colours."""
    color, adj = {}, {cg.cage_id: set() for cg in state.cages}
    for (r, c), cid in state.cage_of.items():
        for n in ((r + 1, c), (r, c + 1)):
            other = state.cage_of.get(n)
            if other is not None and other != cid:
                adj[cid].add(other); adj[other].add(cid)
    for cg in state.cages:
        used = {color[n] for n in adj[cg.cage_id] if n in color}
        color[cg.cage_id] = next(i for i in range(len(PALETTE) + 9) if i not in used) % len(PALETTE)
    return color


def board_html(state: BoardState, highlight: Optional[Set[tuple]] = None, show_candidates: bool = True) -> str:
    """Render the 9x9 board: cage sums in corners, dashed cage borders, thick box borders."""
    highlight = highlight or set()
    colors = _cage_colors(state)
    first_cell = {cg.cage_id: min(cg.cells) for cg in state.cages}
    sums = {cg.cage_id: cg.target_sum for cg in state.cages}
    rows = ['<table style="border-collapse:collapse;table-layout:fixed;width:522px;'
            'font-family:sans-serif;margin:auto">']
    for r in range(9):
        rows.append("<tr>")
        for c in range(9):
            cell, cid = (r, c), state.cage_of[(r, c)]

            def side(nr, nc):
                if not (0 <= nr < 9 and 0 <= nc < 9):
                    return "3px solid #111"
                if box_index((nr, nc)) != box_index(cell):
                    return "3px solid #111"
                if state.cage_of[(nr, nc)] != cid:
                    return "2px dashed #c0392b"
                return "1px solid #d0d0d0"

            bg = "#ffe066" if cell in highlight else PALETTE[colors[cid]]
            style = (f"width:58px;height:58px;padding:0;box-sizing:border-box;position:relative;"
                     f"text-align:center;vertical-align:middle;background:{bg};color:#111;"
                     f"border-top:{side(r - 1, c)};border-bottom:{side(r + 1, c)};"
                     f"border-left:{side(r, c - 1)};border-right:{side(r, c + 1)};")
            label = f'<span style="position:absolute;top:1px;left:3px;font-size:10px;color:#c0392b">{sums[cid]}</span>' \
                if first_cell[cid] == cell else ""
            v = state.values[r][c]
            if v is not None:
                body = f'<span style="font-size:26px;font-weight:600">{v}</span>'
            elif show_candidates:
                body = _cand_grid(state.cands(cell))
            else:
                body = ""
            rows.append(f'<td style="{style}">{label}{body}</td>')
        rows.append("</tr>")
    rows.append("</table>")
    return "".join(rows)


def _cand_grid(cands: Set[int]) -> str:
    """Pencil marks in a fixed 3x3 layout (1 top-left ... 9 bottom-right), pinned inside the cell."""
    rows = ""
    for r in range(3):
        cells = "".join(
            f'<span style="display:inline-block;width:33%;text-align:center">{d if d in cands else "&nbsp;"}</span>'
            for d in range(r * 3 + 1, r * 3 + 4))
        rows += f'<div style="height:15px;white-space:nowrap">{cells}</div>'
    return ('<div style="position:absolute;top:11px;left:4px;right:4px;bottom:2px;'
            'font-size:10px;line-height:15px;color:#444">' + rows + "</div>")