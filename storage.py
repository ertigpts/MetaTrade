"""Small durable store for analysis history and the trading journal."""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parent
_ACTIVE_DATABASE_PATH = None


def _database_candidates():
    """Return stable database locations, ending with a writable runtime fallback."""
    configured = os.getenv("TAHLIL_DATABASE_PATH", "").strip()
    candidates = []
    if configured:
        configured_path = Path(configured).expanduser()
        if not configured_path.is_absolute():
            configured_path = _PROJECT_ROOT / configured_path
        candidates.append(configured_path)

    candidates.append(_PROJECT_ROOT / "data" / "tradeai.sqlite3")

    runtime_root = Path(
        os.getenv("TAHLIL_RUNTIME_DIR", "").strip() or tempfile.gettempdir()
    ).expanduser()
    candidates.append(runtime_root / "tradeai" / "tradeai.sqlite3")

    unique = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in unique:
            unique.append(resolved)
    return unique


def _open_database():
    """Open the first writable database path without making app startup brittle."""
    global _ACTIVE_DATABASE_PATH

    candidates = _database_candidates()
    if _ACTIVE_DATABASE_PATH is not None:
        candidates = [_ACTIVE_DATABASE_PATH] + [
            path for path in candidates if path != _ACTIVE_DATABASE_PATH
        ]

    last_error = None
    for path in candidates:
        db = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            db = sqlite3.connect(path, timeout=10)
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA foreign_keys=ON")
            _ACTIVE_DATABASE_PATH = path
            return db
        except (OSError, sqlite3.Error) as exc:
            last_error = exc
            if db is not None:
                db.close()

    raise sqlite3.OperationalError(
        "TradeAI could not open a writable database location."
    ) from last_error


@contextmanager
def connection():
    db = _open_database()
    try:
        yield db
        db.commit()
    finally:
        db.close()


def init_database():
    with connection() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                interval TEXT NOT NULL,
                action_bias TEXT NOT NULL,
                signal_strength INTEGER NOT NULL,
                latest_price REAL NOT NULL,
                summary_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_analyses_owner_created
                ON analyses(owner_id, created_at DESC);

            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL,
                exit_price REAL,
                stop_loss REAL,
                take_profit REAL,
                status TEXT NOT NULL DEFAULT 'open',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_journal_owner_created
                ON journal_entries(owner_id, created_at DESC);

            CREATE TABLE IF NOT EXISTS signal_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id TEXT NOT NULL,
                signal_key TEXT NOT NULL,
                symbol TEXT NOT NULL,
                interval TEXT NOT NULL,
                candle_time TEXT NOT NULL,
                signal TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(owner_id, signal_key)
            );
            CREATE INDEX IF NOT EXISTS idx_signal_events_owner_created
                ON signal_events(owner_id, created_at DESC);

            CREATE TABLE IF NOT EXISTS order_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id TEXT NOT NULL,
                signal_key TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'reserved',
                request_json TEXT NOT NULL,
                result_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(owner_id, signal_key),
                UNIQUE(owner_id, token_hash)
            );
            CREATE INDEX IF NOT EXISTS idx_order_executions_owner_created
                ON order_executions(owner_id, created_at DESC);
            """
        )


def save_analysis(owner_id, symbol, interval, summary):
    now = datetime.now(timezone.utc).isoformat()
    with connection() as db:
        cursor = db.execute(
            """
            INSERT INTO analyses
                (owner_id, symbol, interval, action_bias, signal_strength, latest_price, summary_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                owner_id,
                symbol,
                interval,
                str(summary.get("action_bias", "Wait"))[:50],
                int(summary.get("signal_strength", summary.get("confidence", 0)) or 0),
                float(summary.get("latest_price", 0) or 0),
                json.dumps(summary, ensure_ascii=False),
                now,
            ),
        )
        return cursor.lastrowid


def list_analyses(owner_id, limit=30):
    with connection() as db:
        rows = db.execute(
            """
            SELECT id, symbol, interval, action_bias, signal_strength, latest_price, summary_json, created_at
            FROM analyses WHERE owner_id = ? ORDER BY id DESC LIMIT ?
            """,
            (owner_id, limit),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["summary"] = json.loads(item.pop("summary_json"))
        result.append(item)
    return result


def add_journal_entry(owner_id, payload):
    now = datetime.now(timezone.utc).isoformat()
    with connection() as db:
        cursor = db.execute(
            """
            INSERT INTO journal_entries
                (owner_id, symbol, direction, entry_price, exit_price, stop_loss,
                 take_profit, status, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                owner_id,
                payload["symbol"],
                payload["direction"],
                payload.get("entry_price"),
                payload.get("exit_price"),
                payload.get("stop_loss"),
                payload.get("take_profit"),
                payload.get("status", "open"),
                payload.get("notes", ""),
                now,
                now,
            ),
        )
        return cursor.lastrowid


def list_journal(owner_id, limit=50):
    with connection() as db:
        rows = db.execute(
            "SELECT * FROM journal_entries WHERE owner_id = ? ORDER BY id DESC LIMIT ?",
            (owner_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def signal_exists(owner_id, signal_key):
    with connection() as db:
        row = db.execute(
            "SELECT 1 FROM signal_events WHERE owner_id = ? AND signal_key = ? LIMIT 1",
            (owner_id, signal_key),
        ).fetchone()
    return row is not None


def save_signal_event(owner_id, payload):
    now = datetime.now(timezone.utc).isoformat()
    with connection() as db:
        cursor = db.execute(
            """
            INSERT OR IGNORE INTO signal_events
                (owner_id, signal_key, symbol, interval, candle_time, signal, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                owner_id,
                str(payload["signal_key"]),
                str(payload["symbol"]),
                str(payload["interval"]),
                str(payload["candle_time"]),
                str(payload["signal"]),
                json.dumps(payload, ensure_ascii=False),
                now,
            ),
        )
        return bool(cursor.rowcount)


def reserve_order_execution(owner_id, signal_key, token_hash, request_payload):
    """Atomically reserve a signal before talking to the broker (fail-closed idempotency)."""
    now = datetime.now(timezone.utc).isoformat()
    with connection() as db:
        cursor = db.execute(
            """
            INSERT OR IGNORE INTO order_executions
                (owner_id, signal_key, token_hash, status, request_json, created_at, updated_at)
            VALUES (?, ?, ?, 'reserved', ?, ?, ?)
            """,
            (
                owner_id,
                str(signal_key),
                str(token_hash),
                json.dumps(request_payload, ensure_ascii=False),
                now,
                now,
            ),
        )
        return bool(cursor.rowcount)


def finalize_order_execution(owner_id, signal_key, status, result_payload):
    now = datetime.now(timezone.utc).isoformat()
    with connection() as db:
        cursor = db.execute(
            """
            UPDATE order_executions
               SET status = ?, result_json = ?, updated_at = ?
             WHERE owner_id = ? AND signal_key = ?
            """,
            (
                str(status)[:30],
                json.dumps(result_payload, ensure_ascii=False),
                now,
                owner_id,
                str(signal_key),
            ),
        )
        return bool(cursor.rowcount)


def list_order_executions(owner_id, limit=30):
    with connection() as db:
        rows = db.execute(
            """
            SELECT id, signal_key, status, request_json, result_json, created_at, updated_at
              FROM order_executions WHERE owner_id = ? ORDER BY id DESC LIMIT ?
            """,
            (owner_id, min(max(int(limit), 1), 100)),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["request"] = json.loads(item.pop("request_json") or "{}")
        item["result"] = json.loads(item.pop("result_json") or "{}")
        result.append(item)
    return result
