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

import re
import os
import sys
import logging
import datetime
import threading
import time
from tkinter import messagebox as tkmsg
from tkinter.messagebox import askyesno
import webbrowser


import customtkinter as ctk
import requests


from scripts.constants import (
    EMAIL_ID_FILE,
    ID_FILE,
    LICENSE_KEY_FILE,
    METRICS_FILE,
    PASS_FILE,
    APP_NAME,
    APP_ICON,
    METRICS_FILE_CONTENT,
    TNR_BMTB_SERVER,
    read_file,
    write_file,
    USER_APP_ID
)
from scripts.bma_express import ActivitiesAPI
from scripts.utils import (
    SimpleCipher,
    create_table,
    askstring, get_notes,
    delete_note, NOTES_DB,
    save_note, set_recovery_key,
    verify_recovery_key,
    has_internet
)
from scripts.settings import SettingsWindow, load_settings


# setup logging once (top-level of your file, before class)


class NotesApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        try:
            if not os.path.exists(NOTES_DB):
                create_table()
        except Exception as e:
            logging.error(f"Error while creating table: {e}")

        self.cipher = SimpleCipher()
        self.encrypt = self.cipher.encrypt
        self.decrypt = self.cipher.decrypt

        self.autosave_after_id = None

        # unlock app with password
        self.password = None
        self.password_file = PASS_FILE

        # TODO: when app starts, it opens the main UI
        # then password setter appears. Makes good UX

        settings = load_settings()
        self.locked = False

        if settings.get("request_password", False):
            self.locked = True
            while self.locked:
                result = self.ask_password()
                if result is True:
                    self.locked = False
                elif result in ("Cancelled", "exit"):
                    sys.exit()
                else:
                    tkmsg.showerror("Error", "Incorrect password. Try again.")

        self.current_note = ""
        self.max_words_b4_training = 1000
        self.focused = ctk.BooleanVar(self, False, "focused")

        self.start_ui()
        self.freemium_locked = True

        self.__freemium_note_count_feature(self.freemium_locked)

    def __freemium_note_count_feature(self, locked=True):
        """This is for the freemium
        When the app starts, we check
        for a file with a hashed number
        if the number of notes reaches
        that number, then we remind them
        and redirect to website to own the 
        app.

        The button to add more notes will be disabled
        so as not to have more than `note_count_limit`

        In the first place, don't allow them to create 
        more than 10
        """
        if locked:
            info = METRICS_FILE_CONTENT
            try:
                count = int(info['note_count_limit'])
                urc = int(info['upgrade_reminder_count'])
                mur = int(info['max_upgrade_remind'])
            except KeyError as e:
                logging.error(f"Can't find keys: {e}")

            if self.get_note_count() >= count:
                # remind once only TODO: remove 'not'
                if not int(urc) < int(mur):
                    ans = tkmsg.askyesnocancel("Free version limit reached",
                                               "Your free note limit has been reached\n"
                                               "Would you like to upgrade now "
                                               "to have access "
                                               "to all features?")

                    info['upgrade_reminder_count'] += 1
                    logging.info(info)
                    write_file(METRICS_FILE, info)

                    if ans is not None:
                        if ans:
                            # go to the webpage
                            self.freemium_reg_flow()
                        else:
                            # lock the other notes created
                            pass

                self.add_button.configure(
                    text="Upgrade to add more",
                    command=self.freemium_reg_flow)

            elif self.get_note_count() < count:
                self.add_button.configure(text="Add Note",
                                          command=self.add_note)
        else:
            self.add_button.configure(text="Add Note",
                                      command=self.add_note)

    def __ask_email(self):
        if not os.path.exists(EMAIL_ID_FILE):
            self.user_email = askstring("Email Required",
                                        "Enter your email (required for payment receipt):")
            info = {"user_email": self.user_email}
            write_file(EMAIL_ID_FILE, info)
        else:
            info = read_file(EMAIL_ID_FILE)
            self.user_email = info["user_email"]

    def freemium_reg_flow(self):
        self.__ask_email()
        threading.Thread(target=self.__freemium_reg_flow, daemon=True).start()

    def _validate_email(self, email):
        return True

    def __freemium_reg_flow(self):
        try:

            resp = requests.post(f"{TNR_BMTB_SERVER}/payment",
                                 json={"device_id": USER_APP_ID, "amount": 500,
                                       "email": self.user_email})
            # open resp.json()['data']['authorization_url'] in webview/browser
            reference = str(resp.json()["data"]["reference"])
            logging.info(f"Payment initiated, reference: {reference}")
            webbrowser.open_new_tab(resp.json()['data']['authorization_url'])
            time.sleep(5)

            while True:
                r = requests.post(
                    f"{TNR_BMTB_SERVER}/claim", json={"reference": reference, "device_id": USER_APP_ID})
                j = r.json()
                if j["status"] == "ok":
                    license = j["license"]
                    self.save_encrypted_locally(license)
                    break
                # wait a few seconds then retry
                time.sleep(5)

        except Exception as e:
            logging.error(f"Error during payment processing: {e}")
            tkmsg.showerror(
                "Error", "Failed to initiate payment. ")

        # if freemium_reg code is valid, then unlock that feature
        # else, keep it locked.

        # meaning that we have to check in the beginning if the app
        # is registered so as to unlock before starting app.

    def save_encrypted_locally(self, license):
        with open(LICENSE_KEY_FILE, "w") as f:
            f.write(self.cipher.encrypt(license))
        self.freemium_locked = False
        self.add_button.configure(text="Add Note", command=self.add_note)

    def validate_freemium_reg_code(self):
        pass

    def get_note_count(self):
        return len(self.load_notes())

    def start_ui(self):
        if not self.locked:
            self.title(APP_NAME)
            self.geometry("800x500")
            self.wm_iconbitmap(APP_ICON)

            self.notes_file = NOTES_DB
            # After loading notes
            self.notes = self.load_notes()
            self.current_index = None

            # Sidebar for notes list
            self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
            if not self.focused.get():
                self.sidebar.pack(side="left", fill="y")

            # AI coming soon
            self.suggest_label = ctk.CTkLabel(
                self.sidebar,
                text="AI Suggestion",
            )
            # self.suggest_label.pack()

            button_frame = ctk.CTkFrame(self.sidebar)
            button_frame.pack(pady=5, fill="x")

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
            self.delete_button.pack(side="right", pady=5)

            self.scrollable_list = ctk.CTkScrollableFrame(
                self.sidebar, width=200)
            self.scrollable_list.pack(fill="both", expand=True)

            # Example button in sidebar or menu
            pair = ctk.CTkFrame(self.sidebar)
            pair.pack(fill="x")
            settings_btn = ctk.CTkButton(
                pair,
                fg_color="#555555",
                text="Settings",
                width=80,
                command=lambda: SettingsWindow(self, self.cipher))
            settings_btn.pack(side="left", pady=5)

            focus_btn = ctk.CTkButton(
                pair, fg_color="#555555",
                width=80,
                text="Focus",
                command=self.focus)
            focus_btn.pack(side="right",)

            self.note_buttons = []
            self.refresh_list()

            # Note editor
            self.right_side = ctk.CTkFrame(self, height=300)
            self.right_side.pack(side="right", fill="both",
                                 expand=True, padx=10)

            self.editor_frame = ctk.CTkFrame(self.right_side)
            self.editor_frame.pack(side="top",
                                   pady=10, expand=True, fill="both")

            self.title_entry = ctk.CTkEntry(
                self.editor_frame, placeholder_text="Title")
            self.title_entry.pack(fill="x", pady=5)

            self.textbox = ctk.CTkTextbox(
                self.editor_frame, undo=True, wrap=ctk.WORD)
            self.textbox.pack(fill="both", expand=True, pady=5)

            self.extra_bt_frame = ctk.CTkFrame(self.right_side,)
            self.unfocus_btn = ctk.CTkButton(self.extra_bt_frame,
                                             text="Unfocus",
                                             width=80,
                                             command=self.focus,
                                             fg_color="#555555")
            self.title_entry.bind(
                "<KeyRelease>", lambda e: self.schedule_autosave())
            self.textbox.bind(
                "<KeyRelease>", lambda e: self.schedule_autosave())
            self.title_entry.bind(
                "<Return>", lambda e: self.textbox.focus_set())
            self.wm_protocol("WM_DELETE_WINDOW", self.on_close)

            # inside __init__ after creating textbox
            self.textbox.bind("<Return>", self.handle_multiline)

            # Only add a blank note if no notes exist yet
            if not self.notes:
                self.add_note()
            else:
                # Auto-load the first saved note for convenience
                self.load_note(0)

        self.bma = ActivitiesAPI()

    def focus(self):
        self.focused.set(not self.focused.get())
        if self.focused.get():
            self.unfocus_btn.pack_forget()
            self.extra_bt_frame.pack_forget()
            self.sidebar.pack(side="left", fill="y")
        else:
            self.extra_bt_frame.pack(fill="x",
                                     pady=5,
                                     side="bottom")
            self.unfocus_btn.pack(side="left")
            self.sidebar.pack_forget()

    def on_close(self):
        r""""""
        try:
            poas = self.get_poas(self.get_current_note()[1])
            self.bma.make_activities(poas)
        except Exception as e:
            logging.error(f"While closing, something's happening: {e}")
        finally:
            logging.info(
                f"Closed app successfully")
            self.destroy()  # immediately close window

    def get_current_note(self, index_to_save=None):
        idx = index_to_save if index_to_save is not None else self.current_index
        content = self.textbox.get("1.0", "end-1c").strip()

        # This line is hackable but not from outside
        # content = self.encrypt(content)

        # Encryption is not needed in this particular function
        # because poa checker will need to see the raw text
        return idx, content

    def get_poas(self, current_note):
        if current_note.strip():
            self.poas = re.findall(
                # find anything that follows []
                # and is before a newline or full stop
                r"\[\s?\] ?[^\.|\n]+",
                current_note
            )
            logging.info(f"Found {len(self.poas)} POA's")
            # clean them by removing the []
            self.poas = [re.sub(r"\[\s?\]\s?", "", x) for x in self.poas]
            return self.poas

    # XXX For training an AI: Experimental
    def _corpus_manager(self, _all_notes):
        corpus_file = f"corpus_{datetime.datetime.now().date()}.txt"
        try:
            if (_all_notes[0] > self.max_words_b4_training) and (
                (_all_notes[0] % self.max_words_b4_training >= 0
                 ) and (
                     _all_notes[0] % self.max_words_b4_training <= 500)):
                # This already runs in its own thread
                # self.ac.train_AI(_all_notes[1], _all_notes[0])
                if askyesno("Fine-tune ready",
                            "You've written approximately "
                            f"{_all_notes[0]} new words. "
                            "Save all notes as corpus?"):
                    with open(
                            corpus_file,
                            "w") as f:
                        f.write(_all_notes[1])
                    logging.info(
                        f"Done making corpus at {os.path.abspath(corpus_file)}")
        except Exception as e:
            logging.error(f"Failed to start training: {e}")

    def schedule_autosave(self):
        """Schedule autosave after a delay to avoid excessive saves."""
        if self.autosave_after_id:  # cancel previous timer
            self.after_cancel(self.autosave_after_id)
        self.autosave_after_id = self.after(
            500, self.save_current_note)

    def load_notes(self) -> list:
        """Load notes from SQLite database"""
        return get_notes()

    def refresh_list(self):
        """Refresh the sidebar list of notes

        For freemium: we will always check the note
        limit and modify the add button accordingly.

        """

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

        # Freemium feature
        self.__freemium_note_count_feature()

    def forgot_password(self):
        code = askstring(
            "Recovery", "Enter recovery "
            "code\n\nWrite this recovery code "
            "down in a safe place.\n Losing it "
            "means you cannot reset your "
            "password.", show="*")

        if code is None:
            return False

        elif code == "exit":
            exit()

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

            elif entered == "exit":
                return "exit"

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
        idx, content = self.get_current_note(index_to_save)

        # Always encrypt before saving
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

    def handle_multiline(self, event=None):
        # Get current line
        index = self.textbox.index("insert linestart")
        line_text = self.textbox.get(index, f"{index} lineend")

        if line_text.strip().startswith("-"):
            if line_text.strip() == "-":
                # Case: empty bullet line, exit bullet mode
                self.textbox.delete(index, f"{index} lineend")
                self.textbox.insert("insert", "\n")
                return "break"
            else:
                # Continue bullet list
                self.textbox.insert("insert", "\n- ")
                return "break"

        # default: allow normal Enter
        return

    def add_note(self):
        """Create a new note, saving current note first
        freemium model
        when user hits 10 notes, that's it. Nudge to pay once
        then lock button
        """
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
        self.__freemium_note_count_feature()

    def check_updates(self):
        """Check for updates from DOWNLOAD link"""
        if has_internet():
            # check for the updates
            pass


def main():
    ctk.set_appearance_mode("dark")
    app = NotesApp()
    app.iconbitmap(APP_ICON)
    app.mainloop()

# When users notes reach 10
# nudge for owning the app


if __name__ == "__main__":
    # THIS IS THE MAIN ENTRY POINT OF THE ENTIRE PROJECT
    main()
