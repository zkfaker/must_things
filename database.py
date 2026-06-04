"""Data layer: SQLite database for task management."""

import sqlite3
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables and seed default fixed tasks if first run."""
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS fixed_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS daily_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            is_completed INTEGER DEFAULT 0,
            is_fixed INTEGER DEFAULT 0,
            task_date TEXT NOT NULL,
            fixed_task_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    count = conn.execute("SELECT COUNT(*) FROM fixed_tasks").fetchone()[0]
    if count == 0:
        defaults = [
            "早起喝一杯水",
            "运动30分钟",
            "读书20分钟",
            "吃水果",
        ]
        for title in defaults:
            conn.execute("INSERT INTO fixed_tasks (title) VALUES (?)", (title,))

    conn.commit()
    conn.close()


# ── Fixed tasks ──────────────────────────────────────────────

def get_fixed_tasks():
    conn = _connect()
    rows = conn.execute("SELECT * FROM fixed_tasks ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_fixed_task(title):
    conn = _connect()
    cur = conn.execute("INSERT INTO fixed_tasks (title) VALUES (?)", (title,))
    conn.commit()
    pk = cur.lastrowid
    conn.close()
    return pk


def delete_fixed_task(task_id):
    conn = _connect()
    conn.execute("DELETE FROM fixed_tasks WHERE id = ?", (task_id,))
    conn.execute("DELETE FROM daily_tasks WHERE fixed_task_id = ?", (task_id,))
    conn.commit()
    conn.close()


# ── Daily tasks ──────────────────────────────────────────────

def ensure_daily_fixed_tasks(date_str):
    """
    For every fixed task, create a daily copy for *date_str* if one
    doesn't already exist.  Daily copies inherit the title at the time
    of creation.
    """
    conn = _connect()
    fixed = conn.execute("SELECT * FROM fixed_tasks").fetchall()
    for ft in fixed:
        existing = conn.execute(
            "SELECT id FROM daily_tasks WHERE task_date = ? AND fixed_task_id = ?",
            (date_str, ft["id"]),
        ).fetchone()
        if existing is None:
            conn.execute(
                "INSERT INTO daily_tasks (title, is_fixed, task_date, fixed_task_id) "
                "VALUES (?, 1, ?, ?)",
                (ft["title"], date_str, ft["id"]),
            )
    conn.commit()
    conn.close()


def get_daily_tasks(date_str):
    """Return today's tasks — fixed copies (already ensured) + temp tasks."""
    ensure_daily_fixed_tasks(date_str)
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM daily_tasks WHERE task_date = ? "
        "ORDER BY is_completed ASC, is_fixed DESC, id ASC",
        (date_str,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_temporary_task(title, date_str):
    conn = _connect()
    cur = conn.execute(
        "INSERT INTO daily_tasks (title, is_fixed, task_date) VALUES (?, 0, ?)",
        (title, date_str),
    )
    conn.commit()
    pk = cur.lastrowid
    conn.close()
    return pk


def toggle_task(task_id):
    conn = _connect()
    row = conn.execute(
        "SELECT is_completed FROM daily_tasks WHERE id = ?", (task_id,)
    ).fetchone()
    if row is not None:
        new_val = 0 if row["is_completed"] else 1
        conn.execute(
            "UPDATE daily_tasks SET is_completed = ? WHERE id = ?",
            (new_val, task_id),
        )
        conn.commit()
    conn.close()


def delete_daily_task(task_id):
    conn = _connect()
    conn.execute("DELETE FROM daily_tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def get_incomplete_tasks(date_str):
    conn = _connect()
    rows = conn.execute(
        "SELECT title FROM daily_tasks WHERE task_date = ? AND is_completed = 0",
        (date_str,),
    ).fetchall()
    conn.close()
    return [r["title"] for r in rows]



if __name__ == "__main__":
    init_db()
    today = datetime.date.today().isoformat()
    print("Today's tasks:", get_daily_tasks(today))
