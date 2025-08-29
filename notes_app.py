"""
NotesApp - A Simple Note-Taking Application using CustomTkinter.

This application provides a clean and minimal interface for creating,
editing, and organizing notes, similar to a lightweight notes app.

Features:
- Sidebar list to display all saved notes.
- Title and content fields for each note.
- Create new notes with a single click.
- Automatically select and edit existing notes from the sidebar.
- Modern UI built with customtkinter.

Future Extensions:
- Persistent storage (JSON or SQLite) to save notes across sessions.
- Search and filter functionality for quick access.
- Dark/Light theme toggle.
- Keyboard shortcuts (e.g., Ctrl+N for new, Ctrl+S for save).

Usage:
    Run the script and use the UI to add and manage notes.
    Clicking on a note in the sidebar will load its title and content
    into the editor for easy editing.

Author: Umar Mahmud
"""


from utils import create_table, askstring, get_notes, delete_note, NOTES_DB, save_note
from tkinter import messagebox as tkmsg
import hashlib
import sys
from tkinter import simpledialog
import customtkinter as ctk
import json
import os

create_table()

RECOVERY_FILE = "recovery.key"


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


class SimpleSubstitution:
    def __init__(self):
        # Only a–i mapped
        self.encode_map = {
            "a": "01", "b": "02", "c": "03",
            "d": "04", "e": "05", "f": "06",
            "g": "07", "h": "08", "i": "09",

            "A": "11", "B": "12", "C": "13",
            "D": "14", "E": "15", "F": "16",
            "G": "17", "H": "18", "I": "19",

        }

        self.decode_map = {v: k for k, v in self.encode_map.items()}

    def encrypt(self, text: str) -> str:
        """Replace a–i with digits 1–9."""
        encoded = ""
        for char in text:
            encoded += self.encode_map.get(char, char)
        return encoded

    def decrypt(self, text: str) -> str:
        decoded = ""
        i = 0
        while i < len(text):
            pair = text[i:i+2]
            if pair in self.decode_map:
                decoded += self.decode_map[pair]
                i += 2
            else:
                decoded += text[i]
                i += 1
        return decoded

    def pass_hash(self, text: str) -> str:
        """
        Generate a secure SHA-256 hash of the password.
        Returns the hex digest string (64 characters).
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SettingsWindow(ctk.CTkToplevel):
    """Settings GUI window for NotesApp."""

    def __init__(self, parent, cipher):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("300x250")
        self.resizable(False, False)
        self.transient(parent)   # Tie dialog to parent (only on top of it)
        self.grab_set()   # make modal
        
        self.cipher = cipher
        self.parent = parent

        # Change password section
        ctk.CTkLabel(self, text="Change Password").pack(pady=(20, 5))
        self.change_pass_btn = ctk.CTkButton(
            self, text="Change Password", command=self.change_password)
        self.change_pass_btn.pack(pady=5)

        # Divider
        ctk.CTkLabel(self, text="Notes Management").pack(pady=(20, 5))

        # Clear all notes button
        self.clear_notes_btn = ctk.CTkButton(
            self,
            text="Clear All Notes",
            fg_color="red",
            hover_color="darkred",
            command=self.confirm_clear_all
        )
        self.clear_notes_btn.pack(pady=5)

    def confirm_clear_all(self):
        dialog = ctk.CTkInputDialog(
            text="Type 'YES' to delete ALL notes permanently:",
            title="Confirm Clear All"
        )
        answer = dialog.get_input()
        if answer and answer.strip().upper() == "YES":
            from utils import clear_all_notes
            clear_all_notes()
            self.parent.notes.clear()
            self.parent.refresh_list()
            self.parent.title_entry.delete(0, "end")
            self.parent.textbox.delete("1.0", "end")
            self.parent.current_index = None
            tkmsg.showinfo("Success", "All notes deleted successfully!")

    def verify_current_password(self):
        """Ask user to enter current password for verification."""
        if not os.path.exists("pass.pass"):
            tkmsg.showerror("Error", "No password set yet.")
            return False

        entered = askstring(
            "Verify Password", "Enter current password:", show="*")
        if entered is None:
            return False

        with open("pass.pass", "r") as f:
            stored_hash = f.readline().strip()

        if self.cipher.pass_hash(entered) == stored_hash:
            return True
        else:
            tkmsg.showerror("Error", "Incorrect password.")
            return False

    def change_password(self):
        """Change the app password."""
        if not self.verify_current_password():
            return

        new_pass = askstring(
            "New Password", "Enter new password:", show="*")
        if not new_pass:
            tkmsg.showinfo("Info", "Password change cancelled.")
            return

        with open("pass.pass", "w") as f:
            f.write(self.cipher.pass_hash(new_pass))
        tkmsg.showinfo("Info", "Password changed successfully.")


class NotesApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.cipher = SimpleSubstitution()
        self.encrypt = self.cipher.encrypt
        self.decrypt = self.cipher.decrypt

        self.autosave_after_id = None

        # unlock app with password
        self.password = None
        self.password_file = "pass.pass"

        # unlock app with password
        self.locked = True
        while self.locked:
            result = self.ask_password()
            if result is True:
                self.locked = False
            elif result == "Cancelled":
                sys.exit()
            else:
                tkmsg.showerror("Error", "Incorrect password. Try again.")

        if not self.locked:
            self.title("Thought Book")
            self.geometry("800x500")

            self.notes_file = NOTES_DB
            # After loading notes
            self.notes = self.load_notes()
            self.current_index = None

            # Sidebar for notes list
            self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
            self.sidebar.pack(side="left", fill="y")

            # Example button in sidebar or menu
            settings_btn = ctk.CTkButton(
                self.sidebar,
                fg_color="#555555", text="Settings", command=lambda: SettingsWindow(self, self.cipher))
            settings_btn.pack(pady=5)

            button_frame = ctk.CTkFrame(self.sidebar)
            button_frame.pack(pady=5)

            # Buttons
            self.add_button = ctk.CTkButton(
                button_frame,
                text="Add Note",
                fg_color="#555555",
                width=80,
                command=self.add_note)
            self.add_button.pack(side="left", pady=5, padx=2)
            self.delete_button = ctk.CTkButton(
                button_frame,
                text="Delete Note",
                fg_color="#555555",
                hover_color="darkred",
                text_color="white",
                command=self.delete_note,
                width=80,
            )
            self.delete_button.pack(side="left", pady=5)

            self.scrollable_list = ctk.CTkScrollableFrame(
                self.sidebar, width=200, height=400)
            self.scrollable_list.pack(fill="both", expand=True)

            self.note_buttons = []
            self.refresh_list()

            # Note editor
            self.editor_frame = ctk.CTkFrame(self)
            self.editor_frame.pack(side="right", fill="both",
                                   expand=True, padx=10, pady=10)

            self.title_entry = ctk.CTkEntry(
                self.editor_frame, placeholder_text="Title")
            self.title_entry.pack(fill="x", pady=5)

            self.textbox = ctk.CTkTextbox(
                self.editor_frame, undo=True, wrap=ctk.WORD)
            self.textbox.pack(fill="both", expand=True, pady=5)

            self.title_entry.bind(
                "<KeyRelease>", lambda e: self.schedule_autosave())
            self.textbox.bind(
                "<KeyRelease>", lambda e: self.schedule_autosave())
            self.title_entry.bind(
                "<Return>", lambda e: self.textbox.focus_set())
            self.wm_protocol("WM_DELETE_WINDOW", self.on_close)

            # Only add a blank note if no notes exist yet
            if not self.notes:
                self.add_note()
            else:
                # Auto-load the first saved note for convenience
                self.load_note(0)

    def on_close(self):
        """Handle app close event."""
        # Save whatever is in the editor before exit
        self.save_current_note()
        self.destroy()

    def schedule_autosave(self):
        """Schedule autosave after a delay to avoid excessive saves."""
        if self.autosave_after_id:  # cancel previous timer
            self.after_cancel(self.autosave_after_id)
        self.autosave_after_id = self.after(
            500, self.save_current_note)  # 5s delay

    def load_notes(self) -> list:
        """Load notes from SQLite database"""
        return get_notes()

    def refresh_list(self):
        """Refresh the sidebar list of notes"""
        # Clear old buttons
        for btn in self.note_buttons:
            btn.destroy()
        self.note_buttons.clear()

        for idx, note in enumerate(self.notes):
            title = note.get("title", "Untitled")
            display_title = self.truncate_text(
                title, max_length=20)
            btn = ctk.CTkButton(
                self.scrollable_list, fg_color="#333333",
                text=display_title, width=180,
                command=lambda i=idx: self.load_note(i))

            btn.pack(pady=2)
            self.note_buttons.append(btn)

    def truncate_text(self, text, max_length=20):
        """Truncate text to fit in the sidebar button."""
        return text if len(text) <= max_length else text[:max_length - 3] + "..."

    def load_note(self, index):
        """Load a note into the editor by index, saving previous note first"""
        if self.current_index is not None:
            self.save_current_note(index_to_save=self.current_index)

        self.current_index = index
        note = self.notes[index]

        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, note.get("title", ""))
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", self.decrypt(note.get("content", "")))

        for i, btn in enumerate(self.note_buttons):
            btn.configure(fg_color="#555555" if i == index else "#333333")

    def delete_note(self):
        if tkmsg.askyesno("Confirm Delete", "Are you sure you want to delete this note?"):
            if self.current_index is not None:
                note_id = self.notes[self.current_index].get("id")
                if note_id:
                    delete_note(note_id)
                    del self.notes[self.current_index]

                # Reset editor
                self.title_entry.delete(0, "end")
                self.textbox.delete("1.0", "end")
                self.current_index = None

                self.refresh_list()

    def forgot_password(self):
        code = askstring(
            "Recovery", "Enter recovery code:", show="*")
        if code is None:
            return False

        if verify_recovery_key(code):
            new_pass = askstring(
                "New Password", "Enter new password:", show="*")
            if new_pass:
                with open(self.password_file, 'w') as f:
                    f.write(self.cipher.pass_hash(new_pass))
                tkmsg.showinfo("Success", "Password reset successfully!")
                return True
        else:
            tkmsg.showerror("Error", "Invalid recovery code.")
            return False

    def ask_password(self):
        try:
            with open(self.password_file, 'r') as f:
                PASSWORD_HASH = f.readline().strip()

            entered = askstring(
                "Password", "Enter password (or leave blank to reset):", show="*")
            if entered is None:
                return "Cancelled"

            if entered == "":
                return self.forgot_password()

            if self.cipher.pass_hash(entered) == PASSWORD_HASH:
                return True
            else:
                tkmsg.showerror("Error", "Incorrect password.")
                return False

        except FileNotFoundError:
            new_pass = askstring(
                "Password", "Create password:", show="*")
            if new_pass is None:
                return "Cancelled"

            with open(self.password_file, 'w') as f:
                f.write(self.cipher.pass_hash(new_pass))

            recovery = askstring(
                "Recovery Code", "Set a recovery code (write it down somewhere safe):", show="*")
            if recovery:
                set_recovery_key(recovery)
            tkmsg.showinfo("Info", "Password and recovery code set.")
            return True

    def save_current_note(self, index_to_save=None):
        """Save the note being edited (or a specific index)"""
        idx = index_to_save if index_to_save is not None else self.current_index
        content = self.textbox.get("1.0", "end-1c").strip()
        content = self.encrypt(content)
        title = self.title_entry.get()

        if idx is not None:
            note_id = self.notes[idx].get("id")
            if note_id:
                # update existing note
                save_note(title, content, note_id)
                self.notes[idx] = {"id": note_id,
                                   "title": title, "content": content}
            else:
                # fallback insert
                new_id = save_note(title, content)
                self.notes[idx] = {"id": new_id,
                                   "title": title, "content": content}
        else:
            # new note
            new_id = save_note(title, content)
            self.notes.append(
                {"id": new_id, "title": title, "content": content})
            self.current_index = len(self.notes) - 1

        self.refresh_list()

    def add_note(self):
        """Create a new note, saving current note first"""
        if self.current_index is not None:
            self.save_current_note(index_to_save=self.current_index)

        self.current_index = None
        self.title_entry.delete(0, "end")
        self.textbox.delete("1.0", "end")

        self.title_entry.insert(0, "New Note")
        self.title_entry.focus_set()

        self.save_current_note()

        self.title_entry.select_range(0, "end")
        self.title_entry.focus()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = NotesApp()
    app.mainloop()
