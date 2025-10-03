# license_manager.py

# For license management
import threading
import webbrowser
import customtkinter as ctk
import tkinter.messagebox as tkmsg
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import base64

import requests

from scripts.constants import (EMAIL_ID_FILE, LICENSE_KEY_FILE,
                               TNR_BMTB_SERVER, read_file, logging,
                               APP_ICON, APP_NAME, write_file)
from scripts.utils import askstring


class LicenseManager:
    def __init__(self, master) -> None:
        """Managing all license related things. 
        This classed is called in the Notes app.

        To avoid circular imports, we pass the main
        notes app class here in the form of

        LicenseManager(`self`) where `self` is NotesApp class
        """
        self.master = master

        self.cipher = self.master.cipher

        self.unlocked_feature_id = ""

    def unlock_feature(self, feature_id, associated_button):
        if "unlimited_notes" in feature_id:
            associated_button.configure(
                text="Add Note", command=self.master.add_note)
            
    def check_license(self):
        """Return True if a valid license exists locally."""
        if not os.path.exists(LICENSE_KEY_FILE):
            return False
        try:
            encrypted_license = read_file(LICENSE_KEY_FILE)
            license_data = self.cipher.decrypt(encrypted_license)
            print(license_data)
            # Optional: validate license_data format
            return True
        except Exception as e:
            logging.error(f"License check failed: {e}")
            return False

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
                self.master.add_button.configure(
                    text="Add Note", command=self.master.add_note)
            except Exception as e:
                logging.error(f"Failed to read/validate license: {e}")
                tkmsg.showerror(
                    "Error", "Failed to validate license. Please re-enter.")

    def __show_license_window(self):
        """Display modal license entry window"""
        self.license_window = ctk.CTkToplevel(self)
        self.license_window.title(f"Activate {APP_NAME}")
        self.license_window.geometry("500x400")
        self.license_window.iconbitmap(APP_ICON)
        self.license_window.grab_set()
        self.license_window.resizable(False, True)

        instructions = ctk.CTkLabel(
            self.license_window,
            text=(f"Welcome to {APP_NAME}!\n\nPlease paste your license information below."
                  "\n1. License Data\n2. License Key\n\nIf you haven't "
                  "purchased a license yet, click"),
            justify="left",
            wraplength=460
        )
        instructions.pack(pady=(10, 0), padx=10, anchor="w")

        link_label = ctk.CTkLabel(
            self.license_window, text="here.", text_color="#4a90e2", cursor="hand2", justify="left"
        )
        link_label.pack(pady=(0, 10), padx=10, anchor="w")
        link_label.bind("<Button-1>", lambda e: self.freemium_reg_flow())

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

        self.license_window.mainloop()

    def __submit_license(self, data_entry, key_entry):
        """Handle license submission"""
        license_data = data_entry.get("1.0", "end-1c").strip()
        license_key = key_entry.get("1.0", "end-1c").strip()

        if not license_data or not license_key:
            tkmsg.showerror(
                "Missing Data", "Both License Data and License Key are required.")
            return

        self.validate_license(license_data, license_key)
        self.license_window.destroy()

    def validate_license(self, license_data, license_key):
        """Validate license using RSA public key"""
        with open("public_key.pem", "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())
        try:
            signature = base64.b64decode(license_key)
            public_key.verify(signature, license_data.encode(),  # type: ignore
                              padding.PKCS1v15(), hashes.SHA256())  # type: ignore
            tkmsg.showinfo("Success", "License verified successfully!")
            self.save_encrypted_locally(license_data)
            # Centralized unlock after successful activation
            if hasattr(self.master, "unlock_feature_checks"):
                self.master.unlock_feature_checks("unlimited_notes")
        except Exception as e:
            tkmsg.showerror("Invalid License",
                            "License key does not match data!")
            logging.error(f"License verification failed: {e}")

    def __ask_email(self):
        """Prompt user for email if not stored"""
        if not os.path.exists(EMAIL_ID_FILE):
            self.user_email = askstring(
                "Email Required", "Enter your email (required for payment receipt):")
            write_file(EMAIL_ID_FILE, {"user_email": self.user_email})
        else:
            self.user_email = read_file(EMAIL_ID_FILE)["user_email"]

    def __freemium_reg_flow(self):
        """Perform server payment initiation"""
        try:
            resp = requests.post(
                f"{TNR_BMTB_SERVER}/payment",
                json={"amount": 500, "email": self.user_email})
            reference = str(resp.json()["data"]["reference"])
            logging.info(f"Payment initiated, reference: {reference}")
            webbrowser.open_new_tab(resp.json()['data']['authorization_url'])

        except Exception as e:
            logging.error(f"Error during payment processing: {e}")
            tkmsg.showerror("Error occured",
                            f"Failed to initiate payment."
                            f"\nMight be a connection problem. \n{e}")

    def freemium_reg_flow(self):
        """Start freemium registration/payment flow"""
        self.__ask_email()
        threading.Thread(target=self.__freemium_reg_flow, daemon=True).start()

    def save_encrypted_locally(self, license):
        """Encrypt and save license locally"""
        with open(LICENSE_KEY_FILE, "w") as f:
            f.write(self.cipher.encrypt(license))

        self.master.add_button.configure(
            text="Add Note", command=self.master.add_note)
