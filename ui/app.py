"""Streamlit front-end. Run:  streamlit run ui/app.py   (from the project root)"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st  # noqa: E402

from engine.hints import hint_text  # noqa: E402
from engine.solver import HumanSolver  # noqa: E402
from engine.validator import count_solutions, validate_cages  # noqa: E402
from models.board import BoardState, cell_name  # noqa: E402
from models.parsing import cages_to_text, parse_cage_text, puzzle_from_json  # noqa: E402
from telemetry.logger import TelemetryLogger  # noqa: E402
from ui.render import board_html  # noqa: E402

st.set_page_config(page_title="Killer Sudoku Tutor", layout="wide")
st.title("Killer Sudoku Tutor")
EX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")


@st.cache_resource
def get_logger():
    return TelemetryLogger("telemetry.db")


def load_example(name):
    with open(os.path.join(EX, name)) as f:
        return cages_to_text(puzzle_from_json(f.read()))


if "cage_text" not in st.session_state:
    st.session_state.cage_text = load_example("sample_tier2.json")

with st.sidebar:
    st.header("1. Enter puzzle")
    ex = st.selectbox("Load an example", ["(keep current)", "sample_tier2.json", "sample_needs_tier4.json"])
    if ex != "(keep current)" and st.button("Load example"):
        st.session_state.cage_text = load_example(ex)
        st.session_state.pop("state", None)
    st.text_area("Cages — one per line: `sum: A1 A2 B1` (rows A-I, columns 1-9)",
                 key="cage_text", height=320)
    check_unique = st.checkbox("Also check the puzzle has a unique solution", value=True)
    if st.button("Start puzzle", type="primary"):
        try:
            cages = parse_cage_text(st.session_state.cage_text)
            errors = validate_cages(cages)
            sols = []
            if not errors:
                sols = count_solutions(cages, 2)
                if not sols:
                    errors.append("This puzzle has no solution.")
                elif check_unique and len(sols) > 1:
                    errors.append("This puzzle has more than one solution (check your cage sums).")
            if errors:
                for e in errors:
                    st.error(e)
            else:
                st.session_state.state = BoardState.new(cages)
                st.session_state.history = []
                st.session_state.hint_level = 0
                st.session_state.solution = sols[0]
                st.session_state.finished = False
                st.session_state.msg = None
                lg = get_logger()
                lg.start_game("manual-entry")
                st.success("Puzzle loaded.")
        except ValueError as exc:
            st.error(str(exc))

state = st.session_state.get("state")
if state is None:
    st.info("Enter cages in the sidebar and press **Start puzzle**.")
    st.stop()

solver = HumanSolver()
col_board, col_info = st.columns([3, 2])
nxt = solver.next_step(state)
last = st.session_state.history[-1] if st.session_state.history else None

with col_board:
    show_c = st.toggle("Show candidates", value=True)
    hl = set(last.target_cells) if last else set()
    st.markdown(board_html(state, highlight=hl, show_candidates=show_c), unsafe_allow_html=True)

with col_info:
    st.subheader("Coach")
    filled = sum(v is not None for row in state.values for v in row)
    st.progress(filled / 81, text=f"{filled}/81 cells solved")
    b1, b2, b3 = st.columns(3)
    if b1.button("Hint") and nxt:
        st.session_state.hint_level = min(3, st.session_state.hint_level + 1)
        get_logger().log_event("REQUEST_HINT", filled, technique=nxt.technique,
                               available=[nxt.to_dict()])
    if b2.button("Take step") and nxt:
        state.apply(nxt)
        st.session_state.history.append(nxt)
        st.session_state.hint_level = 0
        get_logger().log_event("APPLY_DEDUCTION", filled, technique=nxt.technique, available=[nxt.to_dict()])
        st.rerun()
    if b3.button("Solve all"):
        res = solver.solve(state)
        st.session_state.state = res.final_state
        st.session_state.history += res.steps
        st.rerun()

    st.markdown("**Your move**")
    if st.session_state.get("msg"):
        kind, text = st.session_state.msg
        getattr(st, kind)(text)
        st.session_state.msg = None
    p1, p2, p3 = st.columns(3)
    row_l = p1.selectbox("Row", list("ABCDEFGHI"), key="mv_row")
    col_n = p2.selectbox("Column", list(range(1, 10)), key="mv_col")
    digit = p3.selectbox("Digit", list(range(1, 10)), key="mv_digit")
    if st.button("Place digit"):
        cell = (ord(row_l) - 65, col_n - 1)
        name = cell_name(cell)
        if state.is_placed(cell):
            st.session_state.msg = ("warning", f"{name} is already filled.")
        elif digit == st.session_state.solution[cell[0]][cell[1]]:
            avail = solver.available_deductions(state)
            used = next((e.technique for e in avail if e.placements.get(cell) == digit), "")
            state.place(cell, digit)
            get_logger().log_event("PLACE_DIGIT", filled, cell=name, value=digit,
                                   technique=used or "not-available-to-engine",
                                   available=[e.to_dict() for e in avail])
            how = f"the engine had this as a **{used}**" if used else "the engine could not see this deduction yet"
            st.session_state.msg = ("success", f"Correct: {digit} in {name} ({how}).")
        else:
            get_logger().log_event("BLUNDER", filled, cell=name, value=digit)
            st.session_state.msg = ("error", f"{digit} in {name} is not right. Try again or ask for a hint.")
        st.rerun()

    lvl = st.session_state.hint_level
    if nxt and lvl:
        st.info(hint_text(nxt, lvl))
    if state.is_solved():
        st.success("Solved!")
        if not st.session_state.get("finished"):
            get_logger().finish_game("completed")
            st.session_state.finished = True
    elif nxt is None:
        st.warning("The Tier 1–3 engine is stuck here — this puzzle needs more advanced techniques (Tier 4+).")

    if last:
        st.markdown(f"**Last step (Tier {last.tier} · {last.technique}):** {last.explanation}")
        with st.expander("Raw deduction payload (what the LLM coach will receive in Phase 3)"):
            st.code(json.dumps(last.to_dict(), indent=2), language="json")

with st.expander(f"Step log ({len(st.session_state.history)} steps)"):
    for i, ev in enumerate(st.session_state.history, 1):
        st.write(f"{i}. T{ev.tier} · {ev.technique} — {ev.explanation}")