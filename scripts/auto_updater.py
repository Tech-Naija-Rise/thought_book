import requests
import os
import sys
import subprocess
import threading

from packaging import version

import customtkinter as ctk
from tkinter import messagebox

from .constants import (logging, APP_VERSION,
                        APP_NAME, APP_SHORT_NAME,
                        UPDATE_DOWNLOAD_FOLDER)

UPDATE_INFO_URL = "https://tech-naija-rise.github.io/thought_book/update.json"


class AutoUpdater:
    def __init__(self, parent, auto_install=False):
        self.parent = parent
        self.auto_install = auto_install
        os.makedirs(UPDATE_DOWNLOAD_FOLDER, exist_ok=True)

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
            logging.info(f"Latest Version found: {latest_version}")

            if version.parse(latest_version) > version.parse(APP_VERSION):
                logging.info(f"Latest Version found: {latest_version}")
                if self.auto_install:
                    self.download_and_install(url)
                else:
                    self.prompt_update(latest_version, notes, url)
        except Exception as e:
            # Silent fail for background updates
            logging.error(f"Update check failed: {e}")

    def prompt_update(self, latest_version, notes, url):
        """Ask user for update, non-blocking."""
        msg = f"{APP_NAME} v{latest_version} is available.\nDo you want to update now?"
        if messagebox.askyesno(f"{APP_SHORT_NAME} Update", msg):
            self.download_and_install(url)

    def download_and_install(self, url, show_progress=False):
        """Download installer with optional progress hook."""
        filename = os.path.join(UPDATE_DOWNLOAD_FOLDER, url.split("/")[-1])
        try:
            r = requests.get(url, stream=True)
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0

            if show_progress:
                # Create a top-level window for progress
                progress_window = ctk.CTkToplevel(self.parent)
                progress_window.title("Downloading Update")
                progress_window.geometry("400x100")
                progress_label = ctk.CTkLabel(
                    progress_window, text="Downloading...")
                progress_label.pack(pady=10)
                progress_bar = ctk.CTkProgressBar(progress_window, width=350)
                progress_bar.set(0)
                progress_bar.pack(pady=10)

            with open(filename, 'wb') as f:
                logging.info("Downloading update")
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if show_progress:
                            # Update progress bar
                            progress_bar.set(downloaded / total_size)
                            progress_window.update()  # refresh GUI

            if show_progress:
                progress_window.destroy()  # close progress window

            # Run installer
            logging.info(f"Finished installation {filename}")
            subprocess.Popen([filename], shell=True)
            self.parent.destroy()  # Close app to allow installer
        except Exception as e:
            logging.error(f"Update failed: {e}")
            messagebox.showerror(
                f"{APP_SHORT_NAME} Update", f"Update failed:\n{e}")
