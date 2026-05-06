from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path


class HistoryStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total INTEGER NOT NULL,
                    passed INTEGER NOT NULL,
                    failed INTEGER NOT NULL,
                    result TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    trigger_source TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def insert(
        self,
        *,
        total: int,
        passed: int,
        failed: int,
        result: str,
        mode: str,
        trigger_source: str,
    ) -> int:
        timestamp = datetime.now().isoformat(timespec="seconds")
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO history (timestamp, total, passed, failed, result, mode, trigger_source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (timestamp, total, passed, failed, result, mode, trigger_source),
            )
            conn.commit()
            return int(cur.lastrowid)

    def list(self, date_filter: str | None = None) -> list[dict]:
        sql = """
            SELECT id, timestamp, total, passed, failed, result, mode, trigger_source
            FROM history
        """
        params: tuple = ()
        if date_filter:
            sql += " WHERE date(timestamp) = ?"
            params = (date_filter,)
        sql += " ORDER BY id DESC LIMIT 1000"

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    def clear(self) -> int:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM history")
            conn.commit()
            return int(cur.rowcount or 0)

    def count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM history").fetchone()
            return int(row["c"]) if row else 0
