"""Phase-1 telemetry: SQLite event log using the plan's games / game_events schema."""
from __future__ import annotations

import json
import sqlite3
import time
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS games (
    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
    puzzle_name TEXT, difficulty_tier INTEGER, status TEXT DEFAULT 'in_progress',
    started_ms INTEGER, total_time_ms INTEGER, report_json TEXT
);
CREATE TABLE IF NOT EXISTS game_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER REFERENCES games(game_id),
    move_number INTEGER, timestamp_ms INTEGER, game_phase TEXT,
    action_type TEXT, cell TEXT, value INTEGER,
    available_deductions_json TEXT, inferred_technique_used TEXT
);
"""


def game_phase(filled: int) -> str:
    """Opening (0-20 cells), Mid-Game (21-55), Endgame (56-81)."""
    return "opening" if filled <= 20 else "mid" if filled <= 55 else "endgame"


class TelemetryLogger:
    def __init__(self, path: str = "telemetry.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.executescript(SCHEMA)
        self.game_id: Optional[int] = None
        self.move = 0
        self._t0 = 0

    def start_game(self, puzzle_name: str, difficulty_tier: Optional[int] = None) -> int:
        self._t0 = int(time.time() * 1000)
        cur = self.conn.execute(
            "INSERT INTO games (puzzle_name, difficulty_tier, started_ms) VALUES (?,?,?)",
            (puzzle_name, difficulty_tier, self._t0))
        self.conn.commit()
        self.game_id, self.move = cur.lastrowid, 0
        return self.game_id

    def log_event(self, action_type: str, filled: int, cell: str = "", value: Optional[int] = None,
                  available: Optional[list] = None, technique: str = "") -> None:
        assert self.game_id is not None, "start_game() first"
        self.move += 1
        self.conn.execute(
            "INSERT INTO game_events (game_id, move_number, timestamp_ms, game_phase, action_type, cell, value,"
            " available_deductions_json, inferred_technique_used) VALUES (?,?,?,?,?,?,?,?,?)",
            (self.game_id, self.move, int(time.time() * 1000) - self._t0, game_phase(filled), action_type,
             cell, value, json.dumps(available or []), technique))
        self.conn.commit()

    def finish_game(self, status: str, report: Optional[dict] = None) -> None:
        self.conn.execute(
            "UPDATE games SET status=?, total_time_ms=?, report_json=? WHERE game_id=?",
            (status, int(time.time() * 1000) - self._t0, json.dumps(report or {}), self.game_id))
        self.conn.commit()
