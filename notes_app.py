from datetime import datetime
import os
import sys
import re
import logging
import threading
import time
import webbrowser
from tkinter import messagebox as tkmsg
from tkinter.messagebox import askyesno

import customtkinter as ctk
import requests

from scripts.constants import (
    EMAIL_ID_FILE,
    LICENSE_KEY_FILE,
    METRICS_FILE,
    METRICS_FILE_CONTENT,
    PASS_FILE,
    APP_NAME,
    APP_ICON,
    TNR_BMTB_SERVER,
    read_file,
    write_file,
    NOTES_DB
)
from scripts.bma_express import ActivitiesAPI
from scripts.utils import (
    SimpleCipher,
    create_table,
    askstring,
    get_notes,
    delete_note,
    save_note,
    set_recovery_key,
    verify_recovery_key,
    has_internet
)
from scripts.settings import SettingsWindow, load_settings
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import base64


class NotesApp(ctk.CTk):
    """Main Notes Application Class"""

    def __init__(self):
        """Initialize the NotesApp, load settings, password, freemium checks, and UI"""
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
        self.password_file = PASS_FILE
        self.password = None

        settings = load_settings()
        self.locked = settings.get("request_password", False)

        if self.locked:
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

    def validate_license(self, license_data, license_key):
        """Validate license using RSA public key"""
        with open("public_key.pem", "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())
        try:
            signature = base64.b64decode(license_key)
            public_key.verify(signature, license_data.encode(),
                              padding.PKCS1v15(), hashes.SHA256())
            tkmsg.showinfo("Success", "License verified successfully!")
            self.save_encrypted_locally(license_data)
        except Exception as e:
            tkmsg.showerror("Invalid License",
                            "License key does not match data!")
            logging.error(f"License verification failed: {e}")

    def __freemium_note_count_feature(self, locked=True):
        """Enforce freemium note count restriction"""
        if locked:
            info = METRICS_FILE_CONTENT
            try:
                count = int(info['note_count_limit'])
                urc = int(info['upgrade_reminder_count'])
                mur = int(info['max_upgrade_remind'])
            except KeyError as e:
                logging.error(f"Can't find keys: {e}")

            if self.get_note_count() >= count:
                if urc < mur:
                    ans = tkmsg.askyesnocancel(
                        "Free version limit reached",
                        "Your free note limit has been reached\nWould you like to upgrade now to have access to all features?"
                    )
                    info['upgrade_reminder_count'] += 1
                    write_file(METRICS_FILE, info)

                    if ans:
                        self.freemium_reg_flow()

                self.add_button.configure(
                    text="Upgrade to add more" if self.freemium_locked else "Add Note",
                    command=self.ask_license if self.freemium_locked else self.add_note
                )
            else:
                self.add_button.configure(
                    text="Add Note", command=self.add_note)
        else:
            self.add_button.configure(text="Add Note", command=self.add_note)

    def ask_license(self):
        """Prompt user for license or validate existing one"""
        if not os.path.exists(LICENSE_KEY_FILE):
            self.__show_license_window()
        else:
            try:
                with open(LICENSE_KEY_FILE, "r") as f:
                    encrypted_license = f.read()
                self.cipher.decrypt(encrypted_license)
                self.freemium_locked = False
                self.add_button.configure(
                    text="Add Note", command=self.add_note)
            except Exception as e:
                logging.error(f"Failed to read/validate license: {e}")
                tkmsg.showerror(
                    "Error", "Failed to validate license. Please re-enter.")
                os.remove(LICENSE_KEY_FILE)
                self.ask_license()

    def __show_license_window(self):
        """Display modal license entry window"""
        license_window = ctk.CTkToplevel(self)
        license_window.title(f"Activate {APP_NAME}")
        license_window.geometry("500x400")
        license_window.grab_set()
        license_window.resizable(False, True)

        instructions = ctk.CTkLabel(
            license_window,
            text=(f"Welcome to {APP_NAME}!\n\nPlease paste your license information below."
                  "\n1. License Data\n2. License Key\n\nIf you haven't "
                  "purchased a license yet, click"),
            justify="left",
            wraplength=460
        )
        instructions.pack(pady=(10, 0), padx=10, anchor="w")

        link_label = ctk.CTkLabel(
            license_window, text="here.", text_color="#4a90e2", cursor="hand2", justify="left"
        )
        link_label.pack(pady=(0, 10), padx=10, anchor="w")
        link_label.bind("<Button-1>", lambda e: self.freemium_reg_flow())

        license_data_label = ctk.CTkLabel(license_window, text="License Data:")
        license_data_label.pack(anchor="w", padx=20)
        license_data_entry = ctk.CTkTextbox(license_window, height=4)
        license_data_entry.pack(fill="x", padx=20, pady=(0, 10))

        license_key_label = ctk.CTkLabel(license_window, text="License Key:")
        license_key_label.pack(anchor="w", padx=20)
        license_key_entry = ctk.CTkTextbox(license_window, height=2)
        license_key_entry.pack(fill="x", padx=20, pady=(0, 10))

        submit_btn = ctk.CTkButton(
            license_window,
            text="Activate",
            command=lambda: self.__submit_license(
                license_data_entry, license_key_entry, license_window)
        )
        submit_btn.pack(pady=10)

        license_window.mainloop()

    def __submit_license(self, data_entry, key_entry, window):
        """Handle license submission"""
        license_data = data_entry.get("1.0", "end-1c").strip()
        license_key = key_entry.get("1.0", "end-1c").strip()

        if not license_data or not license_key:
            tkmsg.showerror(
                "Missing Data", "Both License Data and License Key are required.")
            return

        self.validate_license(license_data, license_key)
        window.destroy()

    def __ask_email(self):
        """Prompt user for email if not stored"""
        if not os.path.exists(EMAIL_ID_FILE):
            self.user_email = askstring(
                "Email Required", "Enter your email (required for payment receipt):")
            write_file(EMAIL_ID_FILE, {"user_email": self.user_email})
        else:
            self.user_email = read_file(EMAIL_ID_FILE)["user_email"]

    def freemium_reg_flow(self):
        """Start freemium registration/payment flow"""
        self.__ask_email()
        threading.Thread(target=self.__freemium_reg_flow, daemon=True).start()

    def __freemium_reg_flow(self):
        """Perform server payment initiation"""
        try:
            resp = requests.post(
                f"{TNR_BMTB_SERVER}/payment",
                json={"amount": 500, "email": self.user_email}, timeout=40)
            reference = str(resp.json()["data"]["reference"])
            logging.info(f"Payment initiated, reference: {reference}")
            webbrowser.open_new_tab(resp.json()['data']['authorization_url'])

        except Exception as e:
            logging.error(f"Error during payment processing: {e}")
            tkmsg.showerror("Error occured",
                            f"Failed to initiate payment. {e}")

    def save_encrypted_locally(self, license):
        """Encrypt and save license locally"""
        with open(LICENSE_KEY_FILE, "w") as f:
            f.write(self.cipher.encrypt(license))
        self.freemium_locked = False
        self.add_button.configure(text="Add Note", command=self.add_note)

    def get_note_count(self):
        """Return current number of notes"""
        return len(self.load_notes())

    def start_ui(self):
        """Initialize and layout the UI components"""
        if self.locked:
            return

        self.title(APP_NAME)
        self.geometry("800x500")
        self.wm_iconbitmap(APP_ICON)
        self.notes = self.load_notes()
        self.current_index = None

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        if not self.focused.get():
            self.sidebar.pack(side="left", fill="y")

        button_frame = ctk.CTkFrame(self.sidebar)
        button_frame.pack(pady=5, fill="x")

        self.add_button = ctk.CTkButton(
            button_frame, text="Add Note", fg_color="#555555", width=80, command=self.add_note)
        self.add_button.pack(side="left", pady=5, padx=2)

        self.delete_button = ctk.CTkButton(button_frame, text="Delete Note", fg_color="#555555",
                                           hover_color="darkred", text_color="white", command=self.delete_note, width=80)
        self.delete_button.pack(side="right", pady=5)

        self.scrollable_list = ctk.CTkScrollableFrame(self.sidebar, width=200)
        self.scrollable_list.pack(fill="both", expand=True)

        pair = ctk.CTkFrame(self.sidebar)
        pair.pack(fill="x")
        settings_btn = ctk.CTkButton(pair, fg_color="#555555", text="Settings",
                                     width=80, command=lambda: SettingsWindow(self, self.cipher))
        settings_btn.pack(side="left", pady=5)

        focus_btn = ctk.CTkButton(
            pair, fg_color="#555555", width=80, text="Focus", command=self.focus)
        focus_btn.pack(side="right")

        self.note_buttons = []
        self.refresh_list()

        # Editor
        self.right_side = ctk.CTkFrame(self, height=300)
        self.right_side.pack(side="right", fill="both", expand=True, padx=10)

        self.editor_frame = ctk.CTkFrame(self.right_side)
        self.editor_frame.pack(side="top", pady=10, expand=True, fill="both")

        self.title_entry = ctk.CTkEntry(
            self.editor_frame, placeholder_text="Title")
        self.title_entry.pack(fill="x", pady=5)

        self.textbox = ctk.CTkTextbox(
            self.editor_frame, undo=True, wrap=ctk.WORD)
        self.textbox.pack(fill="both", expand=True, pady=5)

        self.extra_bt_frame = ctk.CTkFrame(self.right_side)
        self.unfocus_btn = ctk.CTkButton(
            self.extra_bt_frame, text="Unfocus", width=80, command=self.focus, fg_color="#555555")

        self.title_entry.bind(
            "<KeyRelease>", lambda e: self.schedule_autosave())
        self.textbox.bind("<KeyRelease>", lambda e: self.schedule_autosave())
        self.title_entry.bind("<Return>", lambda e: self.textbox.focus_set())
        self.textbox.bind("<Return>", self.handle_multiline)

        self.wm_protocol("WM_DELETE_WINDOW", self.on_close)

        if not self.notes:
            self.add_note()
        else:
            self.load_note(0)

        self.bma = ActivitiesAPI()

    def focus(self):
        """Toggle focus mode: hides/shows sidebar and extra buttons."""
        is_focused = not self.focused.get()
        self.focused.set(is_focused)

        if is_focused:
            self.unfocus_btn.pack_forget()
            self.extra_bt_frame.pack_forget()
            self.sidebar.pack(side="left", fill="y")
        else:
            self.extra_bt_frame.pack(fill="x", pady=5, side="bottom")
            self.unfocus_btn.pack(side="left")
            self.sidebar.pack_forget()

    def on_close(self):
        """Handle app close event, process POAs and destroy window."""
        try:
            _, current_content = self.get_current_note()
            poas = self.get_poas(current_content)
            self.bma.make_activities(poas)
        except Exception as e:
            logging.error(f"Error during app close: {e}")
        finally:
            logging.info("App closed successfully.")
            self.destroy()

    def get_current_note(self, index_to_save=None):
        """Return the current note index and content (unencrypted)."""
        idx = index_to_save if index_to_save is not None else self.current_index
        content = self.textbox.get("1.0", "end-1c").strip()
        return idx, content

    def get_poas(self, current_note):
        """Extract all POA items (marked by []) from the note."""
        if current_note.strip():
            poas = re.findall(r"\[\s?\] ?[^\.\n]+", current_note)
            poas = [re.sub(r"\[\s?\]\s?", "", x) for x in poas]
            logging.info(f"Found {len(poas)} POA(s)")
            return poas
        return []

    def _corpus_manager(self, _all_notes):
        """Experimental: manage corpus for AI training when word threshold is met."""
        word_count, content = _all_notes
        corpus_file = f"corpus_{datetime.now().date()}.txt"
        try:
            threshold_met = (_all_notes[0] > self.max_words_b4_training and
                             0 <= (_all_notes[0] % self.max_words_b4_training) <= 500)
            if threshold_met:
                if askyesno("Fine-tune ready", f"You've written approximately {word_count} new words. Save all notes as corpus?"):
                    with open(corpus_file, "w") as f:
                        f.write(content)
                    logging.info(
                        f"Corpus saved at {os.path.abspath(corpus_file)}")
        except Exception as e:
            logging.error(f"Failed to start corpus management: {e}")

    def schedule_autosave(self):
        """Schedule an autosave after a short delay to reduce excessive writes."""
        if self.autosave_after_id:
            self.after_cancel(self.autosave_after_id)
        self.autosave_after_id = self.after(500, self.save_current_note)

    def load_notes(self) -> list:
        """Load all notes from the database."""
        return get_notes()

    def refresh_list(self):
        """Refresh the sidebar list of notes and update buttons."""
        for btn in self.note_buttons:
            btn.destroy()
        self.note_buttons.clear()

        for idx, note in enumerate(self.notes):
            display_title = self.truncate_text(
                note.get("title", "Untitled"), 20)
            btn = ctk.CTkButton(
                self.scrollable_list, fg_color="#333333", text=display_title, width=180,
                command=lambda i=idx: self.load_note(i))
            btn.pack(pady=2)
            self.note_buttons.append(btn)

    def truncate_text(self, text, max_length=20):
        """Truncate a string to fit within max_length for display in buttons."""
        return text if len(text) <= max_length else text[:max_length - 3] + "..."

    def load_note(self, index):
        """Load note by index, saving current note first."""
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
        """Delete the current note after confirmation."""
        if self.current_index is None:
            return

        if tkmsg.askyesno("Confirm Delete", "Are you sure you want to delete this note?"):
            note_id = self.notes[self.current_index].get("id")
            if note_id:
                delete_note(note_id)
                del self.notes[self.current_index]

            self.title_entry.delete(0, "end")
            self.textbox.delete("1.0", "end")
            self.current_index = None

            self.refresh_list()
            self.__freemium_note_count_feature()

    def forgot_password(self):
        """Handle password recovery via recovery code input."""
        code = askstring(
            "Recovery",
            "Enter recovery code:\n\nWrite this recovery code down in a safe place.\nLosing it means you cannot reset your password.",
            show="*")

        if code is None:
            return False
        if code.lower() == "exit":
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
        """Prompt user for password and validate or trigger recovery."""
        try:
            with open(self.password_file, 'r') as f:
                stored_hash = f.readline().strip()

            entered = askstring(
                "Password", "Enter password (or leave blank to reset):", show="*")
            if entered is None:
                return "Cancelled"
            if entered.lower() == "exit":
                return "exit"
            if entered == "":
                return self.forgot_password()

            if self.cipher.pass_hash(entered) == stored_hash:
                return True
            else:
                tkmsg.showerror("Error", "Incorrect password.")
                return False

        except FileNotFoundError:
            # First-time setup
            new_pass = askstring("Password", "Create password:", show="*")
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
        """Save the current note or a specified note index to the database."""
        idx, content = self.get_current_note(index_to_save)
        content_encrypted = self.encrypt(content)
        title = self.title_entry.get()

        if idx is not None:
            note_id = self.notes[idx].get("id")
            if note_id:
                save_note(title, content_encrypted, note_id)
                self.notes[idx] = {"id": note_id,
                                   "title": title, "content": content_encrypted}
            else:
                new_id = save_note(title, content_encrypted)
                self.notes[idx] = {"id": new_id,
                                   "title": title, "content": content_encrypted}
        else:
            new_id = save_note(title, content_encrypted)
            self.notes.append({"id": new_id, "title": title,
                              "content": content_encrypted})
            self.current_index = len(self.notes) - 1

        self.refresh_list()

    def handle_multiline(self, event=None):
        """Handle multiline bullet input when Enter key is pressed."""
        index = self.textbox.index("insert linestart")
        line_text = self.textbox.get(index, f"{index} lineend")

        if line_text.strip().startswith("-"):
            if line_text.strip() == "-":
                # Empty bullet line, exit bullet mode
                self.textbox.delete(index, f"{index} lineend")
                self.textbox.insert("insert", "\n")
                return "break"
            else:
                self.textbox.insert("insert", "\n- ")
                return "break"

        return None

    def add_note(self):
        """Create a new note, save current, and enforce freemium limits."""
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
        """Check for updates online if internet is available."""
        if has_internet():
            # Implement update check logic here
            pass


def main():
    ctk.set_appearance_mode("dark")
    app = NotesApp()
    app.iconbitmap(APP_ICON)
    app.mainloop()


if __name__ == "__main__":
    main()
