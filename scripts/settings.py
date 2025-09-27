import tkinter.messagebox as tkmsg
import customtkinter as ctk
import os
from scripts.constants import (
    PASS_FILE,
    APP_ICON,
    SETTINGS_FILE,

)
from scripts.utils import (
    askstring, clear_all_notes)
from scripts.feedback_collection import FeedbackAPI



import json

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {"request_password": False}
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)




class SettingsWindow(ctk.CTkToplevel):
    """Settings GUI window for NotesApp."""

    def __init__(self, parent, cipher):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("300x350")
        self.wm_iconbitmap(APP_ICON)
        # add a scrollable
        self.resizable(False, True)
        self.transient(parent)   # Tie dialog to parent (only on top of it)

        self.cipher = cipher
        self.parent = parent

        # Change password section
        ctk.CTkLabel(self, text="Change Password").pack(pady=(20, 5))
        self.change_pass_btn = ctk.CTkButton(
            self, text="Change Password", command=self.change_password)
        self.change_pass_btn.pack(pady=5)

        # Startup lock option
        ctk.CTkLabel(self, text="Security").pack(pady=(20, 5))
        settings = load_settings()
        self.startup_lock_var = ctk.BooleanVar(value=settings.get("request_password", False))
        self.settings = settings

        self.startup_lock_switch = ctk.CTkSwitch(
            self,
            text="Request password at startup",
            variable=self.startup_lock_var,
            command=self.toggle_startup_lock,
        )
        self.startup_lock_switch.pack(pady=5)




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

        # Feedback area
        ctk.CTkLabel(self, text="Feedback and Help").pack(pady=(20, 5))
        self.feedback_btn = ctk.CTkButton(
            self, text="Give feedback", command=self.feedback_collect)
        self.feedback_btn.pack(pady=5)

    def toggle_startup_lock(self):
        """Turn on/off password request at startup (tracked in settings.json)."""
        if self.startup_lock_var.get():
            # Switch turned ON → immediately set password
            new_pass = askstring("Set Password", "Enter a new password:", show="*")
            if not new_pass:
                tkmsg.showinfo("Info", "Password setup cancelled.")
                self.startup_lock_var.set(False)
                return

            recovery = askstring("Recovery Code", "Enter a recovery code (save it safely):", show="*")
            if not recovery:
                tkmsg.showinfo("Info", "Recovery setup cancelled.")
                self.startup_lock_var.set(False)
                return

            with open(PASS_FILE, "w") as f:
                f.write(self.cipher.pass_hash(new_pass) + "\n")
                f.write(self.cipher.pass_hash(recovery))

            self.settings["request_password"] = True
            save_settings(self.settings)
            tkmsg.showinfo("Info", "Password protection enabled.")

        else:
            # Switch turned OFF → keep password file but ignore it
            self.settings["request_password"] = False
            save_settings(self.settings)
            tkmsg.showinfo("Info", "Password request at startup disabled.")



    def feedback_collect(self, event=None):
        self.feedbackAPI = FeedbackAPI(self)
        # i am settings window, this is my brother
        self.feedbackAPI.start()

    def confirm_clear_all(self):
        dialog = ctk.CTkInputDialog(
            text="Type 'YES' to delete ALL notes permanently:",
            title="Confirm Clear All",

        )

        # Set icon for the dialog window
        try:
            dialog.winfo_toplevel().iconbitmap(APP_ICON)
            # or, if you prefer using wm_iconphoto:
            # from PIL import Image, ImageTk
            # icon_image = ImageTk.PhotoImage(file=r"C:\path\to\logo.png")
            # dialog._top.wm_iconphoto(True, icon_image)
        except Exception as e:
            print("Failed to set icon:", e)

        answer = dialog.get_input()
        if answer and answer.strip().upper() == "YES":
            clear_all_notes()
            self.parent.notes.clear()
            self.parent.refresh_list()
            self.parent.title_entry.delete(0, "end")
            self.parent.textbox.delete("1.0", "end")
            self.parent.current_index = None
            tkmsg.showinfo("Success", "All notes deleted successfully!")

    def verify_current_password(self):
        """Ask user to enter current password for verification.
        But allow for him to enter his recovery code to make it
        easier
        """
        if not os.path.exists(PASS_FILE):
            tkmsg.showerror("Error", "No password set yet.")
            return False

        entered = askstring(
            "Verify Password", "Enter current password (or recovery code):", show="*")
        if entered is None:
            return False

        with open(PASS_FILE, "r") as f:
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

        with open(PASS_FILE, "w") as f:
            f.write(self.cipher.pass_hash(new_pass))
        tkmsg.showinfo("Info", "Password changed successfully.")
