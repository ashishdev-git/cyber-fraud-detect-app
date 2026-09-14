import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4


@contextmanager
def connect():
    path = Path(os.getenv('CYBERSHIELD_DB', str(Path(__file__).resolve().parents[1] / 'data' / 'feedback.sqlite3')))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(path), timeout=10)
    try:
        with db:
            db.execute('CREATE TABLE IF NOT EXISTS assessments (id TEXT PRIMARY KEY, risk TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
            db.execute('CREATE TABLE IF NOT EXISTS feedback (analysis_id TEXT PRIMARY KEY, rating TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
            yield db
    finally:
        db.close()


def record_assessment(risk):
    identifier = str(uuid4())
    with connect() as db:
        db.execute('INSERT INTO assessments (id, risk) VALUES (?, ?)', (identifier, risk))
    return identifier


def save_feedback(identifier, rating):
    with connect() as db:
        if db.execute('SELECT 1 FROM assessments WHERE id=?', (identifier,)).fetchone() is None:
            return False
        db.execute('INSERT INTO feedback (analysis_id, rating) VALUES (?, ?) ON CONFLICT(analysis_id) DO UPDATE SET rating=excluded.rating, created_at=CURRENT_TIMESTAMP', (identifier, rating))
    return True
