"""Local SQLite database for The Hangout.

Provides a local, Google-independent data store. Data is ingested from the
Rista Sync Excel file (and optionally directly from the Rista API).
"""
import sqlite3
from pathlib import Path
from contextlib import contextmanager

from hangout.config import PROJECT_ROOT

DB_PATH = PROJECT_ROOT / "hangout.db"


@contextmanager
def get_conn():
    """Get a database connection with WAL mode for concurrent reads."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS daily_sales (
                date         TEXT PRIMARY KEY,
                total_net    REAL NOT NULL DEFAULT 0,
                total_cost   REAL NOT NULL DEFAULT 0,
                total_profit REAL NOT NULL DEFAULT 0,
                margin_pct   REAL NOT NULL DEFAULT 0,
                synced_at    TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS section_sales (
                date         TEXT NOT NULL,
                section      TEXT NOT NULL,
                net          REAL NOT NULL DEFAULT 0,
                cost         REAL NOT NULL DEFAULT 0,
                profit       REAL NOT NULL DEFAULT 0,
                PRIMARY KEY (date, section),
                FOREIGN KEY (date) REFERENCES daily_sales(date)
            );

            CREATE TABLE IF NOT EXISTS expenses (
                name         TEXT PRIMARY KEY,
                amount       REAL NOT NULL DEFAULT 0,
                category     TEXT NOT NULL DEFAULT 'fixed',
                updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_daily_sales_date ON daily_sales(date DESC);
            CREATE INDEX IF NOT EXISTS idx_section_sales_date ON section_sales(date DESC);
        """)


def upsert_daily_sale(conn, date, total_net, total_cost, total_profit, margin_pct):
    """Insert or update a daily sales record."""
    conn.execute("""
        INSERT INTO daily_sales (date, total_net, total_cost, total_profit, margin_pct, synced_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(date) DO UPDATE SET
            total_net = excluded.total_net,
            total_cost = excluded.total_cost,
            total_profit = excluded.total_profit,
            margin_pct = excluded.margin_pct,
            synced_at = datetime('now')
    """, (date, total_net, total_cost, total_profit, margin_pct))


def upsert_section_sale(conn, date, section, net, cost, profit):
    """Insert or update a section sales record."""
    conn.execute("""
        INSERT INTO section_sales (date, section, net, cost, profit)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(date, section) DO UPDATE SET
            net = excluded.net,
            cost = excluded.cost,
            profit = excluded.profit
    """, (date, section, net, cost, profit))


def upsert_expense(conn, name, amount, category="fixed"):
    """Insert or update an expense record."""
    conn.execute("""
        INSERT INTO expenses (name, amount, category, updated_at)
        VALUES (?, ?, ?, datetime('now'))
        ON CONFLICT(name) DO UPDATE SET
            amount = excluded.amount,
            category = excluded.category,
            updated_at = datetime('now')
    """, (name, amount, category))
