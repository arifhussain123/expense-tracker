import os
import sqlite3

from flask import g

# The database lives at the project root (already listed in .gitignore).
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "expense_tracker.db",
)


def get_db():
    """Return a SQLite connection for the current request.

    Rows come back as sqlite3.Row (dict-like access by column name) and
    foreign keys are enforced, which SQLite disables by default.
    """
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(exception=None):
    """Close the request's connection, if one was opened."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    """Wire close_db into the app so connections never leak."""
    app.teardown_appcontext(close_db)


def init_db():
    """Create every table. Safe to call on every start-up."""
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            email         TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at    TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            amount      REAL NOT NULL,
            category    TEXT NOT NULL,
            description TEXT,
            spent_on    TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_expenses_user_date
            ON expenses (user_id, spent_on);
        """
    )
    db.commit()


def seed_db():
    """Insert sample data for development. Does nothing if users already exist."""
    from werkzeug.security import generate_password_hash

    db = get_db()
    if db.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]:
        return

    cursor = db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Nitish Kumar", "nitish@example.com", generate_password_hash("password123")),
    )
    user_id = cursor.lastrowid

    db.executemany(
        """INSERT INTO expenses (user_id, amount, category, description, spent_on)
           VALUES (?, ?, ?, ?, ?)""",
        [
            (user_id, 4500.00, "Bills", "Electricity bill", "2026-03-04"),
            (user_id, 3200.00, "Food", "Groceries for the week", "2026-03-09"),
            (user_id, 2050.00, "Health", "Pharmacy", "2026-03-14"),
            (user_id, 1800.00, "Transport", "Monthly metro pass", "2026-03-18"),
        ],
    )
    db.commit()
