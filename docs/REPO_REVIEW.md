# Existing GitHub projects reviewed (Nov 2026)

Reviewed from their public READMEs only (I could not clone them from my sandbox, so I did not read their source).
Check each licence before copying any code.

| Repo | What it is | What to learn from it |
|---|---|---|
| Barium/killer-sudoku-solver (MIT) | Python backtracking solver with cage-sum pruning, JSON puzzles, `solve(board, cages)` API | Good *baseline to fork*: small, MIT-licensed. Use it to cross-check our uniqueness validator. It guesses; it does not explain. |
| 2pa4ul2/Killer-Sudoku | Backtracking, backjumping and simulated annealing, compact `sum,cells;` input | Useful for comparing search strategies. Not human-style. |
| NumMy0/Sudoku-killer-python | Domain-reduction solver, `input.txt` boards from sudokumania | Closest in spirit to candidate pruning. Documentation is in Spanish. |
| HappyCerberus/sudoku (C++) | "Human-like" solver, no guessing, killer support added later, benchmarked | Shows how to structure a no-guess technique pipeline and benchmark it. |
| n36l3c7/Dedoku (Python) | Pure human-technique solver (classic sudoku), pluggable technique pipeline, `--explain`, 100 tests, mypy/ruff | Best architectural model: ordered `techniques=[...]`, each step reports technique + placements + eliminations. We copied the *pattern*, not the code. |
| GillesArcas/sudosol, bcorso/sudoku-solver | Human-technique solvers for classic sudoku | Reference for naming and ordering of standard techniques. |
| sudokuwiki.org Killer solver (not open source) | Strategy list: Innies/Outies, Killer Combinations, Cage/Unit Overlap, Cage Splitting, Law of Leftovers, Cage Compare, Rule of Parity... | Reference for the Tier 4-5 roadmap. Its code is "personal use only", so reimplement from the maths, never copy. |

Finding: none of the Python killer repos explains its moves in human terms. That gap is what this project fills.
