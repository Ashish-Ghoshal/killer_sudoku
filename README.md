# Killer Sudoku Tutor (Phase 1 MVP)

Deterministic human-logic Killer Sudoku solver with step-by-step explanations and a Streamlit UI.

    pip install -r requirements.txt
    streamlit run ui/app.py
    python -m unittest discover -s tests -v

## Layout
- `models/` dataclasses (Cage, BoardState, DeductionEvent) and puzzle parsing
- `engine/` combos table, techniques (Tier 1-3), solver, validator (uniqueness by backtracking), hints
- `telemetry/` SQLite logger (games, game_events)
- `ui/` Streamlit app + HTML board renderer
- `tools/generate_puzzle.py` makes unique sample puzzles: `python -m tools.generate_puzzle SEED`

## Techniques implemented
T1 Unique Sum Partition, Naked Single, Hidden Single
T2 Cage Min/Max Pruning, Rule of 45 single innie/outie
T3 Cage-Locked Candidates, Naked Pair, Pointing Pair/Triple + box-line reduction

Puzzles needing Tier 4+ (multi-house 45, virtual cages, parity) report "stuck" instead of guessing.
Input format: one cage per line, `17: A1 A2 B1` (rows A-I, columns 1-9).
