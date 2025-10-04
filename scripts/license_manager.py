# license_manager.py

# For license management
import json
import threading
import webbrowser
import customtkinter as ctk
import tkinter.messagebox as tkmsg
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import base64

import requests

from scripts.constants import (EMAIL_ID_FILE, LICENSE_FILE,
                               TNR_BMTB_SERVER,  logging,
                               APP_ICON, APP_NAME, read_json_file, read_txt_file,
                               PUBLIC_KEY, write_json_file, write_txt_file)
from scripts.utils import askstring, center_window


class LicenseManager:
    def __init__(self, master) -> None:
        """Managing all license related things. 
        This classed is called in the Notes app.
        """
        self.master = master
        self.cipher = self.master.cipher
        self.license_file = LICENSE_FILE
        self.public_key = PUBLIC_KEY
        self.is_premium = False
        self.license_data = None
        self.license_key = None

        self.load_and_validate_license()

    def load_and_validate_license(self):
        if not os.path.exists(self.license_file):
            self.is_premium = False
            return False

        data = read_json_file(self.license_file)
        self.license_data, self.license_key = self.parse_license(data)

        if self.verify_signature(self.license_data, self.license_key):
            self.is_premium = True
            return True
        else:
            self.is_premium = False
            os.remove(self.license_file)  # 🚨 remove tampered/invalid license
            return False

    def activate_license(self, license_data, license_key):
        """Called when user enters key only"""
        if self.verify_signature(license_data, license_key):
            self.license_data = license_data
            self.license_key = license_key
            self.is_premium = True
            write_json_file(self.license_file, self.format_license(
                license_data, license_key))
            logging.info("Saved license to file.")
            tkmsg.showinfo(
                "Success", "License activated successfully! "
                "You are now a premium user.")
            return True
        else:
            self.is_premium = False
            tkmsg.showerror("License Error",
                            "Invalid license. Please try again.")
            return False

    def is_premium_user(self):
        return self.is_premium

    def verify_signature(self, license_data, license_key):
        """This is a silent function 
        as opposed to  `activate_license(...)`"""
        try:
            public_key = serialization.load_pem_public_key(
                self.public_key.encode())

            # Encode and hash the license data
            license_bytes = license_data.encode()
            signature = base64.b64decode(license_key)

            public_key.verify(  # type: ignore
                signature,
                license_bytes,
                padding.PKCS1v15(),  # type: ignore
                hashes.SHA256()  # type: ignore
            )
            logging.info("License verified successfully.")
            self.is_premium = True
            return True
        except Exception as e:
            logging.error(f"License verification failed: {e}")
            self.is_premium = False
            return False

    # Formatting
    def format_license(self, license_data, license_key):
        return {
            "license_data": license_data,
            "license_key": license_key
        }

    def parse_license(self, data):
        """TODO: decrypt data"""
        license_dict = data if isinstance(data, dict) else json.loads(data)
        return license_dict["license_data"], license_dict["license_key"]

    def _show_license_window(self, master):
        """Display modal license entry window"""
        self.license_window = ctk.CTkToplevel(master)
        self.license_window.title(f"Activate {APP_NAME}")
        self.license_window.geometry("500x510")
        try:
            self.license_window.grab_set()
        except Exception:
            pass
        self.license_window.resizable(False, True)
        self.license_window.iconbitmap(APP_ICON)
        center_window(self.license_window, offsety=-150)

        instructions = ctk.CTkLabel(
            self.license_window,
            text=(
                f"Welcome to {APP_NAME}!\n\n"
                "You are currently using the free version.\n\n"
                "Unlock the full version to enjoy:\n"
                "• Premium features\n"
                "• A smoother, distraction-free experience\n\n"
                "To activate, please paste:\n"
                "1. Your License Data\n"
                "2. Your License Key\n\n"
                "If you don’t have a license yet, click below to purchase one."
            ),
            justify="left",
            wraplength=480
        )

        instructions.pack(pady=(10, 0), padx=10, anchor="w")

        link_label = ctk.CTkLabel(
            self.license_window, text="purchase license",
            text_color="#5f9de4",
            cursor="hand2", justify="left"
        )
        link_label.pack(pady=(0, 10), padx=10, anchor="w")
        link_label.bind("<Button-1>", lambda e: threading.Thread(
            target=self.initiate_payment, daemon=True).start())

        license_data_label = ctk.CTkLabel(
            self.license_window, text="License Data:")
        license_data_label.pack(anchor="w", padx=20)
        license_data_entry = ctk.CTkTextbox(self.license_window, height=4)
        license_data_entry.pack(fill="x", padx=20, pady=(0, 10))

        license_key_label = ctk.CTkLabel(
            self.license_window, text="License Key:")
        license_key_label.pack(anchor="w", padx=20)
        license_key_entry = ctk.CTkTextbox(self.license_window, height=2)
        license_key_entry.pack(fill="x", padx=20, pady=(0, 10))

        submit_btn = ctk.CTkButton(
            self.license_window,
            text="Activate",
            command=lambda: self.__submit_license(
                license_data_entry, license_key_entry)
        )
        submit_btn.pack(pady=10)
        # something to tell the user that it is
        # loading just as we did in feedback
        # system.
        self.status = ctk.CTkLabel(
            self.license_window, text="",
            text_color="#f5ca3f")
        self.status.pack(anchor="w", padx=20)

        self.license_window.wait_window()

    def __ask_email(self):
        """Prompt user for email if not stored"""
        if not os.path.exists(EMAIL_ID_FILE):
            self.user_email = askstring(
                "Email Required", "Enter your email (required for payment receipt):")
            write_json_file(EMAIL_ID_FILE, {"user_email": self.user_email})
        else:
            self.user_email = read_json_file(EMAIL_ID_FILE)["user_email"]

    def __initiate_payment(self):
        """Perform server payment initiation"""
        try:
            resp = requests.post(
                f"{TNR_BMTB_SERVER}/payment",
                json={"amount": 5000, "email": self.user_email})

            reference = str(resp.json()["data"]["reference"])

            logging.info(f"Payment initiated, reference: {reference}")
            webbrowser.open_new_tab(resp.json()['data']['authorization_url'])
        except Exception as e:
            logging.error(f"Error during payment processing: {e}")
            tkmsg.showerror("Error occured",
                            f"Failed to initiate payment."
                            f"\nMight be a connection problem. \n")

    def _update_status(self, msg):
        self.status.configure(text=msg)
        self.license_window.update_idletasks()

    def initiate_payment(self):
        """Start freemium registration/payment flow"""
        self.__ask_email()
        self._update_status("Opening payment link, please wait...")
        threading.Thread(target=self.__initiate_payment, daemon=True).start()

    def __submit_license(self, data_entry, key_entry):
        """Handle license submission"""
        self._update_status("Verifying license, please wait...")

        license_data = data_entry.get("1.0", "end-1c").strip()
        license_key = key_entry.get("1.0", "end-1c").strip()

        if not license_data or not license_key:
            tkmsg.showerror(
                "Missing Data", "Both License Data and License Key are required.")
            return

        # self.verify_signature(license_data, license_key)
        self.activate_license(license_data, license_key)
        self.license_window.destroy()


"""

[x] App begins.

[] Look for license.json in your app’s data directory.

If file not found → set is_premium = False.

If file found → open it and parse JSON.

Extract license_data and license_key.

Run verify_signature(license_data, license_key) with your embedded public key.

If valid → set is_premium = True.

If invalid → delete license.json, set is_premium = False.


"""
