"""
SQLite helpers for the Electricity Waste Detection system.
"""

import sqlite3
from datetime import datetime, date
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "energy.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS readings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ts          TEXT NOT NULL,
            current_a   REAL NOT NULL,
            power_w     REAL NOT NULL,
            occupancy   INTEGER NOT NULL,
            voltage_v   REAL NOT NULL DEFAULT 230.0,
            waste_flag  INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ts          TEXT NOT NULL,
            message     TEXT NOT NULL,
            power_w     REAL,
            occupancy   INTEGER,
            acknowledged INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )

    # Default settings
    defaults = {
        "voltage": "230",
        "waste_threshold_w": "40",      # power above this while empty = waste
        "empty_minutes": "3",           # minutes unoccupied before alert
        "room_name": "Lab / Classroom 101",
    }
    for k, v in defaults.items():
        cur.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (k, v),
        )

    conn.commit()
    conn.close()


def get_setting(key: str, default=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


def add_reading(current_a: float, power_w: float, occupancy: int,
                voltage_v: float = 230.0, waste_flag: int = 0):
    now = datetime.now().isoformat(timespec="seconds")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO readings (ts, current_a, power_w, occupancy, voltage_v, waste_flag)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (now, current_a, power_w, occupancy, voltage_v, waste_flag),
    )
    conn.commit()
    conn.close()
    return now


def add_alert(message: str, power_w: float = None, occupancy: int = None):
    now = datetime.now().isoformat(timespec="seconds")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO alerts (ts, message, power_w, occupancy, acknowledged)
        VALUES (?, ?, ?, ?, 0)
        """,
        (now, message, power_w, occupancy),
    )
    conn.commit()
    conn.close()


def get_recent_readings(limit: int = 100):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM readings ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return list(reversed(rows))


def get_latest_reading():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM readings ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_alerts(limit: int = 50, unacked_only: bool = False):
    conn = get_connection()
    cur = conn.cursor()
    if unacked_only:
        cur.execute(
            "SELECT * FROM alerts WHERE acknowledged = 0 ORDER BY id DESC LIMIT ?",
            (limit,),
        )
    else:
        cur.execute(
            "SELECT * FROM alerts ORDER BY id DESC LIMIT ?",
            (limit,),
        )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def acknowledge_alert(alert_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE alerts SET acknowledged = 1 WHERE id = ?",
        (alert_id,),
    )
    conn.commit()
    conn.close()


def get_daily_summary(day: str = None):
    """Return total kWh and waste events for a given day (YYYY-MM-DD)."""
    if day is None:
        day = date.today().isoformat()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            COUNT(*) AS samples,
            AVG(power_w) AS avg_power,
            MAX(power_w) AS max_power,
            SUM(CASE WHEN waste_flag = 1 THEN 1 ELSE 0 END) AS waste_samples
        FROM readings
        WHERE ts LIKE ?
        """,
        (f"{day}%",),
    )
    row = dict(cur.fetchone())
    # Rough energy estimate: assume each sample ~ 10 seconds apart
    # energy_kwh ≈ avg_power * (samples * 10 / 3600) / 1000
    samples = row["samples"] or 0
    avg_p = row["avg_power"] or 0
    hours = samples * 10 / 3600
    row["est_kwh"] = round(avg_p * hours / 1000, 4)
    row["day"] = day
    conn.close()
    return row


def get_hourly_power(day: str = None):
    if day is None:
        day = date.today().isoformat()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            substr(ts, 12, 2) AS hour,
            AVG(power_w) AS avg_power,
            MAX(occupancy) AS occupied
        FROM readings
        WHERE ts LIKE ?
        GROUP BY hour
        ORDER BY hour
        """,
        (f"{day}%",),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


if __name__ == "__main__":
    init_db()
    print(f"Database ready at {DB_PATH}")
