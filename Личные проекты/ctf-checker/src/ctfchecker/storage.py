import sqlite3
from typing import Optional, Dict, Any, List, Tuple
from .utils import mask_flag, now_ts

SCHEMA = """
CREATE TABLE IF NOT EXISTS checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL,
    challenge_id TEXT NOT NULL,
    status TEXT NOT NULL,         -- OK / FAIL / ERROR
    duration_ms INTEGER NOT NULL,
    details TEXT
);
"""

class Storage:
    def __init__(self, db_path: str = "checks.sqlite3"):
        self.db_path = db_path
        self._init()

    def _init(self):
        con = sqlite3.connect(self.db_path)
        try:
            con.execute(SCHEMA)
            con.commit()
        finally:
            con.close()

    def add(self, challenge_id: str, status: str, duration_ms: int, details: str = ""):
        con = sqlite3.connect(self.db_path)
        try:
            con.execute(
                "INSERT INTO checks (ts, challenge_id, status, duration_ms, details) VALUES (?, ?, ?, ?, ?)",
                (now_ts(), challenge_id, status, duration_ms, details)
            )
            con.commit()
        finally:
            con.close()

    def history(self, limit: int = 50) -> List[Tuple]:
        con = sqlite3.connect(self.db_path)
        try:
            cur = con.execute(
                "SELECT id, ts, challenge_id, status, duration_ms, details FROM checks ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return cur.fetchall()
        finally:
            con.close()
