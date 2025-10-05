import requests
import os
import sys
import subprocess
import threading

from packaging import version

import customtkinter as ctk
from tkinter import messagebox

from .constants import (logging, APP_VERSION,
                        APP_NAME, APP_SHORT_NAME)

UPDATE_INFO_URL = "https://tech-naija-rise.github.io/thought_book/update.json"
DOWNLOAD_FOLDER = os.path.join(
    os.path.expanduser("~"), f"{APP_SHORT_NAME}_updates")


class AutoUpdater:
    def __init__(self, parent, auto_install=False):
        self.parent = parent
        self.auto_install = auto_install
        os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

    def check_update_background(self):
        """Run version check in background thread."""
        threading.Thread(target=self._check, daemon=True).start()

    def _check(self):
        try:
            resp = requests.get(UPDATE_INFO_URL, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            latest_version = data['latest_version']
            url = data['url']
            notes = data.get('notes', "")

            if version.parse(latest_version) > version.parse(APP_VERSION):
                if self.auto_install:
                    self.download_and_install(url)
                else:
                    self.prompt_update(latest_version, notes, url)
        except Exception as e:
            # Silent fail for background updates
            logging.error("Update check failed:", e)

    def prompt_update(self, latest_version, notes, url):
        """Ask user for update, non-blocking."""
        msg = f"New version {latest_version} is available.\n\nChanges:\n{notes}\n\nDo you want to update?"
        if messagebox.askyesno(f"{APP_SHORT_NAME} Update", msg):
            self.download_and_install(url)

    def download_and_install(self, url):
        """Download installer with optional progress hook."""
        filename = os.path.join(DOWNLOAD_FOLDER, url.split("/")[-1])
        try:
            r = requests.get(url, stream=True)
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0

            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Optional: hook to update progress bar

            # Run installer
            subprocess.Popen([filename], shell=True)
            self.parent.destroy()  # Close app to allow installer
        except Exception as e:
            messagebox.showerror(
                f"{APP_SHORT_NAME} Update", f"Update failed:\n{e}")
