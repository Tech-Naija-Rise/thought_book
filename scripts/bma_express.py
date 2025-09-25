# bma_express.py
import json
from pathlib import Path
import shutil
import tkinter.messagebox as tkmsg
import subprocess
import sys
import threading
import os
from .constants import LOGS_FILE, BMA_DOWNLOAD_LINK, NOTES_FOLDER
import logging


class ActivitiesAPI:
    """First check if BMA is installed or not
    simple check could be.

    When a person exits, it does the check first
    """

    def _check_installed(self):
        return "installed" if shutil.which("BMA.exe") else "not installed"


    def __init__(self) -> None:
        self.poa_list = []

    def make_activities(self, poa_list):
        """We are running in another thread because it freezes 
        before exiting which is undesirable.
        """
        self.status = self._check_installed()
        self.reminded_info_path = Path(NOTES_FOLDER) / "reminded.info"

        if not self.reminded_info_path.exists():
            with open(self.reminded_info_path, "w", encoding="utf-8") as f:
                json.dump({"bma_notify_count": 0}, f)

        with open(self.reminded_info_path, "r", encoding="utf-8") as f:
            reminded_info = json.load(f)

        if self.status == "not installed":
            if reminded_info["bma_notify_count"] < 3:
                answer = tkmsg.askyesno(
                    "Get the full experience",
                    "Looks like you’ve started creating tasks.\n\n"
                    "To complete the experience, please install "
                    "Bobsi Mo Activities (BMA).\n\n"
                    "Do you want to install it now?",
                )
                logging.info("BMA not installed, request install.")
                reminded_info["bma_notify_count"] += 1
                with open(self.reminded_info_path, "w", encoding="utf-8") as f:
                    json.dump(reminded_info, f)

                if answer:
                    subprocess.Popen(["start", BMA_DOWNLOAD_LINK], shell=True)

            else:
                logging.error(
                    "BMA is not installed and user has been reminded 3 times. "
                )

        elif self.status == "installed":
            if poa_list:
                threading.Thread(
                    target=self._make,
                    args=(poa_list,),
                    daemon=False,
                    name="BMA caller",
                ).start()

    def _make(self, poa_list):
        """Before executing, check if BMA is actually installed."""
        self.poa_list = poa_list

        for actv in self.poa_list:
            try:
                cmd = f'BMA.exe add "{actv}"'
                info=subprocess.run(["BMA.exe", "add", actv], capture_output=True, text=True)
                logging.info(
                    "I talked to BMA. He says: "
                    f"{info.stdout.strip()}"
                )
            except Exception as e:
                logging.error(f"{e}: {cmd}")

if __name__ == "__main__":
    pass
