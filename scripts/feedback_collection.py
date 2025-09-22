"""This is a script that allows the user to send
feedback or feature requests to the developer

The feedback window will be launched from the settings class



This is a subapp that will be installed together with every BM
app so that the process of feedback collection is easier


"""

from datetime import datetime
import json
import os
import threading
import pathlib
import time
import customtkinter as ctk
import requests

from .constants import logging, fb_path, logs_file, tkmsg, app_name, BMTb_FEEDBACK_SERVER
from .utils import has_internet


class FeedbackAPI(ctk.CTkToplevel):
    def __init__(self, parent=None) -> None:
        """Collect feedback from offline and when the user
        gets online, then just send it to the developer through
        email.

        But inform the user that you will be checking when they
        get online so that the feedback can be sent.
        """
        self.parent = parent
        super().__init__(self.parent)
        self.transient(self.parent)
        self.title(f"BM - Give feedback")
        self.geometry("500x400")

        self.help = ctk.CTkLabel(
            self, text="Report Issues, suggest feedback, or provide general feedback here")
        self.help.pack()

        self.credentials_frame = ctk.CTkFrame(self)
        self.credentials_frame.pack(fill="x", expand=True)

        self.editor_frame = ctk.CTkFrame(self)
        self.editor_frame.pack(side="top",
                               pady=10, expand=True, fill="both")

        self.name_entry = ctk.CTkEntry(
            self.credentials_frame, placeholder_text="Your Full Name (Optional)")
        self.name_entry.pack(expand=1, fill="x")

        self.email_entry = ctk.CTkEntry(
            self.credentials_frame,
            placeholder_text="We need your email to notify you if we have a fix.")
        self.email_entry.pack(expand=1, fill="x")

        self.textbox = ctk.CTkTextbox(
            self.editor_frame, undo=True, wrap=ctk.WORD)
        self.textbox.pack(fill="both", expand=True, pady=5)

        self.actions_frame = ctk.CTkFrame(self)
        self.actions_frame.pack(fill="x", expand=True)

        self.send_btn = ctk.CTkButton(
            self.actions_frame, width=30, text="Send Feedback",
            command=self.save_or_send)
        self.send_btn.pack(side="right", padx=5)
        self.cancel_btn = ctk.CTkButton(self.actions_frame,
                                        width=30,
                                        text="Cancel",
                                        fg_color="#555555",
                                        command=self.destroy)
        self.cancel_btn.pack(side="right", padx=5)

        self.b_email_addr = "technaijarise@gmail.com"

        # Automatically check for internet in the background
        # and send feedback if there is any saved
        # otherwise, just end thread
        threading.Thread(name="Background internet check",
                         target=self.check_periodically,
                         daemon=True).start()

    def get_saved(self):
        """Return list of locally saved feedbacks."""
        if os.path.exists(fb_path):
            with open(fb_path, "r") as r:
                try:
                    return json.load(r)
                except json.JSONDecodeError:
                    return []
        return []

    def start(self):
        self.mainloop()

    def _validate(self):
        """Validate user input and return feedback data."""
        self.user_name = self.name_entry.get().strip()
        self.email_name = self.email_entry.get().strip()
        self.body = self.textbox.get("1.0", "end-1c").strip()

        self.data = {
            "app_name": app_name,
            "user_name": self.user_name,
            "follow_up": self.email_name,
            "user_feedback": self.body,
            "timestamp": datetime.now().strftime("%d-%m-%Y, %H:%M:%S"),
            "user_app_log": self.get_app_log()
        }

        if not self.body or not self.email_name:
            tkmsg.showerror("Fields required",
                            "Your email and feedback are required")
            logging.info("Validation failed: empty name or feedback")
            return self.data, False

        return self.data, True
    
    def get_app_log(self):
        """Return the last 100 lines of the app log file."""
        log_path = pathlib.Path(logs_file)
        if log_path.exists():
            try:
                with open(log_path, "r") as log_file:
                    lines = log_file.readlines()
                    return "".join(lines[-5:])  # Return last 5 lines
            except Exception as e:
                logging.error(f"Error reading log file: {e}")
                return "Could not read log file."
        return "Log file does not exist."
    
    def send_feedback(self, data={}, url=BMTb_FEEDBACK_SERVER):
        """This function is called from the GUI and
        as long as there is internet, it usually works well"""

        if not data:
            self.data = self._validate()[0]
        else:
            self.data = data

        r = requests.post(
            url, json=self.data, timeout=3)
        if r.json().get("status") == "feedback_received":
            logging.info("Feedback sent to server!")
            return True
        else:
            logging.error(
                "Feedback not sent or server returned error check logs of server")
            return False
        
    def save_or_send(self):
        threading.Thread(
            target=self._save_or_send,
            name="Feedback save or send",
            daemon=True).start()
        
    def _save_or_send(self):
        """Save this feedback locally for sending later
        or send it right now through email.
        """
        if self._validate()[1]:  # type: ignore
            if has_internet():
                # if i have internet, then do this through gmail directly.
                self.send_feedback()
                tkmsg.showinfo("Feedback sent",
                               "Thank you for your feedback!")
                self.destroy()
            else:
                # locally store feedback because offline
                logging.error("No connection, will save feedback locally.")
                self.save_locally()
                tkmsg.showinfo(
            "Feedback will be saved for later",
            "You are offline now. We've saved "
            "your feedback and will send it when "
            "you are online.")
                self.destroy()

    def save_locally(self, data={}):
        """Append the latest feedback to the end of 
        the list then save it in a json

        Best way is to read the contents, then append and rewrite
        """
        if not data:
            self.data = self._validate()[0]
        else:
            self.data = data

        fb_path_ = pathlib.Path(fb_path)

        # Read existing feedbacks
        try:
            with open(fb_path_, "r") as r:
                saved_feedbacks = json.load(r)
                if not isinstance(saved_feedbacks, list):
                    saved_feedbacks = []
        except json.JSONDecodeError:
            saved_feedbacks = []

        # Append new feedback and save
        saved_feedbacks.append(self.data)
        with open(fb_path_, "w") as w:
            json.dump(saved_feedbacks, w)

        logging.info(f"Saved feedback into '{fb_path_.name}'")
        # tkmsg.showinfo("Saved for later", "We have saved your feedback.")

    def _web(self, LINK):
        import webbrowser as wb
        wb.open_new_tab(LINK)

    def clear_saved(self):
        """Clear the feedbacks.json file"""
        with open(fb_path, "w") as w:
            json.dump([], w)

    def check_periodically(self):
        logging.info("Starting internet check background process")
        while True:
            saved_feedbacks = self.get_saved()
            # XXX
            if saved_feedbacks and has_internet():
                logging.info(
                    f"Sending {len(saved_feedbacks)} saved feedback(s)...")
                for fb in saved_feedbacks:
                    if self.send_feedback(fb):
                        logging.info("Sent feedback successfully")
                    else:
                        logging.error(
                            "Failed to send feedback; will retry later")
                self.clear_saved()

            elif not saved_feedbacks:
                break
            time.sleep(60)  # check every 1 minute


if __name__ == "__main__":
    # FeedbackAPI().start()
    pass
