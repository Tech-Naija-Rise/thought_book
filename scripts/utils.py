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
import requests
import re
import hashlib
import customtkinter as ctk
import os
import sqlite3
import json
from .constants import (NOTES_DB, RECOVERY_FILE, logging, APP_ICON)
from typing import (List, Dict, Optional)
import winreg
# import tkinter.messagebox as tkmsg

def set_user_env_var(name, value):
    reg_path = r"Environment"
    reg_key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        reg_path,
        0,
        winreg.KEY_SET_VALUE
    )
    winreg.SetValueEx(reg_key, name, 0, winreg.REG_SZ, value)
    winreg.CloseKey(reg_key)
    logging.info(f"[+] User variable '{name}' set to '{value}'")


# # This will be the directory of every
# # BM app including BMTB. So it would be easier for each app to communicate with
# # the other
# if not os.getenv("BM"):
#     set_user_env_var("BM", os.path.abspath("."))
# else:
#     logging.warning("BM env variable already set.")


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
    if os.path.exists(NOTES_DB) and\
            os.path.getsize(NOTES_DB) > 10_000_000:
        logging.warning(
            "Warning: Notes database is very large and may slow startup.")
    try:
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
    except sqlite3.DatabaseError:
        logging.error(
            "Database is corrupted."
            " Please restore from backup or"
            " delete the file.")


