import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).parent.parent / "aethermesh.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize SQLite tables for workflows, execution states, and events."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                task TEXT NOT NULL,
                status TEXT NOT NULL,
                confidence REAL NOT NULL,
                mutations INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                state_json TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                reason TEXT NOT NULL,
                details_json TEXT NOT NULL
            )
        """)
        conn.commit()


def save_run(run_id: str, state_dict: Dict[str, Any]) -> None:
    """Save or update an execution state and its events in the SQLite database."""
    init_db()
    task = state_dict.get("task", "")
    status = state_dict.get("status", "completed")
    confidence = state_dict.get("confidence", 0.0)
    metrics = state_dict.get("metrics", {})
    mutations = metrics.get("mutations", 0) if isinstance(metrics, dict) else 0
    events = state_dict.get("events", [])

    started_at = events[0]["timestamp"] if events and "timestamp" in events[0] else ""

    state_json = json.dumps(state_dict)

    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO runs (id, task, status, confidence, mutations, started_at, state_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, task, status, confidence, mutations, started_at, state_json),
        )

        for evt in events:
            evt_id = evt.get("id", "")
            evt_timestamp = evt.get("timestamp", "")
            evt_type = evt.get("event_type", "")
            evt_reason = evt.get("reason", "")
            evt_details = json.dumps(evt.get("details", {}))

            conn.execute(
                """
                INSERT OR REPLACE INTO events (id, workflow_id, timestamp, event_type, reason, details_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (evt_id, run_id, evt_timestamp, evt_type, evt_reason, evt_details),
            )

        conn.commit()


def get_all_runs() -> List[Dict[str, Any]]:
    """Fetch all saved past runs for the /history endpoint."""
    init_db()
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM runs ORDER BY rowid DESC").fetchall()
        runs = []
        for r in rows:
            runs.append({
                "summary": {
                    "id": r["id"],
                    "task": r["task"],
                    "status": r["status"],
                    "confidence": r["confidence"],
                    "mutations": r["mutations"],
                    "startedAt": r["started_at"],
                },
                "state": json.loads(r["state_json"]),
            })
        return runs


def get_run_by_id(run_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a specific execution state by workflow_id."""
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT state_json FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row:
            return json.loads(row["state_json"])
        return None
