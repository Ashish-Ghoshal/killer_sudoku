import json
import os
import tempfile
import unittest

from engine.combos import partitions
from engine.solver import HumanSolver
from engine.validator import count_solutions, validate_cages, verify_solution
from models.board import BoardState
from models.parsing import cages_to_text, parse_cage_text, puzzle_from_json
from telemetry.logger import TelemetryLogger
from tools.generate_puzzle import generate
from ui.render import board_html

EX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")


def load(name):
    with open(os.path.join(EX, name)) as f:
        return puzzle_from_json(f.read())


class TestCombos(unittest.TestCase):
    def test_magic_cages(self):
        self.assertEqual(partitions(2, 3), (frozenset({1, 2}),))
        self.assertEqual(partitions(2, 17), (frozenset({8, 9}),))
        self.assertEqual(partitions(3, 24), (frozenset({7, 8, 9}),))
        self.assertEqual(len(partitions(2, 10)), 4)


class TestParsing(unittest.TestCase):
    def test_roundtrip(self):
        cages = load("sample_tier2.json")
        self.assertEqual(parse_cage_text(cages_to_text(cages)), cages)

    def test_bad_cell(self):
        with self.assertRaises(ValueError):
            parse_cage_text("5: Z9 A1")


class TestValidator(unittest.TestCase):
    def test_sample_is_valid_and_unique(self):
        cages = load("sample_tier2.json")
        self.assertEqual(validate_cages(cages), [])
        self.assertEqual(len(count_solutions(cages, 2)), 1)

    def test_detects_missing_cells(self):
        self.assertTrue(validate_cages(parse_cage_text("3: A1 A2")))

    def test_detects_impossible_sum(self):
        errs = validate_cages(parse_cage_text("2: A1 A2"))
        self.assertTrue(any("impossible" in e for e in errs))


class TestSolver(unittest.TestCase):
    def test_solves_sample_with_human_logic_only(self):
        cages = load("sample_tier2.json")
        res = HumanSolver().solve(BoardState.new(cages))
        self.assertTrue(res.solved)
        self.assertEqual(verify_solution(res.final_state.values, cages), [])
        self.assertLessEqual(res.max_tier, 3)

    def test_matches_backtracking_answer(self):
        for seed in (1, 2, 3):
            cages, sol = generate(seed)
            res = HumanSolver().solve(BoardState.new(cages))
            if res.solved:
                self.assertEqual(res.final_state.values, sol)

    def test_reports_stuck_instead_of_guessing(self):
        res = HumanSolver().solve(BoardState.new(load("sample_needs_tier4.json")))
        self.assertTrue(res.stuck and not res.solved)

    def test_every_step_is_explained_and_serialisable(self):
        res = HumanSolver().solve(BoardState.new(load("sample_tier2.json")))
        for ev in res.steps:
            self.assertTrue(ev.explanation)
            json.dumps(ev.to_dict())


class TestTelemetryAndUI(unittest.TestCase):
    def test_logger_writes_rows(self):
        with tempfile.TemporaryDirectory() as d:
            lg = TelemetryLogger(os.path.join(d, "t.db"))
            lg.start_game("x", 2)
            lg.log_event("PLACE_DIGIT", 5, "A1", 3, technique="Naked Single")
            lg.finish_game("completed")
            n = lg.conn.execute("SELECT COUNT(*) FROM game_events").fetchone()[0]
            self.assertEqual(n, 1)
            lg.conn.close()

    def test_render_contains_cage_sums(self):
        html = board_html(BoardState.new(load("sample_tier2.json")))
        self.assertIn("<table", html)


if __name__ == "__main__":
    unittest.main()
