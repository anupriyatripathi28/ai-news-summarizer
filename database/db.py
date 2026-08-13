"""
database/db.py
----------------
All SQLite database logic lives here, kept separate from app.py so the
data layer can be reused, tested, or swapped out independently of Flask.

The database file itself (news_summarizer.db) is created automatically
inside this "database/" folder the first time the app runs.
"""

import sqlite3
import os
from datetime import datetime

# Absolute path to the .db file so it always resolves correctly no matter
# where the app is launched from.
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "news_summarizer.db")


def get_connection():
    """Return a new SQLite connection with dict-like row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    return conn


def init_db():
    """
    Create the 'articles' table if it doesn't already exist.
    Called once when the Flask app starts up.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            summary TEXT NOT NULL,
            key_points TEXT NOT NULL,       -- stored as JSON string
            sentiment TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_article(url, title, content, summary, key_points_json, sentiment):
    """
    Insert one summarized article into the database.
    key_points_json should already be a JSON-encoded string (a list of points).
    Returns the new row's id.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO articles (url, title, content, summary, key_points, sentiment, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            url,
            title,
            content,
            summary,
            key_points_json,
            sentiment,
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_all_articles():
    """Return every saved article, most recent first (without full content, for a fast list view)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, url, title, summary, sentiment, created_at
        FROM articles
        ORDER BY created_at DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_article_by_id(article_id):
    """Return a single full article record (including content and key points) by id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_article(article_id):
    """Delete a single history entry by id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM articles WHERE id = ?", (article_id,))
    conn.commit()
    conn.close()
