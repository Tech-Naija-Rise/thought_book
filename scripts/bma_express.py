# bma_express.py
import json
from pathlib import Path
import shutil
import tkinter.messagebox as tkmsg
import subprocess
import sys
import threading
import os
from .constants import BMA_DOWNLOAD_LINK, NOTES_FOLDER
import logging


class ActivitiesAPI:
    """First check if BMA is installed or not
    simple check could be.

    When a person exits, it does the check first
    """

    def _check_installed(self, path):
        return "installed" if os.path.exists(path) else "not installed"

    def __init__(self) -> None:
        self.poa_list = []
        self.BMA_FOLDER = Path(f"{os.getenv("BMA", "")}")

        # .exe typical path to BMA app
        self.BMA_PATH = self.BMA_FOLDER / "Activities.exe"
        self.status = self._check_installed(self.BMA_PATH)

        # TODO
        # Number of times not to remind
        # Before finally reminding
        # So it means we would not remind user
        # for every 10 (task filled) app closes
        # MAX_OPENS_BEFORE_REMINDER
        self.remind_interval = 100
        # TODO

        # Maximum number of times we remind the user
        # after which we wait for interval above
        # then reset the counter to 0 so he is reminded.
        # we can make that 100
        self.max_reminds = 2

    def make_activities(self, poa_list):
        """We are running in another thread because it freezes 
        before exiting which is undesirable.
        """
        self.reminded_info_path = Path(NOTES_FOLDER) / "reminded.info"

        if poa_list:
            if not self.reminded_info_path.exists():
                with open(self.reminded_info_path, "w", encoding="utf-8") as f:
                    json.dump({"bma_notify_count": 0}, f)

            with open(self.reminded_info_path, "r", encoding="utf-8") as f:
                reminded_info = json.load(f)

            if self.status == "not installed":
                # Remind every
                if reminded_info["bma_notify_count"] < self.max_reminds:
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
                        subprocess.Popen(
                            ["start", BMA_DOWNLOAD_LINK], shell=True)

                else:
                    logging.error(
                        "BMA is not installed and "
                        f"user has been reminded {self.max_reminds} times. "
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
                # cmd = f'{self.BMA_PATH} add "{actv}"'
                info = subprocess.run(
                    [f"{self.BMA_PATH}", "add", actv], capture_output=True, text=True)
                logging.info(
                    "I talked to BMA. He says: "
                    f"{info.stdout.strip()}"
                )
            except Exception as e:
                logging.error(f"{e}: {info.stderr}")


if __name__ == "__main__":
    pass
