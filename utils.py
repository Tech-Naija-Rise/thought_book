"""
SQLite helper for NotesApp

Provides a tiny, well-documented API the main app can import:
- NOTES_DB: path to the sqlite file
- create_table(): create DB schema
- add_note(title, content) -> id
- update_note(id, title, content)
- save_note(title, content, note_id=None) -> id (insert or update)
- get_notes() -> list[dict]
- delete_note(id)
- migrate_from_json(path) -> number of imported notes

USAGE:
    from utils import create_table, get_notes, save_note, delete_note
    create_table()  # call once at app start

Notes: this module expects the caller to handle encryption/decryption of `content`.
"""

import os
import sqlite3
import json
from tkinter import dialog
from typing import List, Dict, Optional

# Put the DB next to this utils.py file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NOTES_DB = os.path.join(BASE_DIR, "notes.db")


def get_connection() -> sqlite3.Connection:
    """Return a DB connection. Caller doesn't need to commit when using `with`.
    """
    return sqlite3.connect(NOTES_DB)


def create_table() -> None:
    """Create the notes table if it doesn't exist.

    Columns:
      - id (PK)
      - title
      - content (encrypted or plain text, the app decides)
      - created_at
      - updated_at
    """
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()


def add_note(title: str, content: str) -> int:
    """Insert a new note. Returns the new note id."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO notes (title, content) VALUES (?, ?)", (title, content)
        )
        nid = c.lastrowid
        conn.commit()
    return nid # type: ignore


def update_note(note_id: int, title: str, content: str) -> None:
    """Update an existing note.

    Note: this also updates the updated_at timestamp.
    """
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE notes SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (title, content, note_id),
        )
        conn.commit()


def save_note(title: str, content: str, note_id: Optional[int] = None) -> int:
    """Save a note. If note_id is provided it will update, otherwise insert.

    Returns the id of the saved note.
    """
    if note_id:
        update_note(note_id, title, content)
        return note_id
    return add_note(title, content)

def clear_all_notes():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM notes")
        conn.commit()

def get_notes() -> List[Dict]:
    """Return all notes as a list of dicts ordered by updated_at desc."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, title, content, created_at, updated_at FROM notes ORDER BY updated_at DESC"
        )
        rows = c.fetchall()

    notes: List[Dict] = []
    for r in rows:
        notes.append(
            {
                "id": r[0],
                "title": r[1] or "",
                "content": r[2] or "",
                "created_at": r[3],
                "updated_at": r[4],
            }
        )
    return notes


def delete_note(note_id: int) -> None:
    """Delete a note by id."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()


def migrate_from_json(json_path: str = "notes.json") -> int:
    """One-time migration: import notes from a JSON file.

    The expected JSON format is a list of objects with at least
    `title` and `content` fields, e.g.:
        [ {"title": "x", "content": "y"}, ... ]

    Returns the number of notes imported.
    """
    if not os.path.exists(json_path):
        return 0

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for item in data:
        title = item.get("title", "")
        content = item.get("content", "")
        add_note(title, content)
        count += 1

    return count






import customtkinter as ctk

def askstring(title="Input", prompt="Enter value:", show=None):
    """Universal CTk askstring dialog. Returns str or None."""
    
    # Root hidden window
    root = ctk.CTk()
    root.withdraw()  
    # Create dialog
    dialog = ctk.CTkToplevel(root)
    dialog.title(title)
    dialog.geometry("300x150")
    # dialog.lift()   # bring above all windows
    dialog.transient(root)   # Tie dialog to root (only on top of it)
    dialog.grab_set()        # Keep it modal (block other app windows)


    
    # Prompt
    label = ctk.CTkLabel(dialog, text=prompt)
    label.pack(pady=(15, 5))
    
    # Entry
    entry = ctk.CTkEntry(dialog, show=show, width=220)
    entry.pack(pady=5)

    dialog.after_idle(lambda: entry.focus_set())

    result = {"value": None}
    
    def on_ok():
        result["value"] = entry.get() # type: ignore
        dialog.destroy()
    
    def on_cancel():
        dialog.destroy()

    # Shortcuts
    dialog.bind("<Escape>", lambda e: on_cancel())
    dialog.bind("<Return>", lambda e: on_ok())

    # Buttons
    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(pady=10)
    
    ok_btn = ctk.CTkButton(btn_frame, text="OK", command=on_ok, width=80)
    ok_btn.pack(side="left", padx=5)
    
    cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=on_cancel, width=80)
    cancel_btn.pack(side="left", padx=5)
    
    dialog.wait_window()
    root.destroy()
    
    return result["value"]


__all__ = [
    "NOTES_DB",
    "create_table",
    "add_note",
    "update_note",
    "save_note",
    "get_notes",
    "delete_note",
    "migrate_from_json",
]
