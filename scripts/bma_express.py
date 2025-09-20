import tkinter.messagebox as tkmsg
import subprocess
import sys
import threading
import os
from .constants import logs_file, BMA_DOWNLOAD_LINK

"""
Normally we should have permission from BMA to make changes to
the activities in its database because we could make mistakes 
that would make BMA look bad, basically

Which means that as a convention of BMA suite of apps
we must have a CLI api in order to interact with the apps' files

if thought book wants to communicate with BMA or BMT

he has to run a subprocess or cmd calling

meaning that when deploying any BM app, we must add
them to system environment varibles so that
"""
import logging
# setup logging once (top-level of your file, before class)
logging.basicConfig(
    filename=logs_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",

)

# Every BM app is going to put its folder in
# the environment variables of the user's computer
# if BMA is not installed and its env variable is not set
# then the activities api will not work
# Because BMA is not installed.
_ = os.getenv("BMA", None)


class ActivitiesAPI:
    """First check if BMA is installed or not
    simple check could be.

    When a person exits, it does the check first

    """

    def _check_installed(self) -> bool:
        """Check if BMA is installed in the user's system
        for now, just check the environment variable. Every app
        from BM would be putting it's name in the env vars"""

        if _ is None:
            logging.error(
                "BMA environment variable not set. BMA must be installed. "
                "Trigger BMA install suggestion to user through tkmsg. Exiting..."
            )
            return False
        else:
            return True

    def __init__(self) -> None:
        self.poa_list = []

    def make_activities(self, poa_list):
        """We are running in another thread because it freezes 
        before exiting which is undesirable.

        """
        self.status = ""
        if not self._check_installed():
            import tkinter.messagebox as tkmsg   
            if tkmsg.askyesno(
                "Install BMA",
                "Bobsi Mo Activities app is required to complete"
                " the experience for you,"
                    " would like to install it?"):
                try:
                    import webbrowser as wb
                    wb.open_new_tab(BMA_DOWNLOAD_LINK)

                    # lazy way of checking if we have it installed
                    # before concluding it is.
                    self.status = "installed"

                except Exception:
                    tkmsg.showerror(
                        "Downloading process failed",
                        "The download process failed."
                    )
                    self.status = "failed"
        
        threading.Thread(target=self._make, args=(
            poa_list, self.status,), daemon=False, name="BMA caller").start()

    def _make(self, poa_list, installed_status=""):
        """
        Before executing, check if BMA is actually installed.
        """
        self.poa_list = poa_list

        if installed_status == "installed":
            for actv in self.poa_list:
                    try:
                        cmd = f'{_}\\BMA.exe add "{actv}"'
                        # communicate with BMA cli
                        info = subprocess.run(cmd, capture_output=True)
                        logging.info(
                            "I talked to BMA. He says: "
                            f"{info.stdout.decode(encoding='utf-8').strip()}".strip()
                        )
                    except Exception as e:
                        logging.error(f"{e}: {cmd}")


if __name__ == "__main__":
    # ActivitiesAPI().make_activities(
    #     ['[ ] do something', "[ ] do another thing"])
    pass