def add_note(title: str, content: str) -> int:
    """Insert a new note. Returns the new note id."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO notes (title, content) VALUES (?, ?)",
            (title, content)
        )
        nid = c.lastrowid
        conn.commit()
    return nid  # type: ignore


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
            "SELECT id, title, content, created_at,"
            " updated_at FROM notes ORDER BY updated_at"
            " DESC"
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


def set_recovery_key(code: str):
    hashed = hashlib.sha256(code.encode('utf-8')).hexdigest()
    with open(RECOVERY_FILE, 'w') as f:
        f.write(hashed)


def verify_recovery_key(code: str) -> bool:
    if not os.path.exists(RECOVERY_FILE):
        return False
    entered_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()
    with open(RECOVERY_FILE, 'r') as f:
        stored_hash = f.readline().strip()
    return entered_hash == stored_hash


def _center_window(w, parent=None):
    """Center any window `w`"""
    w.update_idletasks()  # Actualize geometry information
    w.update()

    minwidth = w.winfo_reqwidth()
    minheight = w.winfo_reqheight()
    maxwidth = w.winfo_vrootwidth()
    maxheight = w.winfo_vrootheight()
    if parent is not None and parent.winfo_ismapped():
        x = parent.winfo_rootx() + (parent.winfo_width() - minwidth) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - minheight) // 2
        vrootx = w.winfo_vrootx()
        vrooty = w.winfo_vrooty()
        x = min(x, vrootx + maxwidth - minwidth)
        x = max(x, vrootx)
        y = min(y, vrooty + maxheight - minheight)
        y = max(y, vrooty)
        if w._windowingsystem == 'aqua':
            # Avoid the native menu bar which sits on top of everything.
            y = max(y, 22)
    else:
        x = (w.winfo_screenwidth() - minwidth) // 2
        y = (w.winfo_screenheight() - minheight) // 2

    w.wm_maxsize(maxwidth, maxheight)
    w.wm_geometry(f'+{x}+{y}')
    w.wm_deiconify()  # Become visible at the desired location


def center_window(w: ctk.CTk | ctk.CTkToplevel, wdth, hght, offsetx=0, offsety=0):
    """Center any CTk/Tk window on the screen."""
    w.update_idletasks()  # Ensure geometry info is accurate
    w.wm_withdraw()
    # Get actual window size
    width = w.winfo_reqwidth()
    height = w.winfo_reqheight()

    # Fallback if width/height not yet drawn
    if width == 1 and height == 1:
        width = w.winfo_reqwidth()
        height = w.winfo_reqheight()

    # Calculate center coordinates
    x = (w.winfo_screenwidth() - width) // 2
    y = (w.winfo_screenheight() - height) // 2

    # Move window to center without resizing it
    w.geometry(f'{wdth}x{hght}+{x+offsetx}+{y+offsety}')
    w.wm_deiconify()


def askstring(title="Input", prompt="Enter value:", show=None, placeholder="", width=300, height=150):
    """Universal CTk askstring dialog. Returns str or None."""

    # Root hidden window
    root = ctk.CTk()
    root.withdraw()
    root.iconbitmap(APP_ICON)
    # Create dialog
    dialog = ctk.CTkToplevel(root)
    dialog.title(title)
    dialog.winfo_toplevel().geometry(f"{width}x{height}")
    dialog.wm_iconbitmap(APP_ICON)
    dialog.transient(root)   # Tie dialog to root (only on top of it)
    try:
        dialog.grab_set()
    except Exception:
        pass
    # Prompt
    label = ctk.CTkLabel(dialog, text=prompt, wraplength=300)
    label.pack(pady=(15, 5))

    # Entry
    entry = ctk.CTkEntry(dialog, show=show, width=220,
                         placeholder_text=placeholder)
    entry.pack(pady=5)

    dialog.after_idle(lambda: entry.focus_set())

    result = {"value": None}

    def on_ok():
        result["value"] = entry.get()  # type: ignore
        dialog.destroy()

    def on_cancel():
        result["value"] = "exit"  # type: ignore
        dialog.destroy()

    # Shortcuts
    dialog.bind("<Escape>", lambda e: on_cancel())
    dialog.bind("<Return>", lambda e: on_ok())
    dialog.wm_protocol("WM_DELETE_WINDOW", on_cancel)

    # Buttons
    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(pady=10)

    ok_btn = ctk.CTkButton(btn_frame, text="OK", command=on_ok, width=80)
    ok_btn.pack(side="left", padx=5)

    cancel_btn = ctk.CTkButton(
        btn_frame, text="Cancel", command=on_cancel, width=80)
    cancel_btn.pack(side="left", padx=5)

    dialog.wait_window()
    root.destroy()

    return result["value"]


def count_words_in_string(text):
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def has_internet():
    try:
        requests.get("https://www.google.com", timeout=3)
        return True
    except Exception:
        return False

def connected_to_server(url):
    try:
        logging.info(f"Attempting to connect to server at '{url}'")
        response = requests.get(url, timeout=60)

        if 200 <= response.status_code < 300:
            logging.info("Connected to server successfully!")
            return True
        else:
            logging.warning(
                f"Server responded with status code: {response.status_code}")
            return False

    except requests.Timeout:
        logging.error("Connection timed out.")
        return False
    except requests.ConnectionError:
        logging.error("Failed to connect to server.")
        return False
    except requests.RequestException as e:
        logging.error(f"An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    # print(all_notes())
    pass


# class TrainingUI(ctk.CTk):
#     def __init__(self):
#         super().__init__()
#         self.title("GPT Training Progress")
#         self.geometry("360x120")

#         # Label for status
#         self.label = ctk.CTkLabel(self, text="Training not started…")
#         self.label.pack(fill="x", padx=10, pady=(10, 4))

#         # Progress bar
#         self.bar = ctk.CTkProgressBar(self)
#         self.bar.pack(fill="x", padx=10, pady=(0, 4))
#         self.bar.set(0.0)

#         # Percent text
#         self.percent = ctk.CTkLabel(self, text="0%")
#         self.percent.pack(fill="x", padx=10, pady=(0, 10))

#     def update_progress(self, current: int | str, end: int | str, message="Training..."):
#         """
#         Update the UI with training progress.
#         Pass current step, total steps (end), and an optional message.
#         """

#         # clamp between 0 and 1
#         progress = max(0.0, min(1.0, int(current) / int(end)))
#         self.bar.set(progress)
#         self.label.configure(text=message)
#         self.percent.configure(text=f"{int(progress * 100)}%")
#         self.update_idletasks()  # force UI refresh
