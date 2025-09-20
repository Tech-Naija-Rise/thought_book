"""This is a script that allows the user to send
feedback or feature requests to the developer

The feedback window will be launched from the settings class



This is a subapp that will be installed together with every BM
app so that the process of feedback collection is easier


"""

import urllib.parse
import json
import os
import threading
import pathlib
import time
import customtkinter as ctk

from .constants import logging, fb_path, tkmsg
from .utils import has_internet, create_fb_tb


class FeedbackAPI(ctk.CTk):
    def __init__(self) -> None:
        """Collect feedback from offline and when the user
        gets online, then just send it to the developer through
        email.

        But inform the user that you will be checking when they
        get online so that the feedback can be sent.
        """
        super().__init__()
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
            self.credentials_frame, placeholder_text="Your Full Name")
        self.name_entry.pack(expand=1, fill="x")

        self.email_entry = ctk.CTkEntry(
            self.credentials_frame,
            placeholder_text="your email (to receive updates)")
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

        threading.Thread(name="Background internet check",
                         target=self.check_periodically,
                         daemon=True).start()

    def parse_feedbacks(self):
        """Go through the file and give back a long string
        with all the feedbacks"""
        parsed = ""
        if os.path.exists(fb_path):
            with open(fb_path) as r:
                obj = json.load(r)
            for fb in obj:
                name = fb["name"]
                email = fb["email"]
                body = fb["body"]

                title = rf"BMTb User Feedback from {name}"
                body = f"{body}\n\n\nSend the updates to user's email after addressing issue: "

                final_link = f"&to={self.b_email_addr}"
                f"&su={urllib.parse.quote(title)}"
                f"&body={urllib.parse.quote(body)}{email}{urllib.parse.quote("\n")}"
                
                parsed += final_link

        print(parsed)
        return parsed

    def start(self):
        self.mainloop()

    def _validate(self):
        self.user_name = self.name_entry.get()
        self.email_name = self.email_entry.get()
        self.body = self.textbox.get("1.0", "end")

        # The name is required
        if self.name_entry.get().strip():
            # print(self.user_name.strip())
            return True
        else:
            return False

    def save_or_send(self):
        """Save this feedback locally for sending later
        or send it right now through email.
        """

        if has_internet():
            # if i have internet, then do this through gmail directly.
            if self._validate():
                self.open_gmail(self.user_name,
                                self.email_name,
                                self.body)
        else:
            # locally store feedback
            logging.error("No connection, will save feedback locally.")

            if self._validate():
                self.save_locally(self.user_name, self.email_name, self.body)
                tkmsg.showinfo(
                    "Feedback will be saved for later",
                    "Offline? No problem. We've saved "
                    "your feedback and will send it when "
                    "you are online.")

                self.destroy()
                logging.info("Feedback area destroyed")
            else:
                tkmsg.showerror("Name required",
                                "Your name and feeback are required")
                logging.info("Empty fields.")

    def save_locally(self, name, email, body):
        fb_path_ = pathlib.Path(fb_path)
        obj = {"name": name, "email": email, "body": body}
        create_fb_tb()
        
        logging.info(f"Saved feedback into '{fb_path_.name}'")
        # tkmsg.showinfo("Saved for later", "We have saved your feedback.")

    def _web(self, LINK):
        import webbrowser as wb
        wb.open_new_tab(LINK)

    def open_gmail(self, name="", email="", body="", all_=""):
        """`all_` is for when we take from the saved fb file have a long
        string containing all users feedback"""
        LINK = "https://mail.google.com/mail/?view=cm&fs=1"
        import urllib.parse
        if (name and body) or (name and body and email):
            title = rf"BMTb User Feedback from {name}"
            body = f"{body}\n\n\nSend the updates to user's email after addressing issue: "
            LINK = (
                LINK+f"&to={self.b_email_addr}"
                f"&su={urllib.parse.quote(title)}"
                f"&body={urllib.parse.quote(body)}{email}"
            )
            threading.Thread(target=self._web, args=(LINK,)).start()
        elif (all_):
            LINK = LINK + f"{all_}{email}"

    def check_periodically(self):
        logging.info("Starting internet check background process")
        while True:
            # check if the feedbacks are there.
            # check if internet is there
            # send
            if os.path.exists(fb_path) and has_internet():
                self.open_gmail(all_=self.parse_feedbacks())
                logging.info("Sending feedbacks...")
                logging.info("Sent feedbacks - maybe")
            else:
                logging.error(
                    "Either there was no internet,"
                    " or there's no feedback yet")

            time.sleep(60*2)


if __name__ == "__main__":
    FeedbackAPI().start()
