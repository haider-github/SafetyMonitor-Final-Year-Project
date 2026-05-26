import sqlite3
from datetime import datetime

DB_PATH = "safety.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS workers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        worker_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        phone TEXT,
        department TEXT,
        location TEXT,
        image_path TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS violations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        worker_id TEXT,
        missing_gear TEXT,
        timestamp TEXT,
        snapshot_path TEXT
    )''')
    conn.commit()
    conn.close()
    print("Database ready!")


def add_worker(worker_id, name, phone="", department="", location="", image_path=""):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO workers (worker_id, name, phone, department, location, image_path) VALUES (?, ?, ?, ?, ?, ?)",
            (worker_id, name, phone, department, location, image_path)
        )
        conn.commit()
        result = "success"
    except sqlite3.IntegrityError:
        result = "exists"
    conn.close()
    return result


def get_worker_by_id(worker_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT * FROM workers WHERE worker_id = ?", (worker_id,)
    ).fetchone()
    conn.close()
    return row


def log_violation(worker_id, missing_gear, snapshot_path=""):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO violations (worker_id, missing_gear, timestamp, snapshot_path) VALUES (?, ?, ?, ?)",
        (worker_id, missing_gear, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), snapshot_path)
    )
    conn.commit()
    conn.close()


def get_all_violations():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT v.id, v.worker_id, v.missing_gear, v.timestamp, v.snapshot_path, "
        "w.name, w.department, w.location, w.phone "
        "FROM violations v LEFT JOIN workers w ON v.worker_id = w.worker_id "
        "ORDER BY v.id DESC"
    ).fetchall()
    conn.close()
    return rows


def get_all_workers():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT * FROM workers").fetchall()
    conn.close()
    return rows


def get_violation_count():
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM violations").fetchone()[0]
    conn.close()
    return count


def get_worker_count():
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM workers").fetchone()[0]
    conn.close()
    return count


def get_recent_violations(limit=5):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT v.id, v.worker_id, v.missing_gear, v.timestamp, v.snapshot_path, "
        "w.name, w.department, w.phone "
        "FROM violations v LEFT JOIN workers w ON v.worker_id = w.worker_id "
        "ORDER BY v.id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return rows
def update_worker(worker_id, name, phone, department, location, image_path=None):
    conn = sqlite3.connect(DB_PATH)
    if image_path:
        conn.execute(
            "UPDATE workers SET name=?, phone=?, department=?, location=?, image_path=? WHERE worker_id=?",
            (name, phone, department, location, image_path, worker_id)
        )
    else:
        conn.execute(
            "UPDATE workers SET name=?, phone=?, department=?, location=? WHERE worker_id=?",
            (name, phone, department, location, worker_id)
        )
    conn.commit()
    conn.close()


def delete_worker(worker_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM workers WHERE worker_id=?", (worker_id,))
    conn.commit()
    conn.close()